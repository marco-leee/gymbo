"""Socket.IO ``/yolo`` namespace: multi-stream frames to YOLO inference."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

import socketio

from models.exercise import ExerciseType
from models.yolo_ws_protocol import (
    YoloFrameIncoming,
    YoloFrameResult,
    YoloRegisterStream,
    YoloUnregisterStream,
)
from utils.video import CameraView
from yolo_frame_processing import frame_bytes_to_bgr, parse_yolo_frame_event
from yolo_inference_runtime import YoloInferenceRuntime
from yolo_stream_registry import StreamRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _WorkItem:
    sid: str
    exercise_type: ExerciseType
    camera_view: CameraView
    incoming: YoloFrameIncoming


class YoloInferenceNamespace(socketio.AsyncNamespace):
    def __init__(
        self,
        namespace: str,
        *,
        runtime: YoloInferenceRuntime,
        registry: StreamRegistry,
        max_concurrent_infer: int,
        max_pending_frames: int,
    ) -> None:
        super().__init__(namespace)
        self.runtime = runtime
        self.registry = registry
        self._max_concurrent_infer = max_concurrent_infer
        self._max_pending_frames = max(1, max_pending_frames)
        self.infer_semaphore: asyncio.Semaphore | None = None
        self._queues: dict[str, asyncio.Queue[_WorkItem]] = {}
        self._consumer_tasks: dict[str, asyncio.Task[None]] = {}

    async def _ensure_infer_sem(self) -> asyncio.Semaphore:
        if self.infer_semaphore is None:
            self.infer_semaphore = asyncio.Semaphore(self._max_concurrent_infer)
        return self.infer_semaphore

    def _connected(self, sid: str) -> bool:
        try:
            return bool(self.server.manager.is_connected(sid, self.namespace))
        except Exception:
            return False

    async def _stop_consumer(self, stream_id: str) -> None:
        """Cancel consumer and drop bookkeeping for ``stream_id``."""
        task = self._consumer_tasks.pop(stream_id, None)
        self._queues.pop(stream_id, None)
        if task is None:
            return
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def _ensure_queue(self, stream_id: str) -> asyncio.Queue[_WorkItem]:
        existing = self._queues.get(stream_id)
        if existing is not None:
            return existing
        q: asyncio.Queue[_WorkItem] = asyncio.Queue(maxsize=self._max_pending_frames)
        self._queues[stream_id] = q

        async def runner() -> None:
            await self._consume_loop(stream_id, q)

        self._consumer_tasks[stream_id] = asyncio.create_task(
            runner(), name=f"yolo-consumer-{stream_id}"
        )
        return q

    async def _consume_loop(
        self,
        stream_id: str,
        q: asyncio.Queue[_WorkItem],
    ) -> None:
        sem = await self._ensure_infer_sem()
        try:
            while True:
                item = await q.get()
                incoming = item.incoming
                meta = incoming.meta
                seq = meta.seq

                try:
                    frame_bgr = frame_bytes_to_bgr(
                        incoming.frame,
                        meta.dimensions.width,
                        meta.dimensions.height,
                        meta.dimensions.format,
                    )
                except Exception as e:
                    payload = YoloFrameResult(
                        stream_id=stream_id,
                        seq=seq,
                        t_server=time.time(),
                        overall=None,
                        error=str(e),
                    )
                    if self._connected(item.sid):
                        await self.emit(
                            "yolo_frame_result",
                            payload.model_dump(mode="json"),
                            room=item.sid,
                        )
                    continue

                async with sem:
                    t_infer = time.time()
                    try:
                        overall = await asyncio.to_thread(
                            self.runtime.infer,
                            frame_bgr,
                            idx=seq,
                            timestamp=t_infer,
                            exercise_type=item.exercise_type,
                            camera_view=item.camera_view,
                        )
                    except Exception as e:
                        logger.exception(
                            "Inference failed for sid=%s stream=%s",
                            item.sid,
                            stream_id,
                        )
                        overall = None
                        err_msg = str(e)
                    else:
                        err_msg = None
                        if overall is None:
                            err_msg = (
                                "no perception output "
                                "(no person or pose/seg gate failed)"
                            )

                out = YoloFrameResult(
                    stream_id=stream_id,
                    seq=seq,
                    t_server=t_infer,
                    overall=overall,
                    error=err_msg,
                )
                if self._connected(item.sid):
                    await self.emit(
                        "yolo_frame_result",
                        out.model_dump(mode="json"),
                        room=item.sid,
                    )

        except asyncio.CancelledError:
            raise

    async def on_connect(self, sid: str, environ: dict) -> None:
        logger.info("Yolo client connected: %s", sid)

    async def on_disconnect(self, sid: str) -> None:
        removed = self.registry.disconnect_session(sid)
        for stream_id in removed:
            await self._stop_consumer(stream_id)
        logger.info(
            "Yolo client disconnected: %s (%d streams dropped)",
            sid,
            len(removed),
        )

    async def on_yolo_register_stream(self, sid: str, data: dict) -> None:
        try:
            msg = YoloRegisterStream.model_validate(data or {})
            cam = msg.camera_view or "RIGHT"
            ex = msg.exercise_type or "SQUAT"
            CameraView.from_string(cam)
            ExerciseType.from_string(ex)
        except Exception as e:
            await self.emit("error", {"message": str(e)}, room=sid)
            return

        ok, err = self.registry.register(
            sid,
            msg.stream_id,
            camera_view=cam,
            exercise_type=ex,
        )
        if not ok:
            await self.emit("error", {"message": err or "register failed"}, room=sid)
            return

        await self.emit(
            "yolo_register_stream_ack",
            {"stream_id": msg.stream_id, "ok": True},
            room=sid,
        )

    async def on_yolo_unregister_stream(self, sid: str, data: dict) -> None:
        try:
            msg = YoloUnregisterStream.model_validate(data or {})
        except Exception as e:
            await self.emit("error", {"message": str(e)}, room=sid)
            return
        if self.registry.unregister(sid, msg.stream_id):
            await self._stop_consumer(msg.stream_id)

    async def on_yolo_frame(self, sid: str, data: dict) -> None:
        t_recv = time.time()
        try:
            incoming = parse_yolo_frame_event(data or {})
        except Exception as e:
            await self.emit("error", {"message": str(e)}, room=sid)
            return

        meta = incoming.meta
        stream_id = meta.stream_id
        seq = meta.seq

        if not self.registry.is_owned_by(stream_id, sid):
            await self.emit(
                "error",
                {"message": "unknown or unregistered stream_id"},
                room=sid,
            )
            return

        rec = self.registry.record(stream_id)
        if rec is None:
            await self.emit(
                "error",
                {"message": "unknown or unregistered stream_id"},
                room=sid,
            )
            return

        try:
            ex_t = ExerciseType.from_string(rec.exercise_type)
            cam_v = CameraView.from_string(rec.camera_view)
        except Exception as e:
            await self.emit("error", {"message": str(e)}, room=sid)
            return

        q = self._ensure_queue(stream_id)
        work = _WorkItem(
            sid=sid,
            exercise_type=ex_t,
            camera_view=cam_v,
            incoming=incoming,
        )
        try:
            q.put_nowait(work)
        except asyncio.QueueFull:
            overflow = YoloFrameResult(
                stream_id=stream_id,
                seq=seq,
                t_server=t_recv,
                overall=None,
                error=(
                    "queue_overflow: inference backlog exceeds "
                    f"YOLO_MAX_PENDING_FRAMES ({self._max_pending_frames}); "
                    "slow down uploads or increase capacity"
                ),
            )
            if self._connected(sid):
                await self.emit(
                    "yolo_frame_result",
                    overflow.model_dump(mode="json"),
                    room=sid,
                )
