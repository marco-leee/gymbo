"""Unit tests for observation merger rep counting."""

from __future__ import annotations

from agent.domain.models import MergedObservationState, VLMFrameResult
from agent.domain.observation_merger import merge_observation, reset_set_reps


def test_rep_increment_on_rep_completed():
    state = MergedObservationState()
    vlm = VLMFrameResult(rep_completed=True, rep_phase="lockout")
    merge_observation(state, vlm)
    assert state.completed_reps == 1
    assert state.total_session_reps == 1


def test_no_increment_without_rep_completed():
    state = MergedObservationState()
    vlm = VLMFrameResult(rep_completed=False, rep_phase="descending")
    merge_observation(state, vlm)
    assert state.completed_reps == 0


def test_reset_set_reps():
    state = MergedObservationState(completed_reps=5, active_issues=["lean"])
    reset_set_reps(state)
    assert state.completed_reps == 0
    assert state.active_issues == []
