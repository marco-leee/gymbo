#!/usr/bin/env python3
"""Pump a video file into the /trainer Socket.IO namespace for local dev testing.

Replaces the live webcam frame loop when validating the trainer worker without the UI.

Example (self-contained — MongoDB + worker must be running)::

    # Terminal 1
    cd backend && TRAINER_DRY_RUN=1 uv run python src/trainer_fastapi_main.py

    # Terminal 2
    cd backend && uv run python src/scripts/test_trainer_video_socketio.py \\
      --video src/test.mp4 --bootstrap

Example (run already created via REST or live UI)::

    cd backend && uv run python src/scripts/test_trainer_video_socketio.py \\
      --run-id <uuid> \\
      --gymbo-session-id <session-uuid> \\
      --session-exercise-id <exercise-object-id> \\
      --client-id <client-uuid> \\
      --start

Environment:

- ``TRAINER_WS_URL`` — base URL fallback for ``--url`` (default ``http://127.0.0.1:10001``).
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import cv2
import socketio
from dotenv import load_dotenv
from socketio import exceptions as sio_exceptions

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NS = "/trainer"
_SRC = Path(__file__).resolve().parent.parent
_BACKEND = _SRC.parent

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

ACTIVE_STATUSES = frozenset({"active"})
PAUSE_SEND_STATUSES = frozenset({"resting", "paused", "feedback", "ended", "created"})


def _resolve_video(video: Path) -> Path:
    if video.is_file():
        return video
    for base in (_SRC, _BACKEND):
        alt = base / video
        if alt.is_file():
            return alt
    raise SystemExit(f"Video not found: {video}")


def _load_env() -> None:
    load_dotenv(_SRC / ".env")


def _post_json(url: str, *, timeout: float = 30.0) -> dict[str, Any]:
    req = Request(url, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"POST {url} failed ({exc.code}): {body}") from exc
    except URLError as exc:
        raise SystemExit(f"POST {url} failed: {exc}") from exc


def _bootstrap_run(
    *,
    gymbo_session_id: str,
    session_exercise_id: str,
    client_id: str,
    exercise_type: str,
    planned_sets: int,
    target_reps: int,
) -> str:
    from agent.domain.models import CoachedExerciseRun, ExerciseRunConfig
    from agent.infra.run_repository import RunRepository

    run = CoachedExerciseRun(
        gymbo_session_id=gymbo_session_id,
        session_exercise_id=session_exercise_id,
        trainer_id="video-script",
        client_id=client_id,
        exercise_type=exercise_type,
        config=ExerciseRunConfig(
            planned_sets=planned_sets,
            target_reps_per_set=target_reps,
            rest_duration_sec=10,
        ),
    )
    RunRepository().create_run(run)
    logger.info("Created run in MongoDB: %s", run.id)
    return run.id


def main() -> None:
    _load_env()

    p = argparse.ArgumentParser(
        description="Send video frames to the /trainer Socket.IO namespace.",
    )
    p.add_argument(
        "--url",
        default=os.environ.get("TRAINER_WS_URL", "http://127.0.0.1:10001"),
        help="Trainer worker origin (Socket.IO). Env: TRAINER_WS_URL",
    )
    p.add_argument(
        "--video",
        type=Path,
        default=Path("src/test.mp4"),
        help="Input video (default: backend/src/test.mp4)",
    )
    p.add_argument("--run-id", default=None, help="Existing CoachedExerciseRun id")
    p.add_argument(
        "--bootstrap",
        action="store_true",
        help="Create a dev run in MongoDB (requires MONGODB_URI / MONGO_URI)",
    )
    p.add_argument("--start", action="store_true", help="POST /internal/runs/{run_id}/start before WS connect")
    p.add_argument(
        "--gymbo-session-id",
        default="video-test-session",
        help="Register payload + bootstrap session id",
    )
    p.add_argument(
        "--session-exercise-id",
        default="video-test-exercise",
        help="Register payload + bootstrap exercise id",
    )
    p.add_argument(
        "--client-id",
        default=None,
        help="Register client_id (default: random uuid)",
    )
    p.add_argument("--exercise-type", default="overhead_squat")
    p.add_argument("--camera-view", default="LEFT")
    p.add_argument("--planned-sets", type=int, default=1)
    p.add_argument("--target-reps", type=int, default=5)
    p.add_argument("--fps", type=float, default=1.0, help="Wall-clock send rate while status is active")
    p.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (0 = until video EOF or run ends)")
    p.add_argument("--jpeg-quality", type=int, default=85)
    p.add_argument(
        "--active-timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for status=active after register",
    )
    p.add_argument("--connect-timeout", type=float, default=30.0)
    p.add_argument("--register-timeout", type=float, default=15.0)
    p.add_argument(
        "--send-during-prepare",
        action="store_true",
        help="Send frames before active (server v1 accepts preparing/setup; contract v1.1 does not)",
    )
    p.add_argument(
        "--end-run",
        action="store_true",
        help="Emit trainer:control end after finishing frames",
    )
    p.add_argument(
        "--engineio-debug",
        action="store_true",
        help="Enable python-socketio client debug logging",
    )
    args = p.parse_args()

    if not args.run_id and not args.bootstrap:
        raise SystemExit("Provide --run-id or use --bootstrap to create a dev run")
    if args.bootstrap and args.run_id:
        raise SystemExit("Use either --bootstrap or --run-id, not both")

    client_id = args.client_id or str(uuid.uuid4())
    base_url = args.url.rstrip("/")
    video_path = _resolve_video(args.video)

    run_id = args.run_id
    if args.bootstrap:
        run_id = _bootstrap_run(
            gymbo_session_id=args.gymbo_session_id,
            session_exercise_id=args.session_exercise_id,
            client_id=client_id,
            exercise_type=args.exercise_type,
            planned_sets=args.planned_sets,
            target_reps=args.target_reps,
        )
        args.start = True

    assert run_id is not None

    if args.start:
        start_body = _post_json(f"{base_url}/internal/runs/{run_id}/start")
        logger.info("Started graph: %s", start_body)

    register_done = threading.Event()
    register_ok: list[bool] = []
    errors: list[dict[str, Any]] = []
    status_lock = threading.Lock()
    run_status = "created"
    active_ready = threading.Event()
    run_finished = threading.Event()

    sio_client = socketio.Client(
        logger=args.engineio_debug,
        engineio_logger=args.engineio_debug,
        reconnection=False,
    )

    @sio_client.on("connect", namespace=NS)
    def _on_connect() -> None:
        logger.info("connected namespace=%s", NS)

    @sio_client.on("disconnect", namespace=NS)
    def _on_disconnect() -> None:
        logger.info("disconnected namespace=%s", NS)

    @sio_client.on("trainer:registered", namespace=NS)
    def _on_registered(data: object) -> None:
        logger.info("trainer:registered %s", data)
        with status_lock:
            register_ok.append(True)
        register_done.set()

    @sio_client.on("trainer:state", namespace=NS)
    def _on_state(data: object) -> None:
        nonlocal run_status
        if not isinstance(data, dict):
            return
        status = str(data.get("status", ""))
        phase = data.get("phase")
        reps = (data.get("current_set") or {}).get("completed_reps")
        with status_lock:
            prev = run_status
            run_status = status
            if status in ACTIVE_STATUSES:
                active_ready.set()
            elif status in PAUSE_SEND_STATUSES:
                active_ready.clear()
            if status == "ended":
                run_finished.set()
        if status != prev or reps is not None:
            logger.info("trainer:state status=%s phase=%s reps=%s", status, phase, reps)

    @sio_client.on("trainer:phase_message", namespace=NS)
    def _on_phase(data: object) -> None:
        if isinstance(data, dict):
            logger.info("trainer:phase_message phase=%s msg=%s", data.get("phase"), data.get("message"))

    @sio_client.on("trainer:voice_cue", namespace=NS)
    def _on_voice(data: object) -> None:
        if isinstance(data, dict):
            logger.info("trainer:voice_cue text=%s", (data.get("text") or "")[:120])

    @sio_client.on("trainer:error", namespace=NS)
    def _on_error(data: object) -> None:
        payload = data if isinstance(data, dict) else {"message": str(data)}
        logger.warning("trainer:error %s", payload)
        with status_lock:
            errors.append(payload)
        register_done.set()

    logger.info("Connecting to %s …", base_url)
    try:
        sio_client.connect(
            base_url,
            namespaces=[NS],
            wait_timeout=args.connect_timeout,
        )
    except Exception as exc:
        raise SystemExit(f"connect failed: {exc}") from exc

    register_payload = {
        "run_id": run_id,
        "gymbo_session_id": args.gymbo_session_id,
        "session_exercise_id": args.session_exercise_id,
        "client_id": client_id,
        "exercise_type": args.exercise_type,
        "camera_view": args.camera_view,
        "config": {"frame_sample_rate_fps": args.fps},
    }
    logger.info("Registering run %s …", run_id)
    try:
        sio_client.emit("trainer:register", register_payload, namespace=NS)
    except sio_exceptions.BadNamespaceError:
        sio_client.disconnect()
        raise SystemExit("connection lost before trainer:register") from None

    if not register_done.wait(timeout=args.register_timeout):
        sio_client.disconnect()
        raise SystemExit("timed out waiting for trainer:registered")
    if not register_ok:
        sio_client.disconnect()
        raise SystemExit(f"registration failed: {errors[-1] if errors else 'unknown'}")

    if not args.send_during_prepare:
        logger.info("Waiting for status=active (timeout %.0fs) …", args.active_timeout)
        if not active_ready.wait(timeout=args.active_timeout):
            sio_client.disconnect()
            with status_lock:
                st = run_status
            raise SystemExit(f"timed out waiting for active (last status={st})")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        sio_client.disconnect()
        raise SystemExit(f"could not open video: {video_path}")

    jpeg_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(args.jpeg_quality)]
    send_interval = 1.0 / max(args.fps, 0.1)
    seq = 0
    sent = 0

    def may_send() -> bool:
        if args.send_during_prepare:
            with status_lock:
                return run_status not in ("ended",)
        with status_lock:
            return run_status in ACTIVE_STATUSES

    try:
        while True:
            if run_finished.is_set():
                logger.info("run ended; stopping frame pump")
                break
            if args.max_frames and sent >= args.max_frames:
                logger.info("reached --max-frames=%s", args.max_frames)
                break

            if not may_send():
                time.sleep(0.05)
                continue

            ok, frame_bgr = cap.read()
            if not ok:
                logger.info("end of video after %s frame(s) sent", sent)
                break

            h, w = frame_bgr.shape[:2]
            timestamp_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            ec, buf = cv2.imencode(".jpg", frame_bgr, jpeg_params)
            if not ec:
                logger.warning("imencode failed at seq=%s", seq)
                seq += 1
                continue

            payload = {
                "meta": {
                    "run_id": run_id,
                    "seq": seq,
                    "timestamp_sec": float(timestamp_sec),
                    "dimensions": {"width": int(w), "height": int(h), "format": "jpeg"},
                },
                "frame": base64.b64encode(buf.tobytes()).decode("ascii"),
            }
            try:
                sio_client.emit("trainer:frame", payload, namespace=NS)
            except sio_exceptions.BadNamespaceError:
                logger.error("connection lost at seq=%s", seq)
                break

            sent += 1
            seq += 1
            if sent % 10 == 0 or sent == 1:
                logger.info("sent frame seq=%s (total=%s)", seq - 1, sent)
            time.sleep(send_interval)

        logger.info("Done: sent %s frame(s)", sent)
    finally:
        cap.release()

    if args.end_run and NS in sio_client.namespaces:
        try:
            sio_client.emit("trainer:control", {"run_id": run_id, "action": "end"}, namespace=NS)
            time.sleep(1.0)
        except sio_exceptions.BadNamespaceError:
            logger.warning("skip end control: namespace already disconnected")

    time.sleep(0.5)
    sio_client.disconnect()

    if sent == 0:
        raise SystemExit("no frames sent; check video path, run status, and worker logs")


if __name__ == "__main__":
    main()
