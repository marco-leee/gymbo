"""Tests for pipeline biometrics (no YOLO)."""

from __future__ import annotations

import numpy as np

from models.exercise import ExerciseType
from models.overall_results import OverallResult
from pipeline.biometrics import FrameBiometricsResult, back_profile_to_snapshot, compute_frame_biometrics
from pipeline.back_profile import Back
from pipeline.enums import FramePerceptionStatus
from pipeline.frame_state import FramePerceptionState
from pipeline.schemas import FramePerceptionRecord, FrameSize
from utils.video import CameraView


def _minimal_record() -> FramePerceptionRecord:
    return FramePerceptionRecord(
        idx=0,
        timestamp=0.0,
        frame=FrameSize(width=640, height=480),
        status=FramePerceptionStatus.OK,
    )


def _lm(x: float, y: float, v: float = 1.0) -> dict:
    return {"x": x, "y": y, "z": 0.0, "visibility": v, "presence": v}


def test_compute_frame_biometrics_returns_none_without_overall_result() -> None:
    st = FramePerceptionState(
        overall_result=None,
        crop_xyxy=None,
        mask_u8_crop=np.ones((10, 10), dtype=np.uint8),
        cropped_frame=None,
        perception_record=_minimal_record(),
    )
    assert (
        compute_frame_biometrics(
            st,
            exercise_type=ExerciseType.SQUAT,
            camera_view=CameraView.RIGHT,
        )
        is None
    )


def test_back_profile_to_snapshot_offsets_full_frame_coords() -> None:
    raw = np.array([[10, 20], [12, 22]], dtype=np.int32)
    bk = Back(
        raw_pixels_crop_yx=raw,
        n_pixels=2,
        x_span=3,
        y_span=3,
        reference_segment="hip24-shoulder12",
    )
    snap = back_profile_to_snapshot(bk, (100, 50, 200, 150))
    assert snap.polyline_crop_yx == [[10, 20], [12, 22]]
    assert snap.polyline_full_frame_yx == [[60, 120], [62, 122]]
    assert snap.reference_segment == "hip24-shoulder12"


def test_compute_frame_biometrics_smoke_synthetic_pose_and_mask() -> None:
    """Squat KIPs + optional back polyline with synthetic landmarks / full mask."""
    landmarks = [_lm(0.5, 0.5) for _ in range(33)]
    landmarks[0] = _lm(0.5, 0.10)
    landmarks[9] = _lm(0.48, 0.14)
    landmarks[10] = _lm(0.52, 0.14)
    landmarks[11] = _lm(0.42, 0.28)
    landmarks[12] = _lm(0.58, 0.28)
    landmarks[23] = _lm(0.42, 0.52)
    landmarks[24] = _lm(0.58, 0.52)
    landmarks[25] = _lm(0.42, 0.72)
    landmarks[26] = _lm(0.58, 0.72)
    landmarks[27] = _lm(0.42, 0.92)
    landmarks[28] = _lm(0.58, 0.92)

    h, w = 128, 96
    mask = np.ones((h, w), dtype=np.uint8) * 255

    ov = OverallResult(
        idx=0,
        timestamp=0.0,
        pose_estimation_result={"pose_landmarks": [landmarks]},
        segmentation_result={"frame_crop_xyxy": [10, 20, 10 + w, 20 + h]},
    )
    st = FramePerceptionState(
        overall_result=ov,
        crop_xyxy=(10, 20, 10 + w, 20 + h),
        mask_u8_crop=mask,
        cropped_frame=None,
        perception_record=_minimal_record(),
    )

    bio = compute_frame_biometrics(
        st,
        exercise_type=ExerciseType.SQUAT,
        camera_view=CameraView.RIGHT,
    )
    assert bio is not None
    assert "INSIDE_KNEE" in bio.key_interest_points_2d
    parsed = FrameBiometricsResult.model_validate(
        bio.model_dump(mode="json"),
    )
    assert parsed.reps is None
    # Back geometry often resolves with full mask + landmarks; allow either way.
    if parsed.back_shape is not None:
        assert parsed.back_shape.n_vertices >= 2
