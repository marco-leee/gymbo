"""Typed JSON-oriented schemas for OD → pose → seg perception passes."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from pipeline.enums import (
    CoordinateSpace,
    FramePerceptionStatus,
    LandmarkLayout,
    MaskPayloadFormat,
    PerceptionPassId,
)


class ModelRef(BaseModel):
    """Checkpoint / task identification for one pass."""

    name: str = Field(description="Checkpoint filename or reproducible artifact id.")
    task: str = Field(description="Ultralytics task, e.g. detect | pose | segment.")


class FrameSize(BaseModel):
    width: Annotated[int, Field(ge=1)]
    height: Annotated[int, Field(ge=1)]


class BBoxXYXYPixels(BaseModel):
    """Absolute box in pixels, inclusive-exclusive semantics match OpenCV slicing."""

    x1: float
    y1: float
    x2: float
    y2: float


class DetectionInstance(BaseModel):
    instance_id: int = Field(ge=0)
    class_id: int
    class_name: str
    confidence: Annotated[float, Field(ge=0.0)]
    bbox_xyxy_px: tuple[float, float, float, float]


class PrimarySubjectRef(BaseModel):
    """Which detection was chosen as the single subject for crop-based passes."""

    detection_instance_id: int | None


class ObjectDetectionPass(BaseModel):
    pass_id: PerceptionPassId = PerceptionPassId.OBJECT_DETECTION
    model: ModelRef
    frame: FrameSize
    detections: list[DetectionInstance] = Field(default_factory=list)
    primary_subject: PrimarySubjectRef | None = None
    crop_from_primary_px: tuple[int, int, int, int] | None = None


class LandmarkPoint(BaseModel):
    x: float
    y: float
    z: float = 0.0
    visibility: float = 0.0
    presence: float = 0.0


class PoseSubject(BaseModel):
    track_or_instance_id: int | None = None
    landmarks: Annotated[list[LandmarkPoint], Field(min_length=33, max_length=33)]


class PoseEstimationPass(BaseModel):
    pass_id: PerceptionPassId = PerceptionPassId.POSE_ESTIMATION
    model: ModelRef
    coordinate_space: CoordinateSpace = CoordinateSpace.NORMALIZED_CROP_XY
    landmark_layout: LandmarkLayout = LandmarkLayout.BODY_33
    frame_count: int = Field(ge=0)
    subjects: list[PoseSubject] = Field(default_factory=list)
    annotated_crop_png_base64: str | None = None


class CropPayload(BaseModel):
    """BGR crop bytes encoding (matches historical segmentation blobs)."""

    bgr_raw_base64: str
    channels: Annotated[int, Field(ge=1, le=4)]


class SegmentationAlignment(BaseModel):
    crop_xyxy_frame_px: tuple[int, int, int, int]


class MaskArtifact(BaseModel):
    width: Annotated[int, Field(ge=1)]
    height: Annotated[int, Field(ge=1)]
    format: MaskPayloadFormat
    data_base64: str


class SegmentationPass(BaseModel):
    pass_id: PerceptionPassId = PerceptionPassId.SEGMENTATION
    model: ModelRef
    mask_primary: MaskArtifact
    mask_png_preview_base64: str | None = Field(
        default=None,
        description="PNG encoding of same mask for quick preview (may be omitted).",
    )
    crop: CropPayload | None = None
    alignment: SegmentationAlignment


class PipelineProvenance(BaseModel):
    conf_threshold: Annotated[float, Field(ge=0.0)]
    yolo_detect_weights: str | None = None
    yolo_pose_weights: str | None = None
    yolo_seg_weights: str | None = None


class FramePerceptionRecord(BaseModel):
    idx: Annotated[int, Field(ge=0)]
    timestamp: float
    frame: FrameSize
    status: FramePerceptionStatus
    object_detection: ObjectDetectionPass | None = None
    pose_estimation: PoseEstimationPass | None = None
    segmentation: SegmentationPass | None = None
    provenance: PipelineProvenance | None = None


class OverallPerceptionBatch(BaseModel):
    """Aggregate export (mirrors OverallResults metadata shape, distinct type)."""

    results: list[FramePerceptionRecord]
    camera_view: str | None = None
    exercise_type: str | None = None
    video_width: int | None = None
    video_height: int | None = None
    fps: int | None = None
