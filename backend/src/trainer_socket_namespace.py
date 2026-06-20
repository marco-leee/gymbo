"""Socket.IO /trainer namespace handlers."""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

import socketio

from agent.app.event_publisher import RunEventPublisher
from agent.app.run_controller import RunController
from agent.app.run_registry import RunRegistry
from agent.domain.models import IncomingFrame, RunStatus
from models.trainer_ws_protocol import (
    TrainerControlPayload,
    TrainerFramePayload,
    TrainerPingPayload,
    TrainerRegisterPayload,
    TrainerUnregisterPayload,
)

logger = logging.getLogger(__name__)
NS = "/trainer"


class TrainerNamespace(socketio.AsyncNamespace):
    def __init__(
        self,
        namespace: str,
        *,
        registry: RunRegistry,
        controller: RunController,
    ) -> None:
        super().__init__(namespace)
        self.registry = registry
        self.controller = controller
        self.publisher = RunEventPublisher(self._emit_to_sid)
        self._max_pending = int(os.environ.get("TRAINER_MAX_PENDING_FRAMES", "4"))

    async def _emit_to_sid(self, sid: str, event: str, data: dict[str, Any]) -> None:
        await self.emit(event, data, room=sid)

    async def trigger_event(self, event: str, *args) -> None:
        """Map contract events with colons to handlers."""
        handlers = {
            "trainer:register": self.on_trainer_register,
            "trainer:frame": self.on_trainer_frame,
            "trainer:control": self.on_trainer_control,
            "trainer:unregister": self.on_trainer_unregister,
            "trainer:ping": self.on_trainer_ping,
        }
        handler = handlers.get(event)
        if handler is not None:
            return await handler(*args)
        return await super().trigger_event(event, *args)

    async def on_connect(self, sid, _environ) -> None:
        logger.info("Trainer client connected: %s", sid)

    async def on_disconnect(self, sid) -> None:
        logger.info("Trainer client disconnected: %s", sid)
        ctx = self.registry.by_sid(sid)
        if ctx:
            await self.controller.end(ctx.run.id)

    async def on_trainer_register(self, sid, data: dict) -> None:
        try:
            payload = TrainerRegisterPayload.model_validate(data)
        except Exception as exc:
            await self.publisher.publish_error(sid, code="VALIDATION_ERROR", message=str(exc))
            return

        ctx = self.controller.load_or_attach(payload.run_id, sid=sid)
        if ctx is None:
            await self.publisher.publish_error(
                sid, code="RUN_NOT_FOUND", message="Run not found", run_id=payload.run_id
            )
            return

        if ctx.sid and ctx.sid != sid and ctx.run.status not in (RunStatus.ENDED, RunStatus.CREATED):
            await self.publisher.publish_error(
                sid, code="ALREADY_ACTIVE", message="Run already active", run_id=payload.run_id
            )
            return

        ctx.sid = sid
        await self.publisher.publish_registered(ctx)

    async def on_trainer_frame(self, sid, data: dict) -> None:
        try:
            payload = TrainerFramePayload.model_validate(data)
        except Exception as exc:
            await self.publisher.publish_error(sid, code="VALIDATION_ERROR", message=str(exc))
            return

        ctx = self.registry.get(payload.meta.run_id)
        if ctx is None:
            await self.publisher.publish_error(
                sid, code="RUN_NOT_ACTIVE", message="Unknown run", run_id=payload.meta.run_id
            )
            return

        if ctx.paused or ctx.run.status == RunStatus.PAUSED:
            return

        if ctx.run.status not in (RunStatus.ACTIVE, RunStatus.PREPARING, RunStatus.SETUP):
            await self.publisher.publish_error(
                sid,
                code="RUN_NOT_ACTIVE",
                message="Run not accepting frames",
                run_id=payload.meta.run_id,
            )
            return

        try:
            jpeg_bytes = base64.b64decode(payload.frame)
        except Exception:
            await self.publisher.publish_error(sid, code="VALIDATION_ERROR", message="Invalid frame encoding")
            return

        incoming = IncomingFrame(
            seq=payload.meta.seq,
            timestamp_sec=payload.meta.timestamp_sec,
            jpeg_bytes=jpeg_bytes,
            width=payload.meta.dimensions.width,
            height=payload.meta.dimensions.height,
        )
        ctx.frame_buffer.push(incoming)

    async def on_trainer_control(self, sid, data: dict) -> None:
        try:
            payload = TrainerControlPayload.model_validate(data)
        except Exception as exc:
            await self.publisher.publish_error(sid, code="VALIDATION_ERROR", message=str(exc))
            return

        ctx = self.registry.get(payload.run_id)
        if ctx is None:
            await self.publisher.publish_error(
                sid, code="RUN_NOT_FOUND", message="Run not found", run_id=payload.run_id
            )
            return

        if payload.action == "resume":
            await self.controller.resume(payload.run_id)
        elif payload.action == "end":
            await self.controller.end(payload.run_id)
        elif payload.action == "end_set":
            ctx.end_set_requested = True
        elif payload.action == "end_rest":
            ctx.end_rest_requested = True
        elif payload.action == "emergency_ack":
            pass

        await self.publisher.publish_state(ctx)

    async def on_trainer_unregister(self, sid, data: dict) -> None:
        try:
            payload = TrainerUnregisterPayload.model_validate(data)
        except Exception:
            return
        await self.controller.end(payload.run_id)

    async def on_trainer_ping(self, sid, data: dict) -> None:
        try:
            payload = TrainerPingPayload.model_validate(data)
        except Exception:
            return
        ctx = self.registry.get(payload.run_id)
        if ctx:
            await self.publisher.publish_pong(ctx)
