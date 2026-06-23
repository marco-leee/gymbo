"""Standalone single-frame OD → pose → seg runner producing ``FramePerceptionRecord``."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

from pipeline.enums import (
    CoordinateSpace,
    FramePerceptionStatus,
    LandmarkLayout,
    MaskPayloadFormat,
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
    PoseEstimationPass,
    PoseSubject,
    PipelineProvenance,
    PrimarySubjectRef,
    SegmentationAlignment,
    SegmentationPass,
)
from pipeline.bbox_kalman import BBoxKalmanFilter
from pipeline.pose_kalman import PoseKalmanBank
from pipeline.yolo_compat import (
    best_person_box_index,
    clamp_crop_xyxy,
    person_class_id,
    yolo_keypoints_to_body33,
)


def _detect_model_name(weights_path: str) -> str:
    return weights_path.replace("\\", "/").rsplit("/", 1)[-1]


@dataclass(frozen=True)
class PerceptionRunConfig:
    conf_threshold: float
    yolo_detect_weights: str
    yolo_pose_weights: str
    yolo_seg_weights: str
    kalman_enabled: bool = True
    kalman_vis_threshold: float | None = None


def _detection_names(det: Any) -> dict[Any, Any]:
    n = getattr(det, "names", {})
    return n if isinstance(n, dict) else dict(n)


def _build_detection_pass(
    det: Any, config: PerceptionRunConfig, w: int, h: int
) -> tuple[ObjectDetectionPass | None, int | None]:
    if det.boxes is None or len(det.boxes) == 0:
        return None, None
    boxes = det.boxes
    names_dict = _detection_names(det)
    detection_list: list[DetectionInstance] = []
    for i in range(len(boxes)):
        cid = int(boxes.cls[i])
        cname = str(names_dict.get(cid, cid))
        detection_list.append(
            DetectionInstance(
                instance_id=i,
                class_id=cid,
                class_name=cname,
                confidence=float(boxes.conf[i]),
                bbox_xyxy_px=(
                    float(boxes.xyxy[i][0]),
                    float(boxes.xyxy[i][1]),
                    float(boxes.xyxy[i][2]),
                    float(boxes.xyxy[i][3]),
                ),
            )
        )
    pcid = person_class_id(names_dict)
    frame_area = float(w * h)
    best_i = best_person_box_index(boxes, pcid, config.conf_threshold, frame_area)
    crop: tuple[int, int, int, int] | None = None
    primary_ref: PrimarySubjectRef | None = None
    best_used_i: int | None = None
    if best_i is not None:
        x1, y1, x2, y2 = (int(v) for v in boxes.xyxy[best_i].tolist())
        clipped = clamp_crop_xyxy(x1, y1, x2, y2, w, h)
        if clipped is not None:
            crop = clipped
            primary_ref = PrimarySubjectRef(detection_instance_id=best_i)
            best_used_i = best_i

    od = ObjectDetectionPass(
        model=ModelRef(
            name=_detect_model_name(config.yolo_detect_weights),
            task="detect",
        ),
        frame=FrameSize(width=w, height=h),
        detections=detection_list,
        primary_subject=primary_ref,
        crop_from_primary_px=crop,
    )
    return od, best_used_i


def _empty_detection_pass(
    config: PerceptionRunConfig, w: int, h: int
) -> ObjectDetectionPass:
    return ObjectDetectionPass(
        model=ModelRef(
            name=_detect_model_name(config.yolo_detect_weights),
            task="detect",
        ),
        frame=FrameSize(width=w, height=h),
        detections=[],
        primary_subject=None,
        crop_from_primary_px=None,
    )


def _resolve_primary_crop(
    det: Any | None,
    config: PerceptionRunConfig,
    w: int,
    h: int,
    bbox_kalman: BBoxKalmanFilter | None,
) -> tuple[ObjectDetectionPass | None, tuple[int, int, int, int] | None, int | None]:
    has_boxes = det is not None and det.boxes is not None and len(det.boxes) > 0
    if has_boxes:
        od_pass, best_i = _build_detection_pass(det, config, w, h)
        raw_crop = od_pass.crop_from_primary_px if od_pass is not None else None
        confidence = 1.0
        if (
            best_i is not None
            and od_pass is not None
            and best_i < len(od_pass.detections)
        ):
            confidence = od_pass.detections[best_i].confidence
    else:
        od_pass = _empty_detection_pass(config, w, h)
        best_i = None
        raw_crop = None
        confidence = 1.0

    crop: tuple[int, int, int, int] | None = None
    if raw_crop is not None:
        if config.kalman_enabled and bbox_kalman is not None:
            crop = bbox_kalman.apply(
                raw_crop, confidence=confidence, frame_w=w, frame_h=h
            )
        else:
            crop = raw_crop
    elif (
        config.kalman_enabled
        and bbox_kalman is not None
        and bbox_kalman.has_state()
    ):
        crop = bbox_kalman.predict_clamped(w, h)
        if od_pass is not None:
            od_pass = od_pass.model_copy(update={"primary_subject": None})

    if od_pass is not None and crop is not None:
        od_pass = od_pass.model_copy(update={"crop_from_primary_px": crop})

    return od_pass, crop, best_i


def _kalman_vis_threshold(config: PerceptionRunConfig) -> float:
    if config.kalman_vis_threshold is not None:
        return config.kalman_vis_threshold
    return max(config.conf_threshold, 0.5)


def _build_pose_pass(
    *,
    frame_count: int,
    pose_weights_path: str,
    landmarks: list[LandmarkPoint],
) -> PoseEstimationPass | None:
    if len(landmarks) != 33:
        return None
    return PoseEstimationPass(
        model=ModelRef(name=_detect_model_name(pose_weights_path), task="pose"),
        coordinate_space=CoordinateSpace.NORMALIZED_CROP_XY,
        landmark_layout=LandmarkLayout.BODY_33,
        frame_count=frame_count,
        subjects=[PoseSubject(track_or_instance_id=0, landmarks=landmarks)],
        annotated_crop_png_base64=None,
    )


def _pose_pass_from_crop(
    pose_model: YOLO,
    cropped_frame: np.ndarray,
    *,
    frame_count: int,
    conf_threshold: float,
    pose_weights_path: str,
    crop_xyxy_frame_px: tuple[int, int, int, int] | None = None,
    pose_kalman: PoseKalmanBank | None = None,
    config: PerceptionRunConfig | None = None,
) -> PoseEstimationPass | None:
    if cropped_frame.size == 0:
        return None
    ch, cw = cropped_frame.shape[:2]
    pr_list = pose_model(cropped_frame, verbose=False)
    if not pr_list:
        return None
    pr = pr_list[0]
    if pr.keypoints is None or pr.boxes is None or len(pr.boxes) == 0:
        return None
    pcid = person_class_id(_detection_names(pr))
    frame_area = float(cw * ch)
    pi = best_person_box_index(pr.boxes, pcid, conf_threshold, frame_area)
    if pi is None:
        return None
    kall = pr.keypoints.data
    if kall is None or kall.shape[0] <= pi:
        return None
    kp = kall[pi].clone()
    group_dicts = yolo_keypoints_to_body33(kp, cw, ch)

    landmarks = [
        LandmarkPoint(
            x=d["x"],
            y=d["y"],
            z=d["z"],
            visibility=d["visibility"],
            presence=d["presence"],
        )
        for d in group_dicts
    ]
    if (
        config is not None
        and config.kalman_enabled
        and pose_kalman is not None
        and crop_xyxy_frame_px is not None
    ):
        landmarks = pose_kalman.apply_to_landmarks(
            landmarks,
            crop_xyxy_frame_px,
            vis_threshold=_kalman_vis_threshold(config),
        )

    return _build_pose_pass(
        frame_count=frame_count,
        pose_weights_path=pose_weights_path,
        landmarks=landmarks,
    )


def _segmentation_pass_from_crop(
    cropped_frame: np.ndarray,
    seg_results: list[Any],
    *,
    crop_xyxy_frame_px: tuple[int, int, int, int],
    conf_threshold: float,
    seg_weights_path: str,
) -> SegmentationPass | None:
    if not seg_results:
        return None
    seg = seg_results[0]
    if seg.masks is None or len(seg.masks) == 0 or seg.boxes is None:
        return None
    seg_boxes = seg.boxes
    pcid = person_class_id(_detection_names(seg))
    seg_best_i: int | None = None
    seg_best_area = -1.0
    for i in range(len(seg_boxes)):
        if int(seg_boxes.cls[i]) != pcid:
            continue
        if float(seg_boxes.conf[i]) <= conf_threshold:
            continue
        sx1, sy1, sx2, sy2 = seg_boxes.xyxy[i].tolist()
        sarea = (sx2 - sx1) * (sy2 - sy1)
        if sarea > seg_best_area:
            seg_best_area = sarea
            seg_best_i = i
    if seg_best_i is None:
        return None
    mask = seg.masks.data[seg_best_i].float().cpu().numpy()
    ch, cw = cropped_frame.shape[:2]
    if mask.shape != (ch, cw):
        mask = cv2.resize(mask, (cw, ch), interpolation=cv2.INTER_LINEAR)
    mask_u8 = ((mask >= 0.5) * 255).astype(np.uint8)
    crop_contig = np.ascontiguousarray(cropped_frame)
    mask_raw_b64 = base64.standard_b64encode(mask_u8.tobytes()).decode("ascii")
    crop_raw_b64 = base64.standard_b64encode(crop_contig.tobytes()).decode("ascii")
    png_preview: str | None = None
    ok_png, buf = cv2.imencode(".png", mask_u8)
    if ok_png:
        png_preview = base64.standard_b64encode(buf.tobytes()).decode("ascii")

    mask_art = MaskArtifact(
        width=cw,
        height=ch,
        format=MaskPayloadFormat.UINT8_ROW_MAJOR_BASE64,
        data_base64=mask_raw_b64,
    )
    crop_payload = CropPayload(
        bgr_raw_base64=crop_raw_b64, channels=int(crop_contig.shape[2])
    )
    align = SegmentationAlignment(crop_xyxy_frame_px=crop_xyxy_frame_px)
    return SegmentationPass(
        model=ModelRef(name=_detect_model_name(seg_weights_path), task="segment"),
        mask_primary=mask_art,
        mask_png_preview_base64=png_preview,
        crop=crop_payload,
        alignment=align,
    )


def perceive_frame_pipeline(
    frame_bgr: np.ndarray,
    *,
    idx: int,
    timestamp: float,
    object_detector: YOLO,
    pose_model: YOLO,
    segmenter: YOLO,
    config: PerceptionRunConfig,
    pose_kalman: PoseKalmanBank | None = None,
    bbox_kalman: BBoxKalmanFilter | None = None,
) -> FramePerceptionRecord:
    h, w = frame_bgr.shape[:2]
    prov = PipelineProvenance(
        conf_threshold=config.conf_threshold,
        yolo_detect_weights=config.yolo_detect_weights,
        yolo_pose_weights=config.yolo_pose_weights,
        yolo_seg_weights=config.yolo_seg_weights,
    )
    det_results = object_detector(frame_bgr, verbose=False)
    det0 = det_results[0] if det_results else None

    od_pass, crop_xyxy, _best_i = _resolve_primary_crop(
        det0, config, w, h, bbox_kalman
    )
    if crop_xyxy is None:
        has_boxes = det0 is not None and det0.boxes is not None and len(det0.boxes) > 0
        return FramePerceptionRecord(
            idx=idx,
            timestamp=timestamp,
            frame=FrameSize(width=w, height=h),
            status=(
                FramePerceptionStatus.NO_PRIMARY_PERSON
                if has_boxes
                else FramePerceptionStatus.NO_DETECTIONS
            ),
            object_detection=od_pass,
            provenance=prov,
        )

    x1, y1, x2, y2 = crop_xyxy
    cropped_frame = frame_bgr[y1:y2, x1:x2]

    pose_pass = _pose_pass_from_crop(
        pose_model,
        cropped_frame,
        frame_count=idx,
        conf_threshold=config.conf_threshold,
        pose_weights_path=config.yolo_pose_weights,
        crop_xyxy_frame_px=crop_xyxy,
        pose_kalman=pose_kalman,
        config=config,
    )
    seg_list = segmenter(cropped_frame, verbose=False)

    if pose_pass is None:
        if (
            config.kalman_enabled
            and pose_kalman is not None
            and pose_kalman.has_state()
        ):
            predicted = pose_kalman.predict_landmarks(crop_xyxy)
            pose_pass = _build_pose_pass(
                frame_count=idx,
                pose_weights_path=config.yolo_pose_weights,
                landmarks=predicted,
            )
        if pose_pass is None:
            return FramePerceptionRecord(
                idx=idx,
                timestamp=timestamp,
                frame=FrameSize(width=w, height=h),
                status=FramePerceptionStatus.POSE_FAILED,
                object_detection=od_pass,
                provenance=prov,
            )

    seg_pass = _segmentation_pass_from_crop(
        cropped_frame,
        seg_list,
        crop_xyxy_frame_px=crop_xyxy,
        conf_threshold=config.conf_threshold,
        seg_weights_path=config.yolo_seg_weights,
    )

    if seg_pass is None:
        return FramePerceptionRecord(
            idx=idx,
            timestamp=timestamp,
            frame=FrameSize(width=w, height=h),
            status=FramePerceptionStatus.SEGMENTATION_FAILED,
            object_detection=od_pass,
            pose_estimation=pose_pass,
            provenance=prov,
        )

    return FramePerceptionRecord(
        idx=idx,
        timestamp=timestamp,
        frame=FrameSize(width=w, height=h),
        status=FramePerceptionStatus.OK,
        object_detection=od_pass,
        pose_estimation=pose_pass,
        segmentation=seg_pass,
        provenance=prov,
    )


__all__ = [
    "PerceptionRunConfig",
    "perceive_frame_pipeline",
]
