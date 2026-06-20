"""Rep-count accuracy benchmark (SC-003) using dry-run mock path."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.domain.models import FrameSnapshot, MergedObservationState
from agent.domain.observation_merger import merge_observation
from agent.pipeline.vlm.dry_run_adapter import DryRunVLMAdapter
from agent.pipeline.vlm.openrouter_adapter import VLMContextAdapter


@pytest.mark.asyncio
async def test_fixture_rep_completion_tracking():
    # Empty fixture dir forces deterministic mock with lockout rep_completed
    adapter = DryRunVLMAdapter(fixture_dir=Path("/nonexistent-fixtures"))
    ctx = VLMContextAdapter(
        merged_state=MergedObservationState(),
        set_number=1,
        exercise_type="overhead_squat",
    )
    state = MergedObservationState()
    rep_count = 0
    for i in range(12):
        snap = FrameSnapshot(frame_index=i, timestamp_sec=float(i), frame_b64="abc")
        vlm = adapter.analyze(frames=[snap], context=ctx)
        merge_observation(state, vlm)
        if vlm.rep_completed:
            rep_count += 1
    assert rep_count >= 1
    assert state.total_session_reps == rep_count
