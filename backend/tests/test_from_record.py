"""``record_to_frame_state`` / mask decode — no Ultralytics."""

from __future__ import annotations

import base64

import numpy as np

from pipeline.enums import (
    CoordinateSpace,
    FramePerceptionStatus,
    LandmarkLayout,
    MaskPayloadFormat,
)
from pipeline.from_record import decode_mask_u8_from_segmentation, record_to_frame_state
from pipeline.schemas import (
    CropPayload,
    FramePerceptionRecord,
    FrameSize,
    LandmarkPoint,
    MaskArtifact,
    ModelRef,
    ObjectDetectionPass,
    PoseEstimationPass,
    PoseSubject,
    PipelineProvenance,
    PrimarySubjectRef,
    SegmentationAlignment,
    SegmentationPass,
)


def test_decode_segmentation_roundtrip() -> None:
    h, w = 2, 3
    arr = np.arange(6, dtype=np.uint8).reshape((h, w))
    raw_b64 = base64.standard_b64encode(arr.tobytes()).decode("ascii")
    seg = SegmentationPass(
        model=ModelRef(name="s.pt", task="segment"),
        mask_primary=MaskArtifact(
            width=w,
            height=h,
            format=MaskPayloadFormat.UINT8_ROW_MAJOR_BASE64,
            data_base64=raw_b64,
        ),
        alignment=SegmentationAlignment(crop_xyxy_frame_px=(0, 0, w, h)),
    )
    out = decode_mask_u8_from_segmentation(seg)
    np.testing.assert_array_equal(out, arr)


def test_record_to_frame_state_ok_builds_legacy() -> None:
    landmarks = [
        LandmarkPoint(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
        for _ in range(33)
    ]
    cw, ch = 10, 20
    crop_bgr = np.zeros((ch, cw, 3), dtype=np.uint8)
    crop_b64 = base64.standard_b64encode(crop_bgr.tobytes()).decode("ascii")
    mask_u8 = np.ones((ch, cw), dtype=np.uint8) * 255
    mask_b64 = base64.standard_b64encode(mask_u8.tobytes()).decode("ascii")

    rec = FramePerceptionRecord(
        idx=2,
        timestamp=4.56,
        frame=FrameSize(width=100, height=200),
        status=FramePerceptionStatus.OK,
        object_detection=ObjectDetectionPass(
            model=ModelRef(name="d.pt", task="detect"),
            frame=FrameSize(width=100, height=200),
            detections=[],
            primary_subject=PrimarySubjectRef(detection_instance_id=None),
            crop_from_primary_px=(5, 5, 15, 25),
        ),
        pose_estimation=PoseEstimationPass(
            model=ModelRef(name="p.pt", task="pose"),
            coordinate_space=CoordinateSpace.NORMALIZED_CROP_XY,
            landmark_layout=LandmarkLayout.BODY_33,
            frame_count=2,
            subjects=[PoseSubject(landmarks=landmarks)],
        ),
        segmentation=SegmentationPass(
            model=ModelRef(name="s.pt", task="segment"),
            mask_primary=MaskArtifact(
                width=cw,
                height=ch,
                format=MaskPayloadFormat.UINT8_ROW_MAJOR_BASE64,
                data_base64=mask_b64,
            ),
            crop=CropPayload(bgr_raw_base64=crop_b64, channels=3),
            alignment=SegmentationAlignment(crop_xyxy_frame_px=(5, 5, 15, 25)),
        ),
        provenance=PipelineProvenance(conf_threshold=0.5),
    )
    frame_bgr = np.zeros((200, 100, 3), dtype=np.uint8)
    st = record_to_frame_state(rec, frame_bgr)

    assert st.overall_result is not None
    assert st.overall_result.idx == 2
    assert st.overall_result.pose_estimation_result["annotated_image_png_base64"] is None
    assert st.overall_result.pose_estimation_result["pose_landmarks"][0][0]["x"] == 0.5
    assert st.crop_xyxy == (5, 5, 15, 25)
    assert st.mask_u8_crop.shape == (ch, cw)
    assert st.cropped_frame is not None and st.cropped_frame.shape == (ch, cw, 3)
    assert st.perception_record is rec
