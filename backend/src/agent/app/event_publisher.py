"""Emit trainer:* events to connected Socket.IO client."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable, Coroutine

from agent.app.run_context import RunContext
from agent.domain.models import RunPhase, RunStatus


EmitFn = Callable[[str, str, dict[str, Any]], Coroutine[Any, Any, None]]


class RunEventPublisher:
    def __init__(self, emit_fn: EmitFn) -> None:
        self._emit = emit_fn

    async def publish_state(self, ctx: RunContext) -> None:
        if not ctx.sid:
            return
        run = ctx.run
        payload = {
            "run_id": run.id,
            "status": run.status.value if isinstance(run.status, RunStatus) else run.status,
            "phase": run.phase.value if isinstance(run.phase, RunPhase) else run.phase,
            "current_set": {
                "set_number": run.current_set_number,
                "target_reps": run.config.target_reps_per_set,
                "completed_reps": run.merged_observation_state.completed_reps,
            },
            "merged_state": {
                "rep_phase": run.merged_observation_state.rep_phase,
                "in_rep": run.merged_observation_state.in_rep,
                "active_issues": run.merged_observation_state.active_issues,
                "completed_reps": run.merged_observation_state.completed_reps,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await self._emit(ctx.sid, "trainer:state", payload)

    async def publish_voice_cue(
        self,
        ctx: RunContext,
        *,
        cue_id: str,
        message: str,
        focus_issue: str,
        severity: str,
        trigger: str,
        repeat_count: int | None = None,
    ) -> None:
        if not ctx.sid:
            return
        await self._emit(
            ctx.sid,
            "trainer:voice_cue",
            {
                "cue_id": cue_id,
                "run_id": ctx.run.id,
                "message": message,
                "focus_issue": focus_issue,
                "severity": severity,
                "set_number": ctx.run.current_set_number,
                "trigger": trigger,
                "repeat_count": repeat_count,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    async def publish_phase_message(
        self,
        ctx: RunContext,
        *,
        phase: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not ctx.sid:
            return
        await self._emit(
            ctx.sid,
            "trainer:phase_message",
            {
                "run_id": ctx.run.id,
                "phase": phase,
                "message": message,
                "metadata": metadata or {},
            },
        )

    async def publish_emergency(
        self,
        ctx: RunContext,
        *,
        source: str,
        severity: str,
        description: str,
    ) -> None:
        if not ctx.sid:
            return
        await self._emit(
            ctx.sid,
            "trainer:emergency",
            {
                "run_id": ctx.run.id,
                "source": source,
                "severity": severity,
                "description": description,
                "action_required": "pause",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    async def publish_error(
        self, sid: str, *, code: str, message: str, run_id: str | None = None
    ) -> None:
        payload: dict[str, Any] = {"code": code, "message": message}
        if run_id:
            payload["run_id"] = run_id
        await self._emit(sid, "trainer:error", payload)

    async def publish_registered(self, ctx: RunContext) -> None:
        if not ctx.sid:
            return
        run = ctx.run
        await self._emit(
            ctx.sid,
            "trainer:registered",
            {
                "run_id": run.id,
                "session_exercise_id": run.session_exercise_id,
                "status": run.status.value if isinstance(run.status, RunStatus) else run.status,
                "config": run.config.model_dump(),
            },
        )

    async def publish_pong(self, ctx: RunContext) -> None:
        if not ctx.sid:
            return
        await self._emit(
            ctx.sid,
            "trainer:pong",
            {
                "status": ctx.run.status.value
                if isinstance(ctx.run.status, RunStatus)
                else ctx.run.status,
            },
        )
