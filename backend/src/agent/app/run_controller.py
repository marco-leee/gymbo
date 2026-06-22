"""Run lifecycle controller."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from langgraph.types import Command

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
from agent.graphs.factory import (
    build_checkpointer,
    build_dependencies,
    build_session_graph,
    build_voice_graph,
)
from agent.graphs.runtime import build_graph_config
from agent.graphs.state import build_initial_state
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
        self._checkpointer = build_checkpointer()
        self._session_graph = build_session_graph(checkpointer=self._checkpointer)
        self._voice_graph = build_voice_graph()

    def _build_config(self, ctx: RunContext):
        return build_graph_config(
            ctx=ctx,
            deps=self._deps,
            publisher=self.publisher,
            repository=self.repository,
        )

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

        config = self._build_config(ctx)
        await ctx.start_voice_graph_consumer(self._voice_graph, config)

        ctx.run.status = RunStatus.PREPARING
        self.repository.update_run(ctx.run)
        initial = build_initial_state(ctx.run)

        async def _run_session() -> None:
            try:
                await self._session_graph.ainvoke(initial, config)
            except Exception:
                logger.exception("Session graph failed for run %s", run_id)

        ctx.session_task = asyncio.create_task(_run_session())
        return ctx

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

        config = self._build_config(ctx)
        if ctx.session_task is None or ctx.session_task.done():
            ctx.session_task = asyncio.create_task(
                self._session_graph.ainvoke(Command(resume=True), config)
            )
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
