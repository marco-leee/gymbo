"""Draw segmentation tint, skeleton, bbox, and KIP angle arcs on a frame."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
import torch
from ultralytics.utils.plotting import Annotator

from pipeline.from_record import decode_mask_u8_from_segmentation
from pipeline.kip_colors import KIP_COLORS_BGR, KIP_LABELS
from pipeline.schemas import FramePerceptionRecord
from pipeline.yolo_compat import normalized_body33_to_coco17_frame_pixels


def draw_kip_angle(
    image: np.ndarray,
    *,
    center: tuple[int, int],
    angle: int | float,
    rotation_angle: int | float,
    color_bgr: tuple[int, int, int],
    label: str | None = None,
) -> None:
    """Draw an angle arc and degree label at the joint vertex."""
    cx, cy = center
    cv2.ellipse(
        image,
        center,
        (30, 30),
        float(rotation_angle),
        0,
        float(angle),
        color_bgr,
        2,
    )
    cv2.putText(
        image,
        f"{float(angle):.0f}°",
        (cx - 40, cy + 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color_bgr,
        2,
        cv2.LINE_AA,
    )
    if label:
        cv2.putText(
            image,
            label,
            (cx - 40, cy + 44),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color_bgr,
            1,
            cv2.LINE_AA,
        )


def _kip_vertex_center(
    idx_to_coordinates: dict[Any, Any],
) -> tuple[int, int] | None:
    coords = list(idx_to_coordinates.values())
    if len(coords) != 3:
        return None
    _, center, _ = coords
    if not isinstance(center, (list, tuple)) or len(center) < 2:
        return None
    return int(center[0]), int(center[1])


def render_kip_angles(
    frame_bgr: np.ndarray,
    kips: dict[str, dict[str, Any]] | None,
    crop_xy: tuple[int, int, int, int] | None,
) -> np.ndarray:
    """Draw KIP angle arcs using the canonical per-KIP palette."""
    if not kips:
        return frame_bgr

    vis = frame_bgr
    offset_x = int(crop_xy[0]) if crop_xy is not None else 0
    offset_y = int(crop_xy[1]) if crop_xy is not None else 0

    for kip_name, kip_data in kips.items():
        color = KIP_COLORS_BGR.get(kip_name)
        if color is None or not isinstance(kip_data, dict):
            continue

        idx_map = kip_data.get("idx_to_coordinates")
        if not isinstance(idx_map, dict):
            continue

        center = _kip_vertex_center(idx_map)
        if center is None:
            continue

        angle = kip_data.get("angle")
        rotation_angle = kip_data.get("rotation_angle")
        if angle is None or rotation_angle is None:
            continue

        frame_center = (center[0] + offset_x, center[1] + offset_y)
        draw_kip_angle(
            vis,
            center=frame_center,
            angle=angle,
            rotation_angle=rotation_angle,
            color_bgr=color,
            label=KIP_LABELS.get(kip_name),
        )

    return vis


def render_overlays(frame_bgr: np.ndarray, rec: FramePerceptionRecord) -> np.ndarray:
    """Mask tint → COCO skeleton (from stored body-33 landmarks) → person bbox."""
    vis = frame_bgr.copy()
    hh, ww = frame_bgr.shape[:2]

    crop_xy = (
        rec.object_detection.crop_from_primary_px
        if rec.object_detection is not None
        else None
    )

    if rec.segmentation is not None:
        mask_u8 = decode_mask_u8_from_segmentation(rec.segmentation)
        seg_crop = rec.segmentation.alignment.crop_xyxy_frame_px
        x1, y1, x2, y2 = seg_crop
        green = np.zeros_like(vis)
        green[y1:y2, x1:x2, 1] = mask_u8
        region = np.zeros((hh, ww), dtype=bool)
        region[y1:y2, x1:x2] = mask_u8 > 0
        vis_f = vis.astype(np.float32)
        g_f = green.astype(np.float32)
        vis = np.where(
            region[:, :, None],
            (vis_f * 0.55 + g_f * 0.45).astype(np.uint8),
            vis,
        )

    if (
        rec.pose_estimation is not None
        and rec.pose_estimation.subjects
        and crop_xy is not None
    ):
        lm = rec.pose_estimation.subjects[0].landmarks
        trips = [(pt.x, pt.y, pt.visibility) for pt in lm]
        coco17 = normalized_body33_to_coco17_frame_pixels(trips, crop_xy)
        # Ultralytics Annotator expects shape [17, 3] (x, y, conf), not batched [1, 17, 3].
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

    if crop_xy is not None:
        bx1, by1, bx2, by2 = crop_xy
        cv2.rectangle(vis, (bx1, by1), (bx2, by2), (255, 192, 0), 2)

    return vis
