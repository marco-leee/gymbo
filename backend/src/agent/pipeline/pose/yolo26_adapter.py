"""YOLO26 pose adapter (detect primary person, pose on crop)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

from agent.domain.models import PoseResult
from agent.pipeline.preprocessor import encode_frame_b64
from pipeline.yolo_compat import (
    best_person_box_index,
    clamp_crop_xyxy,
    normalized_body33_to_coco17_frame_pixels,
    person_class_id,
    yolo_keypoints_to_body33,
)

_SRC_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_SIZE = "n"


def _yolo26_weight_paths(
    pose_models_root: Path, size: str = DEFAULT_MODEL_SIZE
) -> tuple[Path, Path]:
    return (
        pose_models_root / f"yolo26{size}.pt",
        pose_models_root / f"yolo26{size}-pose.pt",
    )


def _detection_names(det: Any) -> dict[Any, Any]:
    names = getattr(det, "names", {})
    return names if isinstance(names, dict) else dict(names)


def _mean_visibility(group_dicts: list[dict[str, float]]) -> float:
    vis = [d["visibility"] for d in group_dicts if d["visibility"] > 0]
    return float(sum(vis) / len(vis)) if vis else 0.0


def _annotate_pose(
    frame_bgr: np.ndarray,
    group_dicts: list[dict[str, float]],
    crop_xyxy: tuple[int, int, int, int],
) -> np.ndarray:
    vis = frame_bgr.copy()
    trips = [(d["x"], d["y"], d["visibility"]) for d in group_dicts]
    coco17 = normalized_body33_to_coco17_frame_pixels(trips, crop_xyxy)
    kpt = torch.from_numpy(coco17).float()
    annotator = Annotator(vis, line_width=2)
    annotator.kpts(
        kpt,
        shape=vis.shape[:2],
        radius=4,
        kpt_line=True,
        conf_thres=0.25,
    )
    vis = annotator.result()
    x1, y1, x2, y2 = crop_xyxy
    cv2.rectangle(vis, (x1, y1), (x2, y2), (255, 192, 0), 2)
    return vis


class Yolo26PoseAdapter:
    """PosePort implementation using YOLO26 detect + pose checkpoints."""

    def __init__(
        self,
        *,
        model_size: str = DEFAULT_MODEL_SIZE,
        detect_weights: str | Path | None = None,
        pose_weights: str | Path | None = None,
        conf_threshold: float = 0.25,
        pose_models_root: str | Path | None = None,
    ) -> None:
        root = Path(pose_models_root) if pose_models_root else _SRC_ROOT / "pose_models"
        default_detect, default_pose = _yolo26_weight_paths(root, model_size)
        detect_path = Path(detect_weights) if detect_weights else default_detect
        pose_path = Path(pose_weights) if pose_weights else default_pose
        self._conf_threshold = conf_threshold
        self._object_detector = YOLO(str(detect_path))
        self._pose_model = YOLO(str(pose_path))

    def estimate(self, frame: np.ndarray) -> PoseResult | None:
        h, w = frame.shape[:2]
        det_results = self._object_detector(frame, verbose=False)
        det0 = det_results[0] if det_results else None
        if det0 is None or det0.boxes is None or len(det0.boxes) == 0:
            return None

        boxes = det0.boxes
        names_dict = _detection_names(det0)
        pcid = person_class_id(names_dict)
        frame_area = float(w * h)
        best_i = best_person_box_index(
            boxes, pcid, self._conf_threshold, frame_area
        )
        if best_i is None:
            return None

        x1, y1, x2, y2 = (int(v) for v in boxes.xyxy[best_i].tolist())
        crop_xyxy = clamp_crop_xyxy(x1, y1, x2, y2, w, h)
        if crop_xyxy is None:
            return None

        cx1, cy1, cx2, cy2 = crop_xyxy
        cropped = frame[cy1:cy2, cx1:cx2]
        if cropped.size == 0:
            return None

        ch, cw = cropped.shape[:2]
        pose_results = self._pose_model(cropped, verbose=False)
        if not pose_results:
            return None
        pr = pose_results[0]
        if pr.keypoints is None or pr.boxes is None or len(pr.boxes) == 0:
            return None

        crop_area = float(cw * ch)
        pi = best_person_box_index(
            pr.boxes, person_class_id(_detection_names(pr)), self._conf_threshold, crop_area
        )
        if pi is None:
            return None

        kall = pr.keypoints.data
        if kall is None or kall.shape[0] <= pi:
            return None

        group_dicts = yolo_keypoints_to_body33(kall[pi], cw, ch)
        landmarks = {str(i): group_dicts[i] for i in range(len(group_dicts))}
        confidence = max(float(boxes.conf[best_i]), _mean_visibility(group_dicts))
        annotated_b64 = encode_frame_b64(
            _annotate_pose(frame, group_dicts, crop_xyxy)
        )
        return PoseResult(
            landmarks=landmarks,
            confidence=confidence,
            annotated_b64=annotated_b64,
        )
