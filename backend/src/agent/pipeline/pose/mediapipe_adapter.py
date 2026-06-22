"""MediaPipe pose adapter."""

from __future__ import annotations

import os

import numpy as np

from agent.domain.models import PoseResult
from agent.pipeline.preprocessor import encode_frame_b64
from estimator.mediapipe import MediapipeEstimator
from models.exercise import ExerciseType


class MediapipePoseAdapter:
    def __init__(self, *, model_path: str | None = None) -> None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = model_path or os.path.join(root, "pose_models", "pose_landmarker_full.task")
        self._estimator = MediapipeEstimator(model_path=path)

    def estimate(self, frame: np.ndarray) -> PoseResult | None:
        result = self._estimator.detect_image_custom_params(
            frame, ExerciseType.SQUAT, height=frame.shape[0], width=frame.shape[1]
        )
        if result is None:
            return None
        annotated_b64 = None
        if result.annotated_image is not None:
            annotated_b64 = encode_frame_b64(result.annotated_image)
        kips = {}
        if result.key_interest_points_2d:
            kips = {k: v.model_dump() for k, v in result.key_interest_points_2d.items()}
        return PoseResult(landmarks=kips, confidence=0.9, annotated_b64=annotated_b64)
