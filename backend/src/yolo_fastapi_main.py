"""ASGI entry: FastAPI (RunPod LB ``/ping``) + Socket.IO ``/yolo`` on one uvicorn process."""

from __future__ import annotations

import logging
import os

import socketio
import uvicorn
from fastapi import FastAPI

from yolo_inference_runtime import YoloInferenceRuntime
from yolo_socket_namespace import YoloInferenceNamespace
from yolo_stream_registry import StreamRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NS = "/yolo"

_apps_cache: tuple[socketio.ASGIApp, StreamRegistry] | None = None


def _listen_port() -> int:
    if raw := os.environ.get("PORT", "").strip():
        return int(raw)
    return int(os.environ.get("YOLO_WS_PORT", "10001"))


def build_apps() -> tuple[socketio.ASGIApp, StreamRegistry]:
    global _apps_cache
    if _apps_cache is not None:
        return _apps_cache

    max_streams = int(os.environ.get("YOLO_MAX_STREAMS", "32"))
    max_concurrent = int(os.environ.get("YOLO_MAX_CONCURRENT_INFER", "2"))
    max_pending_frames = int(os.environ.get("YOLO_MAX_PENDING_FRAMES", "4"))
    max_buffer = int(os.environ.get("YOLO_WS_MAX_BUFFER", str(100 * 1024 * 1024)))
    cors = os.environ.get("YOLO_WS_CORS", "*")

    engine_kw: dict = {}
    ping_interval_sec = os.environ.get("YOLO_WS_PING_INTERVAL_SEC", "").strip()
    if ping_interval_sec:
        engine_kw["ping_interval"] = float(ping_interval_sec)
    ping_timeout_sec = os.environ.get("YOLO_WS_PING_TIMEOUT_SEC", "").strip()
    if ping_timeout_sec:
        engine_kw["ping_timeout"] = float(ping_timeout_sec)

    runtime = YoloInferenceRuntime.from_env()
    registry = StreamRegistry(max_streams)

    fastapi_app = FastAPI(title="YOLO ingest", version="0.1")

    @fastapi_app.get("/ping")
    async def ping() -> dict[str, str]:
        """RunPod worker health (`ai/runpod.py` pattern)."""

        return {"status": "healthy"}

    @fastapi_app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @fastapi_app.get("/stats")
    async def stats() -> dict[str, int]:
        return {"registered_streams": registry.stream_count()}

    sio = socketio.AsyncServer(
        logger=True,
        cors_allowed_origins=cors,
        async_mode="asgi",
        max_http_buffer_size=max_buffer,
        **engine_kw,
    )
    sio.register_namespace(
        YoloInferenceNamespace(
            NS,
            runtime=runtime,
            registry=registry,
            max_concurrent_infer=max_concurrent,
            max_pending_frames=max_pending_frames,
        ),
    )

    combined = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
    logger.info(
        "YOLO ASGI: FastAPI routes + Socket.IO namespace=%s max_streams=%s "
        "concurrent=%s pending_frame_queue_depth=%s engine_io_extra=%s",
        NS,
        max_streams,
        max_concurrent,
        max_pending_frames,
        sorted(engine_kw.keys()) if engine_kw else "()",
    )
    logger.info(
        "YOLO_CONF (perception thresholds) defaults from env affect gate failures logged as "
        "no perception output; use --paced on the smoke client to debug transport vs model."
    )
    _apps_cache = (combined, registry)
    return _apps_cache


def get_asgi_app() -> socketio.ASGIApp:
    return build_apps()[0]


def main() -> None:
    port = _listen_port()
    combined, _ = build_apps()

    logger.info(
        "Listening 0.0.0.0:%s (/ping FastAPI + %s Socket.IO via /socket.io/)",
        port,
        NS,
    )
    uvicorn.run(combined, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
