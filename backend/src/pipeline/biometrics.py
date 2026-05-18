"""Per-frame biometrics from perception output (KIPs, back polyline, reps placeholder)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from exercises.base import KeyInterestPoint2D
from models.exercise import ExerciseType
from pipeline.back_profile import Back, back_region_halfplane_mask
from pipeline.frame_state import FramePerceptionState
from rep_counter.registry import get_rep_spec
from utils.video import CameraView


class BackShapeSnapshot(BaseModel):
    """Serializable back profile (crop + optional full-frame vertices)."""

    reference_segment: str
    n_vertices: int
    x_span: int
    y_span: int
    polyline_crop_yx: list[list[int]] = Field(
        description="Each [row_y, col_x] in crop pixels — all back half-plane mask pixels "
        "up to and including the column where the per-x profile first hits extremal y "
        "(n_vertices equals len of this list)."
    )
    polyline_full_frame_yx: list[list[int]] | None = Field(
        default=None,
        description="Optional [y, x] in full-frame pixels (crop origin offset)",
    )


class FrameBiometricsResult(BaseModel):
    """Per-frame measurements derived from perception.

    ``reps`` is a placeholder until timeline hysteresis is wired (see ``rep-set-counter.py``).
    """

    key_interest_points_2d: dict[str, dict[str, Any]]
    back_shape: BackShapeSnapshot | None = None
    reps: int | None = Field(default=None, description="Reserved; not computed per frame yet.")


def _landmarks_as_namespaces(pose_landmarks: object) -> list[SimpleNamespace] | None:
    if not pose_landmarks or not isinstance(pose_landmarks, list):
        return None
    group = pose_landmarks[0]
    if not group or not isinstance(group, list):
        return None
    return [SimpleNamespace(**lm) for lm in group]


def back_profile_to_snapshot(
    bk: Back,
    frame_crop_xyxy: tuple[int, int, int, int] | None,
) -> BackShapeSnapshot:
    raw = bk.raw_pixels_crop_yx
    poly_crop = raw.astype(np.int64).tolist()
    full_list: list[list[int]] | None = None
    if frame_crop_xyxy is not None:
        x1, y1, _x2, _y2 = frame_crop_xyxy
        fy = raw[:, 0].astype(np.int64) + int(y1)
        fx = raw[:, 1].astype(np.int64) + int(x1)
        full_list = np.stack([fy, fx], axis=1).tolist()
    return BackShapeSnapshot(
        reference_segment=bk.reference_segment,
        n_vertices=int(bk.n_pixels),
        x_span=int(bk.x_span),
        y_span=int(bk.y_span),
        polyline_crop_yx=poly_crop,
        polyline_full_frame_yx=full_list,
    )


def _filter_back_mask_pixels_to_first_peak_column(
    bk: Back,
    by_raw: np.ndarray,
    bx_raw: np.ndarray,
    camera_view: CameraView,
) -> Back:
    """Keep every back half-plane mask pixel with x <= x_peak.

    x_peak is the column (ascending x order) where the per-x extremal edge first hits
    its global extremum: first max y (LEFT) or first min y (RIGHT), matching
    ``back_region_halfplane_mask`` reduceat semantics.
    """
    poly = bk.raw_pixels_crop_yx
    if poly.size == 0:
        return bk
    if len(bx_raw) == 0:
        return bk
    ys_p = poly[:, 0].astype(np.int64, copy=False)
    xs_p = poly[:, 1].astype(np.int64, copy=False)
    if camera_view == CameraView.RIGHT:
        i_peak = int(np.argmin(ys_p))
    else:
        i_peak = int(np.argmax(ys_p))
    x_peak = int(xs_p[i_peak])
    sel = bx_raw.astype(np.int64, copy=False) <= x_peak
    by_s = by_raw[sel]
    bx_s = bx_raw[sel]
    if len(bx_s) == 0:
        empty = np.empty((0, 2), dtype=np.int32)
        return Back(
            raw_pixels_crop_yx=empty,
            n_pixels=0,
            x_span=0,
            y_span=0,
            reference_segment=bk.reference_segment,
        )
    ord_ = np.lexsort((by_s.astype(np.int64), bx_s.astype(np.int64)))
    raw_t = np.stack([by_s[ord_], bx_s[ord_]], axis=1).astype(np.int32)
    bx = raw_t[:, 1]
    by = raw_t[:, 0]
    xmin = int(bx.min())
    xmax = int(bx.max())
    ymin_i = int(by.min())
    ymax_i = int(by.max())
    return Back(
        raw_pixels_crop_yx=raw_t,
        n_pixels=int(raw_t.shape[0]),
        x_span=xmax - xmin + 1,
        y_span=ymax_i - ymin_i + 1,
        reference_segment=bk.reference_segment,
    )


def compute_frame_biometrics(
    state: FramePerceptionState,
    *,
    exercise_type: ExerciseType,
    camera_view: CameraView,
    vis_thresh: float = 0.5,
) -> FrameBiometricsResult | None:
    """Compute KIPs + back shape when perception produced pose, mask, and legacy export."""
    ov = state.overall_result
    if ov is None or state.mask_u8_crop is None:
        return None

    pose_lm = ov.pose_estimation_result.get("pose_landmarks")
    if (
        not pose_lm
        or not isinstance(pose_lm, list)
        or not pose_lm[0]
        or not isinstance(pose_lm[0], list)
        or len(pose_lm[0]) < 33
    ):
        return None

    landmarks_ns = _landmarks_as_namespaces(pose_lm)
    if landmarks_ns is None:
        return None

    ch, cw = state.mask_u8_crop.shape[:2]
    processor = get_rep_spec(exercise_type).processor
    kips: dict[str, KeyInterestPoint2D] = processor.get_2d_key_points(
        landmarks_ns, camera_view, ch, cw
    )
    kips_dump = {
        name: kip.model_dump(mode="json") for name, kip in kips.items()
    }

    landmarks_dicts: list[dict[str, Any]] = pose_lm[0]

    _mask_out, _by, _bx, bk, by_raw, bx_raw = back_region_halfplane_mask(
        state.mask_u8_crop,
        landmarks_dicts,
        ch,
        cw,
        vis_thresh,
        camera_view.value,
    )
    if bk is not None:
        bk = _filter_back_mask_pixels_to_first_peak_column(
            bk, by_raw, bx_raw, camera_view
        )

    seg = ov.segmentation_result
    xyxy: tuple[int, int, int, int] | None = None
    raw_xy = seg.get("frame_crop_xyxy")
    if (
        isinstance(raw_xy, (list, tuple))
        and len(raw_xy) == 4
        and all(isinstance(v, (int, float)) for v in raw_xy)
    ):
        xyxy = (int(raw_xy[0]), int(raw_xy[1]), int(raw_xy[2]), int(raw_xy[3]))

    back_snap = back_profile_to_snapshot(bk, xyxy) if bk is not None else None

    return FrameBiometricsResult(
        key_interest_points_2d=kips_dump,
        back_shape=back_snap,
    )
