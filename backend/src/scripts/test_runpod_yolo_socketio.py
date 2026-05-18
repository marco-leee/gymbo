#!/usr/bin/env python3
"""Smoke-test the FastAPI+Socket.IO ``/yolo`` namespace (see ``yolo_fastapi_main.py``) with video.

Example::

    cd backend && uv run python src/scripts/test_runpod_yolo_socketio.py \\
      --url https://YOUR_HOST \\
      --video path/to/sample.mp4 \\
      --max-frames 20

Environment:

- ``YOLO_SOCKETIO_URL`` — base URL fallback for ``--url``.
- ``RUNPOD_API_KEY`` / ``YOLO_WS_AUTH_BEARER`` — optional ``Authorization: Bearer`` handshake header.
- Server perception strictness follows ``YOLO_CONF`` on the worker; steady ``no perception output`` logs are usually thresholds or scene/layout, not the socket.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import cv2
import socketio
from socketio import exceptions as sio_exceptions

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NS = "/yolo"


def _resolve_video(video: Path) -> Path:
    if video.is_file():
        return video
    backend = Path(__file__).resolve().parent.parent.parent
    alt = backend / video
    if alt.is_file():
        return alt
    raise SystemExit(f"Video not found: {video}")


def _looks_local_host(host: str | None) -> bool:
    if not host:
        return True
    h = host.lower()
    return h in ("localhost", "127.0.0.1", "::1", "[::1]")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Test YOLO Socket.IO endpoint (FastAPI ASGI) with a video file.",
    )
    p.add_argument(
        "--url",
        default=os.environ.get("YOLO_SOCKETIO_URL", "http://127.0.0.1:10001"),
        help="Socket.IO origin (scheme + host, optional port). Env: YOLO_SOCKETIO_URL",
    )
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--stream-id", default=None)
    p.add_argument("--camera-view", default="RIGHT")
    p.add_argument("--exercise-type", default="SQUAT")
    p.add_argument("--max-frames", type=int, default=30)
    p.add_argument("--jpeg-quality", type=int, default=85)
    p.add_argument("--frame-delay", type=float, default=0.0)
    p.add_argument(
        "--paced",
        action="store_true",
        help="Wait for each yolo_frame_result before sending the next frame (best for WAN / RunPod debugging).",
    )
    p.add_argument(
        "--paced-frame-timeout",
        type=float,
        default=60.0,
        help="Seconds to wait per frame when --paced is set.",
    )
    p.add_argument(
        "--engineio-debug",
        action="store_true",
        help="Enable python-socketio + Engine.IO client logging (disconnect reasons).",
    )
    p.add_argument("--connect-timeout", type=float, default=30.0)
    p.add_argument("--register-timeout", type=float, default=15.0)
    p.add_argument("--result-timeout", type=float, default=120.0)
    p.add_argument(
        "--auth-bearer",
        default=os.environ.get("RUNPOD_API_KEY")
        or os.environ.get("YOLO_WS_AUTH_BEARER"),
        metavar="TOKEN",
        help="Optional Bearer for Engine.IO handshake. Env: RUNPOD_API_KEY",
    )
    args = p.parse_args()
    raw_u = args.url.strip().rstrip("/")

    video_path = _resolve_video(args.video)
    stream_id = args.stream_id or str(uuid.uuid4())
    jpeg_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(args.jpeg_quality)]

    origin = urlparse(
        raw_u if "://" in raw_u else "//" + raw_u
    )
    remoteish = origin.scheme == "https" or not _looks_local_host(origin.hostname)
    if remoteish and args.frame_delay == 0.0 and not args.paced:
        logger.warning(
            "Sending JPEG frames without --frame-delay and without --paced can overwhelm WAN "
            "inference pipelines; queue_overflow or disconnects often follow."
        )

    register_done = threading.Event()
    register_ok: list[bool] = []
    errors: list[dict] = []
    frame_results: list[dict] = []
    lock = threading.Lock()
    result_cv = threading.Condition(lock)
    received_seqs: set[int] = set()

    sio_client = socketio.Client(
        logger=args.engineio_debug,
        engineio_logger=args.engineio_debug,
        reconnection=True,
    )

    @sio_client.on("connect", namespace=NS)
    def _on_connect() -> None:
        logger.info("connected namespace=%s", NS)

    @sio_client.on("disconnect", namespace=NS)
    def _on_disconnect() -> None:
        logger.info("disconnected namespace=%s", NS)
        with result_cv:
            result_cv.notify_all()

    @sio_client.on("yolo_register_stream_ack", namespace=NS)
    def _on_ack(data: object) -> None:
        logger.info("yolo_register_stream_ack %s", data)
        with lock:
            register_ok.append(True)
        register_done.set()

    @sio_client.on("error", namespace=NS)
    def _on_error(data: object) -> None:
        payload = data if isinstance(data, dict) else {"message": str(data)}
        logger.warning("server error event: %s", payload)
        with lock:
            errors.append(payload)
        register_done.set()

    @sio_client.on("yolo_frame_result", namespace=NS)
    def _on_result(data: object) -> None:
        if isinstance(data, dict):
            sq = data.get("seq")
            logger.info(
                "yolo_frame_result stream_id=%s seq=%s error=%s",
                data.get("stream_id"),
                sq,
                data.get("error"),
            )
            with result_cv:
                frame_results.append(dict(data))
                if isinstance(sq, int):
                    received_seqs.add(sq)
                result_cv.notify_all()

    headers: dict[str, str] = {}
    if args.auth_bearer:
        headers["Authorization"] = f"Bearer {args.auth_bearer}"

    logger.info(
        "Connecting to %s %s ...",
        args.url.rstrip("/"),
        "(with Bearer auth)" if headers else "",
    )
    try:
        sio_client.connect(
            args.url.rstrip("/"),
            namespaces=[NS],
            wait_timeout=args.connect_timeout,
            headers=headers,
            retry=True,
        )
    except Exception as e:
        raise SystemExit(f"connect failed: {e}") from e

    payload_reg = {
        "stream_id": stream_id,
        "camera_view": args.camera_view,
        "exercise_type": args.exercise_type,
    }
    logger.info("Registering stream %s …", stream_id)
    try:
        sio_client.emit("yolo_register_stream", payload_reg, namespace=NS)
    except sio_exceptions.BadNamespaceError:
        sio_client.disconnect()
        raise SystemExit(
            "connection_lost_mid_stream: lost /yolo namespace before register emit"
        ) from None

    if not register_done.wait(timeout=args.register_timeout):
        sio_client.disconnect()
        raise SystemExit("timed out waiting for register ack or error")
    if not register_ok:
        sio_client.disconnect()
        raise SystemExit(f"registration failed: {errors[-1] if errors else 'unknown'}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        sio_client.disconnect()
        raise SystemExit(f"could not open video: {video_path}")

    def wait_for_seq(target_seq: int) -> bool:
        deadline = time.monotonic() + args.paced_frame_timeout
        with result_cv:
            while target_seq not in received_seqs:
                if NS not in sio_client.namespaces:
                    logger.error(
                        "connection_lost_mid_stream during paced wait seq=%s",
                        target_seq,
                    )
                    return False
                if time.monotonic() >= deadline:
                    logger.warning(
                        "paced-frame-timeout exceeded waiting for seq=%s", target_seq
                    )
                    return False
                remaining = deadline - time.monotonic()
                result_cv.wait(timeout=min(max(remaining, 0.01), 0.25))
            return True


    seq = 0
    sent = 0
    try:
        while sent < args.max_frames:
            ok, frame_bgr = cap.read()
            if not ok:
                logger.info("end of video after %s frames read", seq)
                break
            h, w = frame_bgr.shape[:2]

            ec, buf = cv2.imencode(".jpg", frame_bgr, jpeg_params)
            if not ec:
                logger.warning("imencode failed at seq=%s", seq)
                seq += 1
                continue
            jpeg_bytes = buf.tobytes()

            outgoing = {
                "frame": jpeg_bytes,
                "stream_id": stream_id,
                "seq": seq,
                "dimensions": {
                    "width": int(w),
                    "height": int(h),
                    "format": "jpeg",
                },
            }
            emit_seq = seq
            try:
                sio_client.emit("yolo_frame", outgoing, namespace=NS)
            except sio_exceptions.BadNamespaceError:
                logger.error(
                    "connection_lost_mid_stream: emit(yolo_frame) failed at seq=%s",
                    emit_seq,
                )
                break
            sent += 1
            seq += 1
            if args.paced and not wait_for_seq(emit_seq):
                logger.warning("stopped sending after pacing failure at seq=%s", emit_seq)
                break
            if args.frame_delay > 0:
                time.sleep(args.frame_delay)
        logger.info("Sent %s frame(s)", sent)
    finally:
        cap.release()

    deadline = time.monotonic() + args.result_timeout
    while (
        sent > 0
        and len(frame_results) < sent
        and time.monotonic() < deadline
    ):
        time.sleep(0.05)

    try:
        sio_client.emit("yolo_unregister_stream", {"stream_id": stream_id}, namespace=NS)
        time.sleep(0.3)
    except sio_exceptions.BadNamespaceError:
        logger.warning("skip unregister emit: namespace already disconnected")
    finally:
        sio_client.disconnect()

    if sent == 0:
        raise SystemExit("no frames sent; check video path and codec")
    if len(frame_results) == 0:
        raise SystemExit("no yolo_frame_result received in time")

    n_err = sum(1 for r in frame_results if r.get("error"))
    logger.info(
        "OK: sent=%s received_results=%s frames_with_inference_error_field=%s",
        sent,
        len(frame_results),
        n_err,
    )
    with open("frame_results.json", "w") as f:
        json.dump(frame_results, f, indent=2)
    sys.exit(0)


if __name__ == "__main__":
    main()
