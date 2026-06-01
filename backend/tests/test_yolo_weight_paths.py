"""Tests for YOLO26 weight path resolution (no checkpoints on disk)."""

from pathlib import Path

import pytest

from video_queue_worker import YOLO_MODEL_SIZES, yolo26_weight_paths


def test_yolo26_weight_paths_n() -> None:
    root = Path("/app/src/pose_models")
    detect, seg, pose = yolo26_weight_paths(root, "n")
    assert detect == str(root / "yolo26n.pt")
    assert seg == str(root / "yolo26n-seg.pt")
    assert pose == str(root / "yolo26n-pose.pt")


def test_yolo26_weight_paths_x() -> None:
    root = Path("pose_models")
    detect, seg, pose = yolo26_weight_paths(root, "x")
    assert detect.endswith("yolo26x.pt")
    assert seg.endswith("yolo26x-seg.pt")
    assert pose.endswith("yolo26x-pose.pt")


@pytest.mark.parametrize("size", YOLO_MODEL_SIZES)
def test_yolo26_weight_paths_all_sizes(size: str) -> None:
    detect, seg, pose = yolo26_weight_paths(Path("pose_models"), size)
    assert f"yolo26{size}.pt" in detect
    assert f"yolo26{size}-seg.pt" in seg
    assert f"yolo26{size}-pose.pt" in pose


def test_yolo26_weight_paths_invalid_size() -> None:
    with pytest.raises(ValueError, match="Invalid YOLO model size"):
        yolo26_weight_paths(Path("pose_models"), "z")
