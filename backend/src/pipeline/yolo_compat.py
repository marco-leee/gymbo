"""Ultralytics / OpenCV helpers (standalone; does not import ``analysis_pipeline``)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from pipeline.constants import MIN_PERSON_IN_FRAME_RATIO

# COCO keypoint index -> fixed 33-body slot (YOLO COCO subset remapped).
_COCO_TO_BODY33_SLOT: dict[int, int] = {
    0: 0,
    3: 7,
    4: 8,
    5: 11,
    6: 12,
    7: 13,
    8: 14,
    9: 15,
    10: 16,
    11: 23,
    12: 24,
    13: 25,
    14: 26,
    15: 27,
    16: 28,
}


def person_class_id(names: dict[Any, Any]) -> int:
    return next((int(cid) for cid, name in names.items() if name == "person"), 0)


def clamp_crop_xyxy(
    x1: int, y1: int, x2: int, y2: int, w: int, h: int
) -> tuple[int, int, int, int] | None:
    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h))
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def best_person_box_index(
    boxes,
    person_cid: int,
    conf_threshold: float,
    frame_area: float,
) -> int | None:
    if boxes is None or len(boxes) == 0:
        return None
    best_i: int | None = None
    best_area = -1.0
    for i in range(len(boxes)):
        if int(boxes.cls[i]) != person_cid:
            continue
        if float(boxes.conf[i]) <= conf_threshold:
            continue
        x1f, y1f, x2f, y2f = boxes.xyxy[i].tolist()
        area = (x2f - x1f) * (y2f - y1f)
        ratio = area / frame_area
        if area > best_area and ratio >= MIN_PERSON_IN_FRAME_RATIO:
            best_area = area
            best_i = i
    return best_i




def empty_landmark() -> dict[str, float]:
    return {"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 0.0, "presence": 0.0}


def yolo_keypoints_to_body33(
    keypoints_xyconf: Any, crop_w: int, crop_h: int
) -> list[dict[str, float]]:
    """Map YOLO COCO keypoints (pixel xy in crop, conf) to 33 slots, crop-normalized."""
    if hasattr(keypoints_xyconf, "cpu"):
        arr = keypoints_xyconf.detach().cpu().float().numpy()
    else:
        arr = np.asarray(keypoints_xyconf, dtype=np.float64)
    n_kpt = arr.shape[0]
    group = [empty_landmark() for _ in range(33)]
    cw = float(max(crop_w, 1))
    ch = float(max(crop_h, 1))

    def take(i_coco: int) -> tuple[float, float, float] | None:
        if i_coco < 0 or i_coco >= n_kpt:
            return None
        row = arr[i_coco]
        kx, ky = float(row[0]), float(row[1])
        kc = float(row[2]) if row.shape[0] > 2 else 1.0
        return kx, ky, kc

    for coco_i, body_slot in _COCO_TO_BODY33_SLOT.items():
        got = take(coco_i)
        if got is None:
            continue
        kx, ky, kconf = got
        group[body_slot] = {
            "x": kx / cw,
            "y": ky / ch,
            "z": 0.0,
            "visibility": kconf,
            "presence": kconf,
        }
    return group


def normalized_body33_to_coco17_frame_pixels(
    landmarks33: Sequence[tuple[float, float, float]],
    crop_xyxy: tuple[int, int, int, int],
) -> np.ndarray:
    """Undo partial COCO remap: 33 normalized crop landmarks -> COCO-17 xy+conf in full-frame pixels."""
    x1, y1, x2, y2 = crop_xyxy
    cw = float(max(x2 - x1, 1))
    ch = float(max(y2 - y1, 1))
    out = np.zeros((17, 3), dtype=np.float32)
    for coco_i in range(17):
        slot = _COCO_TO_BODY33_SLOT.get(coco_i)
        if slot is None or slot >= len(landmarks33):
            continue
        nx, ny, conf = landmarks33[slot]
        out[coco_i, 0] = x1 + float(nx) * cw
        out[coco_i, 1] = y1 + float(ny) * ch
        out[coco_i, 2] = float(conf)
    return out
