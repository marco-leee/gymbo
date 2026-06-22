"""Unit tests for Yolo26PoseAdapter (YOLO mocked; no checkpoint load)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.fixture
def frame_bgr() -> np.ndarray:
    return np.zeros((480, 640, 3), dtype=np.uint8)


def _mock_boxes(*, xyxy: list[float], conf: float = 0.9, cls: int = 0) -> MagicMock:
    boxes = MagicMock()
    boxes.__len__.return_value = 1
    boxes.cls = [cls]
    boxes.conf = [conf]
    boxes.xyxy = [MagicMock()]
    boxes.xyxy[0].tolist.return_value = xyxy
    return boxes


def _mock_keypoints(*, n: int = 17) -> MagicMock:
    data = MagicMock()
    data.shape = (1, n, 3)
    data.__getitem__.return_value = MagicMock()
    kp = MagicMock()
    kp.data = data
    return kp


@patch("agent.pipeline.pose.yolo26_adapter.YOLO")
def test_yolo26_adapter_returns_pose_result(mock_yolo_cls: MagicMock, frame_bgr: np.ndarray) -> None:
    from agent.pipeline.pose.yolo26_adapter import Yolo26PoseAdapter

    detect_result = MagicMock()
    detect_result.boxes = _mock_boxes(xyxy=[50.0, 50.0, 300.0, 400.0])
    detect_result.names = {0: "person"}

    pose_result = MagicMock()
    pose_result.boxes = _mock_boxes(xyxy=[10.0, 10.0, 200.0, 350.0])
    pose_result.names = {0: "person"}
    pose_result.keypoints = _mock_keypoints()

    detector = MagicMock()
    pose_model = MagicMock()
    detector.side_effect = None
    pose_model.side_effect = None
    detector.return_value = [detect_result]
    pose_model.return_value = [pose_result]
    mock_yolo_cls.side_effect = [detector, pose_model]

    with patch(
        "agent.pipeline.pose.yolo26_adapter.yolo_keypoints_to_body33",
        return_value=[{"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.9, "presence": 0.9}] * 33,
    ):
        adapter = Yolo26PoseAdapter(
            detect_weights="/tmp/yolo26n.pt",
            pose_weights="/tmp/yolo26n-pose.pt",
        )
        result = adapter.estimate(frame_bgr)

    assert result is not None
    assert len(result.landmarks) == 33
    assert result.confidence >= 0.9
    assert result.annotated_b64 is not None


@patch("agent.pipeline.pose.yolo26_adapter.YOLO")
def test_yolo26_adapter_no_detection(mock_yolo_cls: MagicMock, frame_bgr: np.ndarray) -> None:
    from agent.pipeline.pose.yolo26_adapter import Yolo26PoseAdapter

    detect_result = MagicMock()
    detect_result.boxes = None
    detector = MagicMock()
    pose_model = MagicMock()
    mock_yolo_cls.side_effect = [detector, pose_model]
    detector.return_value = [detect_result]

    adapter = Yolo26PoseAdapter(
        detect_weights="/tmp/yolo26n.pt",
        pose_weights="/tmp/yolo26n-pose.pt",
    )
    assert adapter.estimate(frame_bgr) is None


def test_yolo26_default_paths_use_n_model() -> None:
    from agent.pipeline.pose.yolo26_adapter import _yolo26_weight_paths

    detect, pose = _yolo26_weight_paths(Path("/models"), "n")
    assert detect.name == "yolo26n.pt"
    assert pose.name == "yolo26n-pose.pt"
