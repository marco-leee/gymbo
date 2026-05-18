"""Schema construction / JSON serialization (no ML stack)."""

from __future__ import annotations

from pipeline.enums import (
    CoordinateSpace,
    FramePerceptionStatus,
    LandmarkLayout,
    MaskPayloadFormat,
    PerceptionPassId,
)
from pipeline.schemas import (
    CropPayload,
    DetectionInstance,
    FramePerceptionRecord,
    FrameSize,
    LandmarkPoint,
    MaskArtifact,
    ModelRef,
    ObjectDetectionPass,
    OverallPerceptionBatch,
    PoseEstimationPass,
    PoseSubject,
    PipelineProvenance,
    PrimarySubjectRef,
    SegmentationAlignment,
    SegmentationPass,
)


def test_full_record_roundtrip_json() -> None:
    landmarks = [
        LandmarkPoint(x=0.01 * i, y=0.02 * i, z=0.0, visibility=1.0, presence=1.0)
        for i in range(33)
    ]
    rec = FramePerceptionRecord(
        idx=0,
        timestamp=1.23,
        frame=FrameSize(width=1920, height=1080),
        status=FramePerceptionStatus.OK,
        object_detection=ObjectDetectionPass(
            model=ModelRef(name="yolo26n.pt", task="detect"),
            frame=FrameSize(width=1920, height=1080),
            detections=[
                DetectionInstance(
                    instance_id=0,
                    class_id=0,
                    class_name="person",
                    confidence=0.9,
                    bbox_xyxy_px=(10.0, 20.0, 100.0, 200.0),
                ),
            ],
            primary_subject=PrimarySubjectRef(detection_instance_id=0),
            crop_from_primary_px=(10, 20, 100, 200),
        ),
        pose_estimation=PoseEstimationPass(
            model=ModelRef(name="yolo26n-pose.pt", task="pose"),
            coordinate_space=CoordinateSpace.NORMALIZED_CROP_XY,
            landmark_layout=LandmarkLayout.BODY_33,
            frame_count=0,
            subjects=[PoseSubject(landmarks=landmarks)],
        ),
        segmentation=SegmentationPass(
            model=ModelRef(name="yolo26n-seg.pt", task="segment"),
            mask_primary=MaskArtifact(
                width=90,
                height=180,
                format=MaskPayloadFormat.UINT8_ROW_MAJOR_BASE64,
                data_base64="AQID",
            ),
            mask_png_preview_base64=None,
            crop=CropPayload(bgr_raw_base64="BAUG", channels=3),
            alignment=SegmentationAlignment(crop_xyxy_frame_px=(10, 20, 100, 200)),
        ),
        provenance=PipelineProvenance(conf_threshold=0.5),
    )

    dumped = rec.model_dump_json()
    restored = FramePerceptionRecord.model_validate_json(dumped)

    assert restored.status == FramePerceptionStatus.OK
    assert restored.object_detection is not None
    assert restored.object_detection.pass_id == PerceptionPassId.OBJECT_DETECTION
    assert restored.pose_estimation is not None
    assert restored.pose_estimation.subjects[0].landmarks[0].visibility == 1.0
    batch = OverallPerceptionBatch(results=[restored], fps=30)
    _ = batch.model_dump_json()


def test_minimal_partial_record_serializes() -> None:
    r = FramePerceptionRecord(
        idx=10,
        timestamp=2.5,
        frame=FrameSize(width=640, height=480),
        status=FramePerceptionStatus.NO_DETECTIONS,
    )
    FramePerceptionRecord.model_validate_json(r.model_dump_json())
