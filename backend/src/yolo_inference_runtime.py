"""Shared Ultralytics YOLO weights + single-frame inference."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np
from ultralytics import YOLO

from analysis_pipeline import infer_overall_result_from_bgr
from models.exercise import ExerciseType
from models.overall_results import OverallResult
from utils.video import CameraView

logger = logging.getLogger(__name__)

_SRC_DIR = Path(__file__).resolve().parent


def _resolve_weights(path_str: str) -> str:
    p = Path(path_str)
    if p.is_file():
        return str(p.resolve())
    alt = _SRC_DIR / path_str
    if alt.is_file():
        return str(alt.resolve())
    return str(p.resolve())


class YoloInferenceRuntime:
    def __init__(
        self,
        detect_path: str,
        pose_path: str,
        seg_path: str,
        *,
        conf_threshold: float,
    ) -> None:
        self.conf_threshold = conf_threshold
        logger.info("Loading YOLO detect: %s", detect_path)
        self.object_detector = YOLO(detect_path)
        logger.info("Loading YOLO pose: %s", pose_path)
        self.pose_model = YOLO(pose_path)
        logger.info("Loading YOLO seg: %s", seg_path)
        self.segmenter = YOLO(seg_path)

    @classmethod
    def from_env(cls) -> YoloInferenceRuntime:
        detect = os.environ.get(
            "YOLO_DETECT_WEIGHTS", str(_SRC_DIR / "pose_models" / "yolo26l.pt")
        )
        pose = os.environ.get(
            "YOLO_POSE_WEIGHTS", str(_SRC_DIR / "pose_models" / "yolo26l-pose.pt")
        )
        seg = os.environ.get(
            "YOLO_SEG_WEIGHTS", str(_SRC_DIR / "pose_models" / "yolo26l-seg.pt")
        )
        conf = float(os.environ.get("YOLO_CONF", "0.8"))
        return cls(
            _resolve_weights(detect),
            _resolve_weights(pose),
            _resolve_weights(seg),
            conf_threshold=conf,
        )

    def infer(
        self,
        frame_bgr: np.ndarray,
        *,
        idx: int,
        timestamp: float,
        exercise_type: ExerciseType = ExerciseType.SQUAT,
        camera_view: CameraView = CameraView.RIGHT,
    ) -> OverallResult | None:
        return infer_overall_result_from_bgr(
            frame_bgr,
            idx=idx,
            timestamp=timestamp,
            conf_threshold=self.conf_threshold,
            object_detector=self.object_detector,
            segmenter=self.segmenter,
            pose_model=self.pose_model,
            exercise_type=exercise_type,
            camera_view=camera_view,
        )
