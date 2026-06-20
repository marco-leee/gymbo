"""VoiceOut subgraph — async cue generation and logging."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent.domain.models import CoachingEventRecord, VoiceOutDecision
from agent.domain.voice_dedup import evaluate_dedup

if TYPE_CHECKING:
    from agent.app.event_publisher import RunEventPublisher
    from agent.app.run_context import RunContext
    from agent.graphs.factory import GraphDependencies
    from agent.infra.run_repository import RunRepository

logger = logging.getLogger(__name__)


class VoiceOutHandler:
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

    async def handle_event(self, event) -> None:
        from agent.domain.models import VoiceOutEvent

        if not isinstance(event, VoiceOutEvent):
            return

        decision, repeat_state = evaluate_dedup(event, self.ctx.voice_repeat_state)
        self.ctx.voice_repeat_state = repeat_state

        if decision == VoiceOutDecision.INCREMENT:
            logger.debug("Voice dedup increment for %s", event.focus_issue)
            return

        trigger = "repeat_threshold" if repeat_state.repeat_count == 0 and decision == VoiceOutDecision.SPEAK else "new_issue"
        message = self.deps.cue_generator.generate(
            event=event,
            state=self.ctx.run.merged_observation_state,
        )

        record = CoachingEventRecord(
            run_id=event.run_id,
            message=message,
            focus_issue=event.focus_issue,
            trigger_reason=event.reason,
            severity=event.severity,
            set_number=event.set_number,
            dedup_repeat_count=repeat_state.repeat_count or None,
        )
        self.repository.save_coaching_event(record)
        self.ctx.recent_coaching.append(
            {
                "message": message,
                "focus_issue": event.focus_issue,
                "timestamp": event.timestamp.isoformat(),
            }
        )

        await self.publisher.publish_voice_cue(
            self.ctx,
            cue_id=record.id,
            message=message,
            focus_issue=event.focus_issue,
            severity=event.severity,
            trigger=trigger,
            repeat_count=repeat_state.repeat_count,
        )
