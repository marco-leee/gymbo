"""Map ``FramePerceptionRecord`` to legacy ``OverallResult`` + ``FramePerceptionState``."""

from __future__ import annotations

import base64

import numpy as np

from models.overall_results import OverallResult
from pipeline.enums import FramePerceptionStatus
from pipeline.frame_state import FramePerceptionState
from pipeline.schemas import FramePerceptionRecord, SegmentationPass


def decode_mask_u8_from_segmentation(seg: SegmentationPass) -> np.ndarray:
    raw = base64.standard_b64decode(seg.mask_primary.data_base64)
    h, w = seg.mask_primary.height, seg.mask_primary.width
    return np.frombuffer(raw, dtype=np.uint8).reshape((h, w)).copy()


def record_to_frame_state(
    rec: FramePerceptionRecord,
    frame_bgr: np.ndarray,
) -> FramePerceptionState:
    """Build viz arrays and optional ``OverallResult`` (legacy JSON) from a perception record."""
    crop_xy: tuple[int, int, int, int] | None = None
    if rec.object_detection is not None:
        crop_xy = rec.object_detection.crop_from_primary_px

    cropped: np.ndarray | None = None
    if crop_xy is not None:
        x1, y1, x2, y2 = crop_xy
        cropped = frame_bgr[y1:y2, x1:x2].copy()

    mask_u8: np.ndarray | None = None
    if rec.segmentation is not None:
        mask_u8 = decode_mask_u8_from_segmentation(rec.segmentation)

    overall: OverallResult | None = None
    if (
        rec.status == FramePerceptionStatus.OK
        and rec.pose_estimation is not None
        and rec.segmentation is not None
    ):
        pose = rec.pose_estimation
        seg = rec.segmentation
        subj = pose.subjects[0]
        group = [lm.model_dump() for lm in subj.landmarks]
        pose_payload = {
            "frame_count": pose.frame_count,
            "annotated_image_png_base64": None,
            "segmentation_mask": None,
            "pose_landmarks": [group],
            "pose_world_landmarks": None,
        }
        seg_payload: dict = {
            "mask_raw_base64": seg.mask_primary.data_base64,
            "mask_width": seg.mask_primary.width,
            "mask_height": seg.mask_primary.height,
            "frame_crop_xyxy": list(seg.alignment.crop_xyxy_frame_px),
        }
        if seg.crop is not None:
            seg_payload["crop_bgr_raw_base64"] = seg.crop.bgr_raw_base64
            seg_payload["crop_channels"] = seg.crop.channels
        if seg.mask_png_preview_base64 is not None:
            seg_payload["mask_png_base64"] = seg.mask_png_preview_base64
        overall = OverallResult(
            idx=rec.idx,
            timestamp=rec.timestamp,
            pose_estimation_result=pose_payload,
            segmentation_result=seg_payload,
        )

    return FramePerceptionState(
        overall,
        crop_xy,
        mask_u8,
        cropped,
        rec,
    )
