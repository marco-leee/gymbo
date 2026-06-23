"""Kalman smoothing / prediction for primary person bounding boxes in frame pixels."""

from __future__ import annotations

import cv2
import numpy as np

from pipeline.pose_kalman import KalmanNoiseConfig
from pipeline.yolo_compat import clamp_crop_xyxy

_MIN_CONFIDENCE = 1e-3
_MIN_BOX_SIZE = 8
_DEFAULT_BBOX_MEASUREMENT_NOISE = 0.2


def _xyxy_to_cxcywh(xyxy: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = xyxy
    w = max(float(x2 - x1), float(_MIN_BOX_SIZE))
    h = max(float(y2 - y1), float(_MIN_BOX_SIZE))
    cx = (float(x1) + float(x2)) / 2.0
    cy = (float(y1) + float(y2)) / 2.0
    return cx, cy, w, h


def _cxcywh_to_xyxy(
    cx: float, cy: float, w: float, h: float
) -> tuple[float, float, float, float]:
    w = max(float(w), float(_MIN_BOX_SIZE))
    h = max(float(h), float(_MIN_BOX_SIZE))
    half_w = w / 2.0
    half_h = h / 2.0
    return cx - half_w, cy - half_h, cx + half_w, cy + half_h


def _clamp_xyxy_int(
    xyxy: tuple[float, float, float, float], frame_w: int, frame_h: int
) -> tuple[int, int, int, int] | None:
    x1, y1, x2, y2 = xyxy
    return clamp_crop_xyxy(int(x1), int(y1), int(x2), int(y2), frame_w, frame_h)


class BBoxKalmanFilter:
    """Constant-velocity Kalman filter on bbox center and size in frame pixels."""

    def __init__(self, *, noise: KalmanNoiseConfig | None = None) -> None:
        noise = noise or KalmanNoiseConfig(
            measurement_noise=_DEFAULT_BBOX_MEASUREMENT_NOISE
        )
        self._kf = cv2.KalmanFilter(8, 4, 0, cv2.CV_32F)
        self._kf.transitionMatrix = np.array(
            [
                [1, 0, 0, 0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0, 1, 0],
                [0, 0, 0, 1, 0, 0, 0, 1],
                [0, 0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 1],
            ],
            dtype=np.float32,
        )
        self._kf.measurementMatrix = np.array(
            [
                [1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 0],
            ],
            dtype=np.float32,
        )
        self._kf.processNoiseCov = np.eye(8, dtype=np.float32) * noise.process_noise
        self._kf.measurementNoiseCov = (
            np.eye(4, dtype=np.float32) * noise.measurement_noise
        )
        self._kf.errorCovPost = np.eye(8, dtype=np.float32)
        self._measurement_noise_base = float(noise.measurement_noise)
        self.initialized = False

    def reset(self) -> None:
        self.initialized = False
        self._kf.statePost = np.zeros((8, 1), dtype=np.float32)
        self._kf.errorCovPost = np.eye(8, dtype=np.float32)

    def has_state(self) -> bool:
        return self.initialized

    def _state_cxcywh(self) -> tuple[float, float, float, float]:
        s = self._kf.statePost
        return float(s[0, 0]), float(s[1, 0]), float(s[2, 0]), float(s[3, 0])

    def predict(self) -> tuple[float, float, float, float] | None:
        if not self.initialized:
            return None
        state = self._kf.predict()
        return (
            float(state[0, 0]),
            float(state[1, 0]),
            float(state[2, 0]),
            float(state[3, 0]),
        )

    def update(
        self, xyxy: tuple[float, float, float, float], *, confidence: float = 1.0
    ) -> tuple[float, float, float, float]:
        cx, cy, bw, bh = _xyxy_to_cxcywh(xyxy)
        conf = max(float(confidence), _MIN_CONFIDENCE)
        r_scale = 1.0 / conf
        self._kf.measurementNoiseCov = (
            np.eye(4, dtype=np.float32) * self._measurement_noise_base * r_scale
        )
        meas = np.array([[cx], [cy], [bw], [bh]], dtype=np.float32)
        if not self.initialized:
            self._kf.statePost = np.array(
                [[cx], [cy], [bw], [bh], [0.0], [0.0], [0.0], [0.0]],
                dtype=np.float32,
            )
            self.initialized = True
            return cx, cy, bw, bh
        self._kf.predict()
        corrected = self._kf.correct(meas)
        return (
            float(corrected[0, 0]),
            float(corrected[1, 0]),
            float(corrected[2, 0]),
            float(corrected[3, 0]),
        )

    def apply(
        self,
        raw_xyxy: tuple[int, int, int, int],
        *,
        confidence: float,
        frame_w: int,
        frame_h: int,
    ) -> tuple[int, int, int, int] | None:
        cxcywh = self.update(
            (float(raw_xyxy[0]), float(raw_xyxy[1]), float(raw_xyxy[2]), float(raw_xyxy[3])),
            confidence=confidence,
        )
        xyxy = _cxcywh_to_xyxy(*cxcywh)
        return _clamp_xyxy_int(xyxy, frame_w, frame_h)

    def predict_clamped(
        self, frame_w: int, frame_h: int
    ) -> tuple[int, int, int, int] | None:
        cxcywh = self.predict()
        if cxcywh is None:
            return None
        xyxy = _cxcywh_to_xyxy(*cxcywh)
        return _clamp_xyxy_int(xyxy, frame_w, frame_h)


__all__ = ["BBoxKalmanFilter"]
