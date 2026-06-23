"""Unit tests for person bbox Kalman filtering."""

from __future__ import annotations

import numpy as np

from pipeline.bbox_kalman import BBoxKalmanFilter
from pipeline.yolo_compat import clamp_crop_xyxy


def _box(cx: float, cy: float, size: float = 80.0) -> tuple[int, int, int, int]:
    half = size / 2.0
    return (
        int(cx - half),
        int(cy - half),
        int(cx + half),
        int(cy + half),
    )


def test_bbox_kalman_smooths_noisy_center():
    filt = BBoxKalmanFilter()
    true_cx = 200.0
    rng = np.random.default_rng(7)
    raw_centers: list[float] = []
    filtered_centers: list[float] = []
    for _ in range(25):
        noisy_cx = true_cx + float(rng.normal(0.0, 12.0))
        raw_centers.append(noisy_cx)
        box = _box(noisy_cx, 150.0)
        out = filt.apply(box, confidence=0.9, frame_w=640, frame_h=480)
        assert out is not None
        filtered_centers.append((out[0] + out[2]) / 2.0)
    assert np.var(filtered_centers) < np.var(raw_centers)


def test_predict_after_init_returns_valid_crop():
    filt = BBoxKalmanFilter()
    assert not filt.has_state()
    box = _box(120.0, 100.0)
    applied = filt.apply(box, confidence=0.95, frame_w=640, frame_h=480)
    assert applied is not None
    assert filt.has_state()

    predicted = filt.predict_clamped(640, 480)
    assert predicted is not None
    assert clamp_crop_xyxy(*predicted, 640, 480) == predicted


def test_no_predict_before_init():
    filt = BBoxKalmanFilter()
    assert filt.predict_clamped(640, 480) is None
    assert not filt.has_state()


def test_low_confidence_moves_filter_less_than_high_confidence():
    high = BBoxKalmanFilter()
    low = BBoxKalmanFilter()
    seed_box = _box(100.0, 100.0)
    high.apply(seed_box, confidence=0.99, frame_w=640, frame_h=480)
    low.apply(seed_box, confidence=0.99, frame_w=640, frame_h=480)

    outlier = _box(300.0, 300.0, size=100.0)
    high_out = high.apply(outlier, confidence=0.99, frame_w=640, frame_h=480)
    low_out = low.apply(outlier, confidence=0.05, frame_w=640, frame_h=480)
    assert high_out is not None and low_out is not None

    high_cx = (high_out[0] + high_out[2]) / 2.0
    low_cx = (low_out[0] + low_out[2]) / 2.0
    assert abs(low_cx - 100.0) < abs(high_cx - 100.0)


def test_apply_and_predict_clamp_to_frame():
    filt = BBoxKalmanFilter()
    box = _box(620.0, 460.0, size=120.0)
    applied = filt.apply(box, confidence=0.9, frame_w=640, frame_h=480)
    assert applied is not None
    assert clamp_crop_xyxy(*applied, 640, 480) == applied

    predicted = filt.predict_clamped(640, 480)
    assert predicted is not None
    assert clamp_crop_xyxy(*predicted, 640, 480) == predicted


def test_reset_clears_state():
    filt = BBoxKalmanFilter()
    filt.apply(_box(50.0, 50.0), confidence=0.9, frame_w=640, frame_h=480)
    assert filt.has_state()
    filt.reset()
    assert not filt.has_state()
    assert filt.predict_clamped(640, 480) is None
