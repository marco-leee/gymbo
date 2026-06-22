"""LangGraph state schema for trainer agent orchestration."""

from __future__ import annotations

from typing import Any, TypedDict

from agent.domain.models import CoachedExerciseRun, RunPhase, RunStatus


class TrainerGraphState(TypedDict, total=False):
    run_id: str
    status: str
    phase: str
    current_set_number: int
    completed_sets: int
    frame_index: int
    rest_elapsed_sec: int
    rest_duration_sec: int
    set_complete: bool
    set_emergency: bool
    end_requested: bool
    paused: bool
    rest_complete: bool
    rest_skipped: bool
    has_frame: bool
    skip_preprocess: bool
    vlm_skipped: bool
    vlm_action: str
    vlm_focus_issue: str | None
    vlm_voice_reason: str | None
    vlm_severity: str
    vlm_issues: list[str]
    frame_seq: int
    voice_event: dict[str, Any]
    voice_event_model: dict[str, Any]
    voice_decision: str
    voice_message: str
    voice_repeat_count: int


def build_initial_state(run: CoachedExerciseRun) -> TrainerGraphState:
    return {
        "run_id": run.id,
        "status": run.status.value,
        "phase": run.phase.value,
        "current_set_number": run.current_set_number,
        "completed_sets": run.completed_sets,
        "frame_index": 0,
        "rest_elapsed_sec": 0,
        "set_complete": False,
        "set_emergency": False,
        "end_requested": False,
        "paused": False,
    }


def state_patch_from_run(run: CoachedExerciseRun, **extra: Any) -> TrainerGraphState:
    patch: TrainerGraphState = {
        "run_id": run.id,
        "status": run.status.value,
        "phase": run.phase.value,
        "current_set_number": run.current_set_number,
        "completed_sets": run.completed_sets,
    }
    patch.update(extra)
    return patch


def apply_status_phase(run: CoachedExerciseRun, status: RunStatus, phase: RunPhase) -> None:
    run.status = status
    run.phase = phase
