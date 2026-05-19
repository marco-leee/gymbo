"""Draw segmentation tint, skeleton, and bbox on a frame (visualization-only)."""

from __future__ import annotations

import cv2
import numpy as np
import torch
from ultralytics.utils.plotting import Annotator

from pipeline.from_record import decode_mask_u8_from_segmentation
from pipeline.schemas import FramePerceptionRecord
from pipeline.yolo_compat import normalized_body33_to_coco17_frame_pixels


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
