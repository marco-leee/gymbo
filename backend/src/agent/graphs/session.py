"""Session graph — prepare → setup → sets → rest → feedback."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agent.domain.exercise_feedback import build_feedback_summary, format_feedback_text
from agent.domain.models import RunPhase, RunStatus
from agent.domain.rep_completion import has_more_sets
from agent.exercises.registry import get_profile
from agent.graphs.rest import RestRunner
from agent.graphs.set_loop import SetLoopRunner

if TYPE_CHECKING:
    from agent.app.event_publisher import RunEventPublisher
    from agent.app.run_context import RunContext
    from agent.graphs.factory import GraphDependencies
    from agent.infra.run_repository import RunRepository

logger = logging.getLogger(__name__)


class SessionRunner:
    def __init__(
        self,
        ctx: RunContext,
        deps: GraphDependencies,
        publisher: RunEventPublisher,
        repository: RunRepository,
    ) -> None:
        self.ctx = ctx
        self.deps = deps
        self.publisher = publisher
        self.repository = repository

    async def run(self) -> None:
        run = self.ctx.run
        profile = get_profile(run.exercise_type)

        run.status = RunStatus.PREPARING
        run.phase = RunPhase.PREPARE
        run.started_at = datetime.now(UTC)
        await self.publisher.publish_phase_message(
            self.ctx, phase="prepare", message=profile.prep_message
        )
        await self.publisher.publish_state(self.ctx)
        await asyncio.sleep(2)

        if self.ctx.end_requested or self.ctx.paused:
            return

        run.status = RunStatus.SETUP
        run.phase = RunPhase.SETUP
        await self.publisher.publish_phase_message(
            self.ctx, phase="setup", message=profile.setup_message
        )
        await self.publisher.publish_state(self.ctx)
        await asyncio.sleep(2)

        run.status = RunStatus.ACTIVE

        while has_more_sets(run.current_set_number, run.config.planned_sets):
            if self.ctx.end_requested or self.ctx.paused:
                break

            await self.publisher.publish_phase_message(
                self.ctx,
                phase="set_announce",
                message=f"Set {run.current_set_number} — target {run.config.target_reps_per_set} reps.",
                metadata={
                    "set_number": run.current_set_number,
                    "target_reps": run.config.target_reps_per_set,
                },
            )

            set_runner = SetLoopRunner(self.ctx, self.deps, self.publisher)
            set_complete = await set_runner.run_set()
            if not set_complete and (self.ctx.paused or self.ctx.end_requested):
                break

            run.completed_sets += 1

            if not has_more_sets(run.current_set_number, run.config.planned_sets):
                break

            if run.config.rest_needed and run.config.rest_duration_sec > 0:
                rest_runner = RestRunner(self.ctx, self.publisher)
                await rest_runner.run_rest()

            run.current_set_number += 1
            self.ctx.run.merged_observation_state.completed_reps = 0

        if self.ctx.end_requested:
            await self._end_run()
            return

        if self.ctx.paused:
            return

        await self._generate_feedback()

    async def _generate_feedback(self) -> None:
        run = self.ctx.run
        run.status = RunStatus.FEEDBACK
        run.phase = RunPhase.FEEDBACK
        coaching = self.repository.list_coaching_for_run(run.id)
        summary = build_feedback_summary(
            merged=run.merged_observation_state,
            coaching_events=coaching,
            planned_sets=run.config.planned_sets,
            target_reps=run.config.target_reps_per_set,
        )
        feedback = format_feedback_text(summary)
        run.exercise_feedback = feedback
        await self.publisher.publish_phase_message(
            self.ctx, phase="feedback", message=feedback, metadata=summary
        )
        await self._finalize()

    async def _end_run(self) -> None:
        if not self.ctx.run.exercise_feedback:
            coaching = self.repository.list_coaching_for_run(self.ctx.run.id)
            summary = build_feedback_summary(
                merged=self.ctx.run.merged_observation_state,
                coaching_events=coaching,
                planned_sets=self.ctx.run.config.planned_sets,
                target_reps=self.ctx.run.config.target_reps_per_set,
            )
            self.ctx.run.exercise_feedback = format_feedback_text(summary)
        await self._finalize()

    async def _finalize(self) -> None:
        run = self.ctx.run
        run.status = RunStatus.ENDED
        run.phase = RunPhase.SESSION_COMPLETE
        run.ended_at = datetime.now(UTC)
        self.repository.update_run(run)
        await self.publisher.publish_phase_message(
            self.ctx,
            phase="session_complete",
            message="Exercise complete. Great work!",
        )
        await self.publisher.publish_state(self.ctx)
