"""Per-joint Kalman smoothing for pose landmarks in full-frame pixel space."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from pipeline.schemas import LandmarkPoint

NUM_BODY_LANDMARKS = 33

# Default tuning — moderate process noise for lifting motion.
_DEFAULT_PROCESS_NOISE = 1e-2
_DEFAULT_MEASUREMENT_NOISE = 1e-1
_MIN_VISIBILITY = 1e-3
_CROP_IOU_RESET_THRESHOLD = 0.3


def _crop_iou(
    a: tuple[int, int, int, int], b: tuple[int, int, int, int]
) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    inter = float(iw * ih)
    if inter <= 0.0:
        return 0.0
    area_a = float(max(ax2 - ax1, 0) * max(ay2 - ay1, 0))
    area_b = float(max(bx2 - bx1, 0) * max(by2 - by1, 0))
    union = area_a + area_b - inter
    if union <= 0.0:
        return 0.0
    return inter / union


def _landmark_to_frame_px(
    lm: LandmarkPoint, crop_xyxy: tuple[int, int, int, int]
) -> tuple[float, float]:
    x1, y1, x2, y2 = crop_xyxy
    cw = float(max(x2 - x1, 1))
    ch = float(max(y2 - y1, 1))
    return x1 + lm.x * cw, y1 + lm.y * ch


def _frame_px_to_landmark_xy(
    fx: float, fy: float, crop_xyxy: tuple[int, int, int, int]
) -> tuple[float, float]:
    x1, y1, x2, y2 = crop_xyxy
    cw = float(max(x2 - x1, 1))
    ch = float(max(y2 - y1, 1))
    return (fx - x1) / cw, (fy - y1) / ch


@dataclass
class KalmanNoiseConfig:
    process_noise: float = _DEFAULT_PROCESS_NOISE
    measurement_noise: float = _DEFAULT_MEASUREMENT_NOISE


class JointKalman2D:
    """Constant-velocity Kalman filter for one joint in frame pixels."""

    def __init__(self, *, noise: KalmanNoiseConfig | None = None) -> None:
        noise = noise or KalmanNoiseConfig()
        self._kf = cv2.KalmanFilter(4, 2, 0, cv2.CV_32F)
        self._kf.transitionMatrix = np.array(
            [[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]],
            dtype=np.float32,
        )
        self._kf.measurementMatrix = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32
        )
        self._kf.processNoiseCov = np.eye(4, dtype=np.float32) * noise.process_noise
        self._kf.measurementNoiseCov = (
            np.eye(2, dtype=np.float32) * noise.measurement_noise
        )
        self._kf.errorCovPost = np.eye(4, dtype=np.float32)
        self._measurement_noise_base = float(noise.measurement_noise)
        self.initialized = False

    def predict(self) -> tuple[float, float]:
        if not self.initialized:
            return 0.0, 0.0
        state = self._kf.predict()
        return float(state[0, 0]), float(state[1, 0])

    def update(self, x: float, y: float, *, visibility: float = 1.0) -> tuple[float, float]:
        vis = max(float(visibility), _MIN_VISIBILITY)
        r_scale = 1.0 / vis
        self._kf.measurementNoiseCov = (
            np.eye(2, dtype=np.float32) * self._measurement_noise_base * r_scale
        )
        meas = np.array([[x], [y]], dtype=np.float32)
        if not self.initialized:
            self._kf.statePost = np.array([[x], [y], [0.0], [0.0]], dtype=np.float32)
            self.initialized = True
            return x, y
        self._kf.predict()
        corrected = self._kf.correct(meas)
        return float(corrected[0, 0]), float(corrected[1, 0])

    def reset(self) -> None:
        self.initialized = False
        self._kf.statePost = np.zeros((4, 1), dtype=np.float32)
        self._kf.errorCovPost = np.eye(4, dtype=np.float32)


class PoseKalmanBank:
    """Bank of 33 joint filters with crop-aware coordinate conversion."""

    def __init__(
        self,
        *,
        noise: KalmanNoiseConfig | None = None,
        crop_iou_reset_threshold: float = _CROP_IOU_RESET_THRESHOLD,
    ) -> None:
        self._noise = noise or KalmanNoiseConfig()
        self._crop_iou_reset_threshold = crop_iou_reset_threshold
        self._joints = [JointKalman2D(noise=self._noise) for _ in range(NUM_BODY_LANDMARKS)]
        self._prev_crop_xyxy: tuple[int, int, int, int] | None = None

    def reset(self) -> None:
        for joint in self._joints:
            joint.reset()
        self._prev_crop_xyxy = None

    def has_state(self) -> bool:
        return any(j.initialized for j in self._joints)

    def _note_crop(self, crop_xyxy: tuple[int, int, int, int]) -> None:
        if self._prev_crop_xyxy is None:
            self._prev_crop_xyxy = crop_xyxy
            return
        if _crop_iou(self._prev_crop_xyxy, crop_xyxy) < self._crop_iou_reset_threshold:
            self.reset()
        self._prev_crop_xyxy = crop_xyxy

    def predict_all(self) -> list[tuple[float, float]]:
        return [j.predict() for j in self._joints]

    def update_from_landmarks(
        self,
        landmarks: list[LandmarkPoint],
        crop_xyxy: tuple[int, int, int, int],
        *,
        vis_threshold: float,
    ) -> list[tuple[float, float]]:
        self._note_crop(crop_xyxy)
        out: list[tuple[float, float]] = []
        for i, lm in enumerate(landmarks[:NUM_BODY_LANDMARKS]):
            fx, fy = _landmark_to_frame_px(lm, crop_xyxy)
            joint = self._joints[i]
            if lm.visibility >= vis_threshold:
                px, py = joint.update(fx, fy, visibility=lm.visibility)
            else:
                px, py = joint.predict() if joint.initialized else (fx, fy)
            out.append((px, py))
        return out

    def apply_to_landmarks(
        self,
        raw: list[LandmarkPoint],
        crop_xyxy: tuple[int, int, int, int],
        *,
        vis_threshold: float,
    ) -> list[LandmarkPoint]:
        filtered_px = self.update_from_landmarks(
            raw, crop_xyxy, vis_threshold=vis_threshold
        )
        out: list[LandmarkPoint] = []
        for lm, (fx, fy) in zip(raw[:NUM_BODY_LANDMARKS], filtered_px, strict=False):
            nx, ny = _frame_px_to_landmark_xy(fx, fy, crop_xyxy)
            out.append(
                LandmarkPoint(
                    x=nx,
                    y=ny,
                    z=lm.z,
                    visibility=lm.visibility,
                    presence=lm.presence,
                )
            )
        while len(out) < len(raw):
            out.append(raw[len(out)])
        return out

    def predict_landmarks(
        self, crop_xyxy: tuple[int, int, int, int]
    ) -> list[LandmarkPoint]:
        self._note_crop(crop_xyxy)
        out: list[LandmarkPoint] = []
        for joint in self._joints:
            fx, fy = joint.predict()
            nx, ny = _frame_px_to_landmark_xy(fx, fy, crop_xyxy)
            vis = 0.0 if not joint.initialized else 0.0
            out.append(
                LandmarkPoint(x=nx, y=ny, z=0.0, visibility=vis, presence=vis)
            )
        return out


__all__ = [
    "KalmanNoiseConfig",
    "JointKalman2D",
    "PoseKalmanBank",
    "NUM_BODY_LANDMARKS",
]
