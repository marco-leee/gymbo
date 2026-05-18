"""Tests for :mod:`yolo_inference_runtime` delegation.

This file is ignored by pytest unless ``RUN_ML_STACK_TESTS=1`` (see ``tests/conftest.py``).
When collected, mocks replace YOLO and ``infer_overall_result_from_bgr`` so no model forward passes run.

Opt-in::

    RUN_ML_STACK_TESTS=1 python -m pytest tests/test_yolo_inference_runtime.py

"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from models.exercise import ExerciseType
from utils.video import CameraView
from yolo_inference_runtime import YoloInferenceRuntime


@pytest.fixture
def fake_weights(tmp_path):
    d = tmp_path / "d.pt"
    p = tmp_path / "p.pt"
    s = tmp_path / "s.pt"
    for f in (d, p, s):
        f.write_bytes(b"stub")
    return d, p, s


def test_runtime_infer_delegates(monkeypatch, fake_weights):
    d, p, s = fake_weights
    monkeypatch.setattr(
        "yolo_inference_runtime.YOLO",
        lambda path: MagicMock(name=f"YOLO({path})"),
    )

    captured = {}

    def fake_infer(frame_bgr, **kwargs):
        captured["frame_shape"] = frame_bgr.shape
        captured.update(kwargs)
        return None

    monkeypatch.setattr(
        "yolo_inference_runtime.infer_overall_result_from_bgr",
        fake_infer,
    )

    rt = YoloInferenceRuntime(
        str(d),
        str(p),
        str(s),
        conf_threshold=0.61,
    )
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    out = rt.infer(frame, idx=7, timestamp=123.45)
    assert out is None
    assert captured["idx"] == 7
    assert captured["timestamp"] == 123.45
    assert captured["conf_threshold"] == 0.61
    assert captured["frame_shape"] == (4, 4, 3)
    assert captured["exercise_type"] == ExerciseType.SQUAT
    assert captured["camera_view"] == CameraView.RIGHT

    rt.infer(
        frame,
        idx=8,
        timestamp=222.0,
        exercise_type=ExerciseType.LUNGE,
        camera_view=CameraView.LEFT,
    )
    assert captured["idx"] == 8
    assert captured["timestamp"] == 222.0
    assert captured["exercise_type"] == ExerciseType.LUNGE
    assert captured["camera_view"] == CameraView.LEFT
