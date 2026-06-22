"""Integration tests for compiled session graph."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import cv2
import numpy as np
import pytest

from agent.app.event_publisher import RunEventPublisher
from agent.app.run_context import RunContext
from agent.domain.models import CoachedExerciseRun, CoachingEventRecord, ExerciseRunConfig, IncomingFrame
from agent.graphs.factory import build_dependencies, build_session_graph, build_voice_graph
from agent.graphs.runtime import build_graph_config
from agent.graphs.state import build_initial_state


def _minimal_jpeg() -> bytes:
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


@dataclass
class FakeRunRepository:
    coaching: list[CoachingEventRecord] = field(default_factory=list)

    def update_run(self, run: CoachedExerciseRun) -> None:
        return None

    def list_coaching_for_run(self, run_id: str) -> list[CoachingEventRecord]:
        return [e for e in self.coaching if e.run_id == run_id]

    def save_coaching_event(self, record: CoachingEventRecord) -> None:
        self.coaching.append(record)


@pytest.mark.asyncio
async def test_session_graph_dry_run_completes():
    run = CoachedExerciseRun(
        id="graph-run",
        gymbo_session_id="sess",
        session_exercise_id="ex",
        trainer_id="t",
        client_id="c",
        config=ExerciseRunConfig(
            planned_sets=1,
            target_reps_per_set=1,
            rest_duration_sec=0,
            rest_needed=False,
        ),
    )
    ctx = RunContext(run=run, dry_run=True)
    ctx.sid = "test-sid"
    deps = build_dependencies(dry_run=True)
    repo = FakeRunRepository()
    events: list[str] = []

    async def emit(_sid, event, _data):
        events.append(event)

    publisher = RunEventPublisher(emit)
    config = build_graph_config(ctx=ctx, deps=deps, publisher=publisher, repository=repo)
    voice_graph = build_voice_graph()
    await ctx.start_voice_graph_consumer(voice_graph, config)

    ctx.frame_buffer.push(
        IncomingFrame(seq=1, timestamp_sec=0.0, jpeg_bytes=_minimal_jpeg(), width=64, height=64)
    )

    graph = build_session_graph()
    initial = build_initial_state(run)

    await asyncio.wait_for(graph.ainvoke(initial, config), timeout=10.0)

    assert run.status.value == "ended"
    assert "trainer:phase_message" in events or "trainer:state" in events
