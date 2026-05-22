"""RunPod job envelope parsing (no runpod SDK / ML stack)."""

from __future__ import annotations

import pytest

from runpod_video_handler import parse_runpod_job


def test_parse_runpod_job_requires_input_key() -> None:
    with pytest.raises(ValueError, match='Missing job\\["input"\\]'):
        parse_runpod_job({"id": "test-job-id"})


def test_parse_runpod_job_validates_envelope() -> None:
    job_payload = {
        "session_id": "507f1f77bcf86cd799439011",
        "exercise_id": "507f1f77bcf86cd799439012",
        "set_id": "507f1f77bcf86cd799439013",
        "r2_key": "session/x/exercises/x/sets/x/video.mp4",
        "job_id": "job-abc",
        "exercise_key": "squat",
    }
    model = parse_runpod_job({"input": job_payload})
    assert model.job_id == "job-abc"
    assert model.session_id == job_payload["session_id"]
    assert model.exercise_key == "squat"
