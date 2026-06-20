"""Run lifecycle controller."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from agent.app.event_publisher import RunEventPublisher
from agent.app.run_context import RunContext
from agent.app.run_registry import RunRegistry
from agent.domain.models import (
    CoachedExerciseRun,
    ExerciseRunConfig,
    RunStatus,
    SafetyEventRecord,
)
from agent.domain.safety_evaluator import evaluate_global_safety
from agent.graphs.factory import build_dependencies, build_session_runner
from agent.graphs.voice_out import VoiceOutHandler
from agent.infra.run_repository import RunRepository

logger = logging.getLogger(__name__)


class RunController:
    def __init__(
        self,
        registry: RunRegistry,
        repository: RunRepository,
        publisher: RunEventPublisher,
        *,
        dry_run: bool = False,
    ) -> None:
        self.registry = registry
        self.repository = repository
        self.publisher = publisher
        self.dry_run = dry_run
        self._deps = build_dependencies(dry_run=dry_run)

    def attach_run(self, run: CoachedExerciseRun, *, sid: str | None = None) -> RunContext:
        ctx = RunContext(run=run, sid=sid, dry_run=self.dry_run)
        self.registry.register(ctx)
        return ctx

    def load_or_attach(self, run_id: str, *, sid: str | None = None) -> RunContext | None:
        existing = self.registry.get(run_id)
        if existing:
            if sid:
                existing.sid = sid
            return existing
        run = self.repository.get_run(run_id)
        if not run:
            return None
        return self.attach_run(run, sid=sid)

    async def start(self, run_id: str) -> RunContext | None:
        ctx = self.load_or_attach(run_id)
        if ctx is None:
            return None
        if ctx.session_task and not ctx.session_task.done():
            return ctx

        voice_handler = VoiceOutHandler(ctx, self._deps, self.publisher, self.repository)
        await ctx.start_voice_consumer(voice_handler.handle_event)

        runner = build_session_runner(ctx, self._deps, self.publisher, self.repository)
        ctx.session_task = asyncio.create_task(runner.run())
        ctx.run.status = RunStatus.PREPARING
        self.repository.update_run(ctx.run)
        return ctx

    async def start_set_loop(self, run_id: str) -> None:
        """Start only the set loop (US1 minimal path)."""
        ctx = self.load_or_attach(run_id)
        if ctx is None:
            return
        from agent.graphs.set_loop import SetLoopRunner

        voice_handler = VoiceOutHandler(ctx, self._deps, self.publisher, self.repository)
        await ctx.start_voice_consumer(voice_handler.handle_event)

        async def _run():
            runner = SetLoopRunner(ctx, self._deps, self.publisher)
            await runner.run_set()

        ctx.set_loop_task = asyncio.create_task(_run())

    async def pause(self, run_id: str, *, source: str = "global_monitor", description: str = "") -> bool:
        ctx = self.registry.get(run_id)
        if ctx is None:
            return False
        ctx.paused = True
        ctx.run.status = RunStatus.PAUSED
        self.repository.save_safety_event(
            SafetyEventRecord(
                run_id=run_id,
                source=source,  # type: ignore[arg-type]
                description=description or "Emergency pause",
            )
        )
        self.repository.update_run(ctx.run)
        await self.publisher.publish_emergency(
            ctx,
            source=source,
            severity="critical",
            description=description or "Session paused",
        )
        return True

    async def resume(self, run_id: str) -> bool:
        ctx = self.registry.get(run_id)
        if ctx is None or ctx.run.status != RunStatus.PAUSED:
            return False
        ctx.paused = False
        ctx.run.status = RunStatus.ACTIVE
        self.repository.update_run(ctx.run)
        await self.publisher.publish_state(ctx)
        if ctx.session_task is None or ctx.session_task.done():
            runner = build_session_runner(ctx, self._deps, self.publisher, self.repository)
            ctx.session_task = asyncio.create_task(runner.run())
        return True

    async def end(self, run_id: str) -> bool:
        ctx = self.registry.get(run_id)
        if ctx is None:
            run = self.repository.get_run(run_id)
            if run and run.status != RunStatus.ENDED:
                run.status = RunStatus.ENDED
                run.ended_at = datetime.now(UTC)
                self.repository.update_run(run)
            return run is not None
        ctx.end_requested = True
        await ctx.teardown()
        run = ctx.run
        if run.status != RunStatus.ENDED:
            run.status = RunStatus.ENDED
            run.ended_at = datetime.now(UTC)
        self.repository.update_run(run)
        self.registry.remove(run_id)
        return True

    async def check_global_safety(self, run_id: str) -> None:
        outcome = evaluate_global_safety()
        if outcome and not outcome.safe:
            await self.pause(run_id, source=outcome.source, description=outcome.description)

    def create_run(
        self,
        *,
        gymbo_session_id: str,
        session_exercise_id: str,
        trainer_id: str,
        client_id: str,
        exercise_type: str,
        config: ExerciseRunConfig,
    ) -> CoachedExerciseRun:
        run = CoachedExerciseRun(
            gymbo_session_id=gymbo_session_id,
            session_exercise_id=session_exercise_id,
            trainer_id=trainer_id,
            client_id=client_id,
            exercise_type=exercise_type,
            config=config,
        )
        return self.repository.create_run(run)
