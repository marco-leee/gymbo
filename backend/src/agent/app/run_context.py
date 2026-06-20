"""Per-run composition root."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from agent.domain.models import (
    CoachedExerciseRun,
    VoiceOutEvent,
    VoiceRepeatState,
)
from agent.pipeline.frame_buffer import FrameBuffer
from agent.pipeline.frame_history import FrameHistory


VoiceConsumer = Callable[[VoiceOutEvent], Coroutine[Any, Any, None]]


@dataclass
class RunContext:
    run: CoachedExerciseRun
    frame_buffer: FrameBuffer = field(default_factory=FrameBuffer)
    frame_history: FrameHistory = field(default_factory=FrameHistory)
    voice_queue: asyncio.Queue[VoiceOutEvent | None] = field(
        default_factory=lambda: asyncio.Queue(maxsize=20)
    )
    voice_repeat_state: VoiceRepeatState = field(default_factory=VoiceRepeatState)
    sid: str | None = None
    dry_run: bool = False
    paused: bool = False
    end_requested: bool = False
    end_set_requested: bool = False
    end_rest_requested: bool = False
    set_loop_task: asyncio.Task | None = None
    session_task: asyncio.Task | None = None
    voice_consumer_task: asyncio.Task | None = None
    recent_coaching: list[dict] = field(default_factory=list)
    rest_activities: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.voice_repeat_state.threshold = self.run.config.voice_repeat_threshold

    async def enqueue_voice(self, event: VoiceOutEvent) -> None:
        try:
            self.voice_queue.put_nowait(event)
        except asyncio.QueueFull:
            self._coalesce_voice(event)

    def _coalesce_voice(self, event: VoiceOutEvent) -> None:
        """Drop oldest same-issue event or oldest overall when queue is full."""
        pending: list[VoiceOutEvent] = []
        while not self.voice_queue.empty():
            try:
                item = self.voice_queue.get_nowait()
                if item is not None:
                    pending.append(item)
            except asyncio.QueueEmpty:
                break
        focus = event.focus_issue.strip().lower()
        pending = [e for e in pending if e.focus_issue.strip().lower() != focus]
        pending.append(event)
        while len(pending) > 20:
            pending.pop(0)
        for e in pending:
            try:
                self.voice_queue.put_nowait(e)
            except asyncio.QueueFull:
                break

    async def start_voice_consumer(self, handler: VoiceConsumer) -> None:
        if self.voice_consumer_task and not self.voice_consumer_task.done():
            return

        async def _consume() -> None:
            while True:
                event = await self.voice_queue.get()
                if event is None:
                    break
                await handler(event)

        self.voice_consumer_task = asyncio.create_task(_consume())

    async def stop_voice_consumer(self) -> None:
        if self.voice_consumer_task is None:
            return
        try:
            self.voice_queue.put_nowait(None)
        except asyncio.QueueFull:
            pass
        if not self.voice_consumer_task.done():
            self.voice_consumer_task.cancel()
            try:
                await self.voice_consumer_task
            except asyncio.CancelledError:
                pass
        self.voice_consumer_task = None

    async def teardown(self) -> None:
        await self.stop_voice_consumer()
        for task in (self.set_loop_task, self.session_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self.set_loop_task = None
        self.session_task = None
        self.frame_buffer.clear()
        self.frame_history.clear()
