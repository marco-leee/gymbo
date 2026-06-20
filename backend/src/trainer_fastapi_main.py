"""ASGI entry: FastAPI + Socket.IO /trainer namespace."""

from __future__ import annotations

import logging
import os

import socketio
import uvicorn
from fastapi import FastAPI

from agent.app.run_controller import RunController
from agent.app.run_registry import RunRegistry
from agent.infra.run_repository import RunRepository
from trainer_api import router as internal_router
from trainer_socket_namespace import TrainerNamespace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NS = "/trainer"
_apps_cache: tuple[socketio.ASGIApp, RunRegistry, RunController] | None = None


def _listen_port() -> int:
    if raw := os.environ.get("PORT", "").strip():
        return int(raw)
    return int(os.environ.get("TRAINER_WS_PORT", "10001"))


def _dry_run() -> bool:
    return os.environ.get("TRAINER_DRY_RUN", "").lower() in ("1", "true", "yes")


def build_apps() -> tuple[socketio.ASGIApp, RunRegistry, RunController]:
    global _apps_cache
    if _apps_cache is not None:
        return _apps_cache

    max_buffer = int(os.environ.get("TRAINER_WS_MAX_BUFFER", str(100 * 1024 * 1024)))
    cors = os.environ.get("TRAINER_WS_CORS", "*")
    dry_run = _dry_run()

    registry = RunRegistry()
    repository = RunRepository()

    sio = socketio.AsyncServer(
        logger=True,
        cors_allowed_origins=cors,
        async_mode="asgi",
        max_http_buffer_size=max_buffer,
    )

    async def emit_to_sid(sid: str, event: str, data: dict) -> None:
        await sio.emit(event, data, room=sid, namespace=NS)

    from agent.app.event_publisher import RunEventPublisher

    publisher = RunEventPublisher(emit_to_sid)
    controller = RunController(registry, repository, publisher, dry_run=dry_run)

    fastapi_app = FastAPI(title="Trainer Agent", version="0.1")
    fastapi_app.include_router(internal_router)

    @fastapi_app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @fastapi_app.get("/stats")
    async def stats() -> dict[str, int]:
        return {"active_runs": registry.count()}

    namespace = TrainerNamespace(NS, registry=registry, controller=controller)
    namespace.publisher = publisher
    sio.register_namespace(namespace)

    combined = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
    logger.info(
        "Trainer ASGI: FastAPI + Socket.IO namespace=%s dry_run=%s port_env=TRAINER_WS_PORT",
        NS,
        dry_run,
    )
    _apps_cache = (combined, registry, controller)
    return _apps_cache


def get_run_controller() -> RunController:
    return build_apps()[2]


def get_asgi_app() -> socketio.ASGIApp:
    return build_apps()[0]


def main() -> None:
    port = _listen_port()
    combined, _, _ = build_apps()
    logger.info("Listening 0.0.0.0:%s (/trainer Socket.IO + internal API)", port)
    uvicorn.run(combined, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
