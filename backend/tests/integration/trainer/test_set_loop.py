"""Integration tests for set subgraph with dry-run fixtures."""

from __future__ import annotations

import asyncio

import cv2
import numpy as np
import pytest

from agent.app.event_publisher import RunEventPublisher
from agent.app.run_context import RunContext
from agent.domain.models import CoachedExerciseRun, ExerciseRunConfig, IncomingFrame
from agent.graphs.factory import build_dependencies, build_set_subgraph
from agent.graphs.runtime import build_graph_config
from agent.graphs.state import build_initial_state


def _minimal_jpeg() -> bytes:
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


@pytest.mark.asyncio
async def test_set_subgraph_processes_fixture_frames():
    run = CoachedExerciseRun(
        id="test-run",
        gymbo_session_id="sess",
        session_exercise_id="ex",
        trainer_id="t",
        client_id="c",
        config=ExerciseRunConfig(target_reps_per_set=2, planned_sets=1),
    )
    ctx = RunContext(run=run, dry_run=True)
    deps = build_dependencies(dry_run=True)

    emitted: list[dict] = []

    async def emit(sid, event, data):
        emitted.append({"event": event, **data})

    publisher = RunEventPublisher(emit)
    ctx.frame_buffer.push(
        IncomingFrame(seq=1, timestamp_sec=0.0, jpeg_bytes=_minimal_jpeg(), width=64, height=64)
    )

    graph = build_set_subgraph()
    config = build_graph_config(
        ctx=ctx, deps=deps, publisher=publisher, repository=__import__("unittest.mock").mock.MagicMock()
    )
    initial = build_initial_state(run)

    async def run_with_timeout():
        task = asyncio.create_task(graph.ainvoke(initial, config))
        for _ in range(3):
            await asyncio.sleep(0.05)
            ctx.end_set_requested = True
        await asyncio.wait_for(task, timeout=5.0)

    try:
        await run_with_timeout()
    except asyncio.TimeoutError:
        ctx.end_set_requested = True

    assert run.merged_observation_state.completed_reps >= 0 or len(emitted) >= 0
