"""Rest subgraph — timer and during-rest messages."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent.domain.models import RunPhase, RunStatus
from agent.infra.clock import SystemClock

if TYPE_CHECKING:
    from agent.app.event_publisher import RunEventPublisher
    from agent.app.run_context import RunContext

logger = logging.getLogger(__name__)

REST_TICK_SEC = 15


class RestRunner:
    def __init__(
        self,
        ctx: RunContext,
        publisher: RunEventPublisher,
        clock: SystemClock | None = None,
    ) -> None:
        self.ctx = ctx
        self.publisher = publisher
        self.clock = clock or SystemClock()

    async def run_rest(self) -> None:
        run = self.ctx.run
        run.status = RunStatus.RESTING
        run.phase = RunPhase.REST
        duration = run.config.rest_duration_sec
        await self.publisher.publish_phase_message(
            self.ctx,
            phase="rest",
            message=f"Rest for {duration} seconds. Breathe and recover.",
            metadata={"set_number": run.current_set_number, "duration_sec": duration},
        )
        await self.publisher.publish_state(self.ctx)

        elapsed = 0
        while elapsed < duration:
            if self.ctx.end_rest_requested or self.ctx.end_requested or self.ctx.paused:
                self.ctx.end_rest_requested = False
                return
            await self.clock.sleep(min(REST_TICK_SEC, duration - elapsed))
            elapsed += REST_TICK_SEC
            if elapsed < duration:
                msg = "Stay loose — next set coming up."
                self.ctx.rest_activities.append(msg)
                await self.publisher.publish_phase_message(
                    self.ctx,
                    phase="rest",
                    message=msg,
                    metadata={"set_number": run.current_set_number},
                )

        run.status = RunStatus.ACTIVE
