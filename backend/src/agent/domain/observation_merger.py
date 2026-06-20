"""Merge VLM results into accumulated observation state."""

from __future__ import annotations

from agent.domain.models import MergedObservationState, VLMFrameResult


def merge_observation(
    state: MergedObservationState,
    vlm: VLMFrameResult,
    *,
    max_history: int = 50,
) -> MergedObservationState:
    """Apply a VLM frame result to merged state (FR-022: rep from VLM only)."""
    state.in_rep = vlm.in_rep
    state.rep_phase = vlm.rep_phase
    if vlm.issues:
        state.active_issues = list(vlm.issues)
        for issue in vlm.issues:
            key = issue.strip().lower()
            state.recurring_issues[key] = state.recurring_issues.get(key, 0) + 1
    if vlm.rep_completed:
        state.completed_reps += 1
        state.total_session_reps += 1
    state.frame_results.append(vlm)
    if len(state.frame_results) > max_history:
        state.frame_results = state.frame_results[-max_history:]
    return state


def reset_set_reps(state: MergedObservationState) -> MergedObservationState:
    """Reset per-set rep counter when starting a new set."""
    state.completed_reps = 0
    state.active_issues = []
    state.in_rep = False
    state.rep_phase = "setup"
    return state
