"""Unit tests for TrainerGraphState helpers."""

from agent.domain.models import CoachedExerciseRun, ExerciseRunConfig, RunStatus
from agent.graphs.state import build_initial_state, state_patch_from_run


def test_build_initial_state_from_run():
    run = CoachedExerciseRun(
        id="run-1",
        gymbo_session_id="sess",
        session_exercise_id="ex",
        trainer_id="t",
        client_id="c",
        config=ExerciseRunConfig(planned_sets=2, target_reps_per_set=5),
    )
    state = build_initial_state(run)
    assert state["run_id"] == "run-1"
    assert state["current_set_number"] == 1
    assert state["completed_sets"] == 0
    assert state["frame_index"] == 0
    assert state["set_complete"] is False


def test_state_patch_from_run_reflects_updates():
    run = CoachedExerciseRun(
        id="run-2",
        gymbo_session_id="sess",
        session_exercise_id="ex",
        trainer_id="t",
        client_id="c",
    )
    run.status = RunStatus.ACTIVE
    run.completed_sets = 2
    patch = state_patch_from_run(run, set_complete=True)
    assert patch["status"] == "active"
    assert patch["completed_sets"] == 2
    assert patch["set_complete"] is True
