"""Enums for perception layer output schemas."""

from __future__ import annotations

from enum import Enum


class PerceptionPassId(str, Enum):
    OBJECT_DETECTION = "object_detection"
    POSE_ESTIMATION = "pose_estimation"
    SEGMENTATION = "segmentation"


class CoordinateSpace(str, Enum):
    """Where landmark / mask coordinates live."""

    FULL_FRAME_PIXEL_XY = "full_frame_pixel_xy"
    NORMALIZED_FULL_FRAME_XY = "normalized_full_frame_xy"
    CROP_PIXEL_XY = "crop_pixel_xy"
    NORMALIZED_CROP_XY = "normalized_crop_xy"


class LandmarkLayout(str, Enum):
    """Fixed 33-slot layout: YOLO COCO keypoints remapped into stable indices."""

    BODY_33 = "body_33"


class FramePerceptionStatus(str, Enum):
    OK = "ok"
    NO_DETECTIONS = "no_detections"
    NO_PRIMARY_PERSON = "no_primary_person"
    POSE_FAILED = "pose_failed"
    SEGMENTATION_FAILED = "segmentation_failed"


class MaskPayloadFormat(str, Enum):
    """How mask bytes are encoded in ``SegmentationPass.mask_payload``."""

    UINT8_ROW_MAJOR_BASE64 = "uint8_row_major_base64"
    PNG_BASE64 = "png_base64"
