"""Unit tests for per-joint pose Kalman filtering."""

from __future__ import annotations

import numpy as np

from pipeline.pose_kalman import JointKalman2D, PoseKalmanBank
from pipeline.schemas import LandmarkPoint


def _lm(x: float, y: float, *, vis: float = 1.0) -> LandmarkPoint:
    return LandmarkPoint(x=x, y=y, z=0.0, visibility=vis, presence=vis)


def _make_landmarks(
    frame_x: float, frame_y: float, crop: tuple[int, int, int, int]
) -> list[LandmarkPoint]:
    x1, y1, x2, y2 = crop
    cw = float(max(x2 - x1, 1))
    ch = float(max(y2 - y1, 1))
    nx = (frame_x - x1) / cw
    ny = (frame_y - y1) / ch
    return [_lm(nx, ny) for _ in range(33)]


def test_joint_kalman_smooths_noisy_trajectory():
    joint = JointKalman2D()
    true_x = 100.0
    rng = np.random.default_rng(42)
    raw: list[float] = []
    filtered: list[float] = []
    for _ in range(30):
        noisy = true_x + float(rng.normal(0.0, 8.0))
        raw.append(noisy)
        fx, _ = joint.update(noisy, 50.0, visibility=1.0)
        filtered.append(fx)
    assert np.var(filtered) < np.var(raw)


def test_visibility_gating_ignores_bad_measurement():
    bank = PoseKalmanBank()
    crop = (0, 0, 100, 100)
    good = _make_landmarks(50.0, 50.0, crop)
    bank.apply_to_landmarks(good, crop, vis_threshold=0.5)

    bad = [_lm(0.99, 0.99, vis=0.01) for _ in range(33)]
    predicted = bank.apply_to_landmarks(bad, crop, vis_threshold=0.5)
    # Low-vis frame should stay near prior filtered position, not jump to 0.99.
    assert predicted[0].x < 0.8
    assert predicted[0].y < 0.8


def test_predict_landmarks_after_initialization():
    bank = PoseKalmanBank()
    crop = (10, 20, 110, 120)
    landmarks = _make_landmarks(60.0, 70.0, crop)
    bank.apply_to_landmarks(landmarks, crop, vis_threshold=0.5)
    assert bank.has_state()

    predicted = bank.predict_landmarks(crop)
    assert len(predicted) == 33
    assert all(np.isfinite(p.x) and np.isfinite(p.y) for p in predicted)
    assert predicted[0].visibility == 0.0


def test_crop_conversion_round_trip_with_moving_crop():
    bank = PoseKalmanBank()
    crop_a = (0, 0, 100, 100)
    landmarks_a = _make_landmarks(50.0, 50.0, crop_a)
    filtered_a = bank.apply_to_landmarks(landmarks_a, crop_a, vis_threshold=0.5)

    crop_b = (50, 50, 150, 150)
    # Same frame-pixel location under a shifted crop -> normalized (0, 0).
    landmarks_b = _make_landmarks(50.0, 50.0, crop_b)
    filtered_b = bank.apply_to_landmarks(landmarks_b, crop_b, vis_threshold=0.5)

    assert filtered_a[0].x == 0.5
    assert filtered_a[0].y == 0.5
    assert filtered_b[0].x == 0.0
    assert filtered_b[0].y == 0.0


def test_reset_clears_state():
    bank = PoseKalmanBank()
    crop = (0, 0, 100, 100)
    bank.apply_to_landmarks(_make_landmarks(40.0, 40.0, crop), crop, vis_threshold=0.5)
    assert bank.has_state()

    bank.reset()
    assert not bank.has_state()
    predicted = bank.predict_landmarks(crop)
    assert predicted[0].x == 0.0
    assert predicted[0].y == 0.0


def test_crop_iou_jump_resets_bank():
    bank = PoseKalmanBank(crop_iou_reset_threshold=0.3)
    crop_a = (0, 0, 100, 100)
    bank.apply_to_landmarks(_make_landmarks(50.0, 50.0, crop_a), crop_a, vis_threshold=0.5)
    assert bank.has_state()

    crop_far = (500, 500, 600, 600)
    bank.apply_to_landmarks(
        _make_landmarks(550.0, 550.0, crop_far), crop_far, vis_threshold=0.5
    )
    assert bank.has_state()
