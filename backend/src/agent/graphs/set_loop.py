"""Set observation subgraph — per-frame loop."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from agent.domain.observation_merger import merge_observation, reset_set_reps
from agent.domain.rep_completion import is_set_complete
from agent.domain.safety_evaluator import evaluate_set_safety
from agent.domain.models import RunPhase, RunStatus, VoiceOutEvent
from agent.pipeline.preprocessor import decode_incoming, incoming_to_snapshot
from agent.pipeline.vlm.openrouter_adapter import VLMContextAdapter

if TYPE_CHECKING:
    from agent.app.event_publisher import RunEventPublisher
    from agent.app.run_context import RunContext
    from agent.graphs.factory import GraphDependencies

logger = logging.getLogger(__name__)

CYCLE_INTERVAL_SEC = 1.0


class SetLoopRunner:
    def __init__(
        self,
        ctx: RunContext,
        deps: GraphDependencies,
        publisher: RunEventPublisher,
    ) -> None:
        self.ctx = ctx
        self.deps = deps
        self.publisher = publisher
        self._frame_index = 0

    async def run_set(self) -> bool:
        """Run observation cycles until set complete, emergency, or end requested."""
        run = self.ctx.run
        run.phase = RunPhase.SET_IN_PROGRESS
        reset_set_reps(run.merged_observation_state)
        await self.publisher.publish_state(self.ctx)

        while True:
            if self.ctx.paused or self.ctx.end_requested:
                return False
            if self.ctx.end_set_requested:
                self.ctx.end_set_requested = False
                return True

            if is_set_complete(
                run.merged_observation_state.completed_reps,
                run.config.target_reps_per_set,
            ):
                return True

            await self._observation_cycle()
            await asyncio.sleep(CYCLE_INTERVAL_SEC)

    async def _observation_cycle(self) -> None:
        ctx = self.ctx
        if ctx.paused:
            return

        frame = ctx.frame_buffer.latest()
        if frame is None:
            logger.debug("Empty frame buffer — skipping cycle")
            return

        try:
            bgr = decode_incoming(frame)
            self.deps.pose.estimate(bgr)
        except Exception as exc:
            logger.warning("Pose/preprocess failed: %s", exc)
            return

        snapshot = incoming_to_snapshot(frame, self._frame_index)
        self._frame_index += 1
        prior = ctx.frame_history.prior_frames()
        all_frames = prior + [snapshot]
        ctx.frame_history.append(snapshot)

        vlm_ctx = VLMContextAdapter(
            merged_state=ctx.run.merged_observation_state,
            set_number=ctx.run.current_set_number,
            exercise_type=ctx.run.exercise_type,
            recent_coaching=ctx.recent_coaching,
        )

        try:
            vlm = self.deps.vlm.analyze(frames=all_frames, context=vlm_ctx)
        except Exception as exc:
            logger.warning("VLM analyze failed: %s", exc)
            return

        if vlm.action == "voice_out" and vlm.focus_issue:
            event = VoiceOutEvent(
                run_id=ctx.run.id,
                set_number=ctx.run.current_set_number,
                focus_issue=vlm.focus_issue,
                reason=vlm.voice_reason or "Form cue needed",
                severity=vlm.severity,
                frame_seq=frame.seq,
            )
            await ctx.enqueue_voice(event)

        merge_observation(ctx.run.merged_observation_state, vlm)

        safety = evaluate_set_safety(vlm)
        if not safety.safe:
            await self._handle_emergency(safety.description, source=safety.source)
            return

        await self.publisher.publish_state(ctx)

    async def _handle_emergency(self, description: str, *, source: str) -> None:
        self.ctx.paused = True
        self.ctx.run.status = RunStatus.PAUSED
        await self.publisher.publish_emergency(
            self.ctx,
            source=source,
            severity="critical",
            description=description,
        )
