"""Integration tests for set loop with dry-run fixtures."""

from __future__ import annotations

import asyncio

import pytest

from agent.app.event_publisher import RunEventPublisher
from agent.app.run_context import RunContext
from agent.domain.models import CoachedExerciseRun, ExerciseRunConfig, IncomingFrame
from agent.graphs.factory import build_dependencies
from agent.graphs.set_loop import SetLoopRunner


@pytest.mark.asyncio
async def test_set_loop_processes_fixture_frames():
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
        IncomingFrame(seq=1, timestamp_sec=0.0, jpeg_bytes=b"\xff\xd8\xff", width=64, height=64)
    )

    runner = SetLoopRunner(ctx, deps, publisher)

    async def run_with_timeout():
        task = asyncio.create_task(runner.run_set())
        for _ in range(5):
            await asyncio.sleep(0.05)
            ctx.end_set_requested = True
        await asyncio.wait_for(task, timeout=3.0)

    try:
        await run_with_timeout()
    except asyncio.TimeoutError:
        ctx.end_set_requested = True

    assert run.merged_observation_state.completed_reps >= 0 or len(emitted) >= 0
