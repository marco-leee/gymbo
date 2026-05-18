"""Back-profile geometry from person mask + BODY-33 landmarks (crop pixel space).

Shared with offline overlay tooling; semantics match ``body_part_overlay_video`` back mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

# Landmark indices for vertical torso band & shoulder→hip references.
LM_NOSE = 0
LM_MOUTH_LEFT = 9
LM_MOUTH_RIGHT = 10
LM_L_SHOULDER = 11
LM_R_SHOULDER = 12
LM_L_HIP = 23
LM_R_HIP = 24


@dataclass
class Back:
    """Back profile polyline in crop coords (vertices sorted by ascending column ``x``)."""

    raw_pixels_crop_yx: np.ndarray  # shape (N, 2), int32 — row=y, col=x
    n_pixels: int
    x_span: int
    y_span: int
    reference_segment: str


def landmarks_to_px(
    landmarks: list[dict[str, Any]], w: int, h: int, vis_thresh: float
) -> tuple[np.ndarray, np.ndarray]:
    pts = np.zeros((33, 2), dtype=np.float64)
    vis = np.zeros(33, dtype=np.float64)
    for i in range(min(33, len(landmarks))):
        lm = landmarks[i]
        vis[i] = float(lm.get("visibility") or 0.0)
        pts[i, 0] = float(lm["x"]) * w
        pts[i, 1] = float(lm["y"]) * h
    good = vis >= vis_thresh
    return pts, good


def _cross_z(ax: float, ay: float, bx: float, by: float, px: float, py: float) -> float:
    return (bx - ax) * (py - ay) - (by - ay) * (px - ax)


def _torso_y_extent(
    pts_xy: np.ndarray,
    good: np.ndarray,
    h: int,
) -> tuple[int, int]:
    mouth_ys: list[float] = []
    if good[LM_MOUTH_LEFT]:
        mouth_ys.append(float(pts_xy[LM_MOUTH_LEFT, 1]))
    if good[LM_MOUTH_RIGHT]:
        mouth_ys.append(float(pts_xy[LM_MOUTH_RIGHT, 1]))
    if not mouth_ys and good[LM_NOSE]:
        mouth_ys.append(float(pts_xy[LM_NOSE, 1]) + float(h) * 0.02)

    hip_ys: list[float] = []
    if good[LM_L_HIP]:
        hip_ys.append(float(pts_xy[LM_L_HIP, 1]))
    if good[LM_R_HIP]:
        hip_ys.append(float(pts_xy[LM_R_HIP, 1]))

    if mouth_ys:
        y_below_mouth = max(mouth_ys)
    elif good[LM_NOSE]:
        y_below_mouth = float(pts_xy[LM_NOSE, 1]) + float(h) * 0.04
    else:
        y_below_mouth = float(h) * 0.08

    if hip_ys:
        y_above_hip = min(hip_ys)
    else:
        y_above_hip = float(h) * 0.65

    r0 = int(np.clip(np.floor(y_below_mouth), 0, h - 1))
    r1 = int(np.clip(np.ceil(y_above_hip), 0, h - 1))

    if r0 >= r1:
        mid = h // 2
        r0 = max(0, mid - max(8, h // 14))
        r1 = min(h - 1, mid + max(8, h // 14))
        if r0 >= r1:
            r1 = min(h - 1, r0 + 4)
    return r0, r1


def resolve_shoulder_hip_reference(
    pts_xy: np.ndarray,
    good: np.ndarray,
    camera_view: str,
) -> tuple[np.ndarray, np.ndarray, str] | None:
    cvu = camera_view.strip().upper()

    if cvu == "RIGHT" and good[LM_R_SHOULDER] and good[LM_R_HIP]:
        return (
            pts_xy[LM_R_HIP].copy(),
            pts_xy[LM_R_SHOULDER].copy(),
            "hip24-shoulder12",
        )
    if cvu == "LEFT" and good[LM_L_SHOULDER] and good[LM_L_HIP]:
        return (
            pts_xy[LM_L_HIP].copy(),
            pts_xy[LM_L_SHOULDER].copy(),
            "hip23-shoulder11",
        )
    if good[LM_L_SHOULDER] and good[LM_L_HIP]:
        return (
            pts_xy[LM_L_HIP].copy(),
            pts_xy[LM_L_SHOULDER].copy(),
            "hip23-shoulder11",
        )
    if good[LM_R_SHOULDER] and good[LM_R_HIP]:
        return (
            pts_xy[LM_R_HIP].copy(),
            pts_xy[LM_R_SHOULDER].copy(),
            "hip24-shoulder12",
        )
    if good[LM_L_SHOULDER] and good[LM_R_SHOULDER] and good[LM_L_HIP] and good[LM_R_HIP]:
        m_sh = (pts_xy[LM_L_SHOULDER] + pts_xy[LM_R_SHOULDER]) / 2.0
        m_hp = (pts_xy[LM_L_HIP] + pts_xy[LM_R_HIP]) / 2.0
        return (m_hp, m_sh, "mid-shoulder-mid-hip")
    return None


def back_region_halfplane_mask(
    mask_u8: np.ndarray,
    landmarks: list[dict[str, Any]],
    h: int,
    w: int,
    vis_thresh: float,
    camera_view: str,
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, Back | None, np.ndarray, np.ndarray
]:
    empty_y = np.array([], dtype=np.int32)
    empty_x = np.array([], dtype=np.int32)
    out = np.zeros((h, w), dtype=np.uint8)

    pts_xy, good = landmarks_to_px(landmarks, w, h, vis_thresh)
    r0, r1 = _torso_y_extent(pts_xy, good, h)
    ri1exclusive = max(r1, r0 + 1)

    band = np.zeros((h, w), dtype=np.uint8)
    band[r0:ri1exclusive, :] = 1

    ref = resolve_shoulder_hip_reference(pts_xy, good, camera_view)
    if ref is None:
        return out, empty_y, empty_x, None, empty_y, empty_x

    ah, bh, ref_tag = ref
    ax, ay = float(ah[0]), float(ah[1])
    bx, by = float(bh[0]), float(bh[1])

    torso_cand = (mask_u8 > 0) & (band > 0)

    cy, cx = np.where(torso_cand)
    if len(cx) == 0:
        return out, empty_y, empty_x, None, empty_y, empty_x

    anch_x = anch_y = None
    if good[LM_NOSE]:
        anch_x = float(pts_xy[LM_NOSE, 0])
        anch_y = float(pts_xy[LM_NOSE, 1])
    elif good[LM_MOUTH_LEFT] or good[LM_MOUTH_RIGHT]:
        xs_m: list[float] = []
        ys_m: list[float] = []
        if good[LM_MOUTH_LEFT]:
            xs_m.append(float(pts_xy[LM_MOUTH_LEFT, 0]))
            ys_m.append(float(pts_xy[LM_MOUTH_LEFT, 1]))
        if good[LM_MOUTH_RIGHT]:
            xs_m.append(float(pts_xy[LM_MOUTH_RIGHT, 0]))
            ys_m.append(float(pts_xy[LM_MOUTH_RIGHT, 1]))
        anch_x = float(sum(xs_m) / len(xs_m))
        anch_y = float(sum(ys_m) / len(ys_m))

    c_anchor = (
        _cross_z(ax, ay, bx, by, anch_x, anch_y) if anch_x is not None else 0.0
    )

    cross_vals = (bx - ax) * (
        cy.astype(np.float64) - ay
    ) - (by - ay) * (cx.astype(np.float64) - ax)

    if abs(c_anchor) > 5.0:
        same_as_anchor = cross_vals * c_anchor > 0
        keep = ~same_as_anchor
    else:
        median_x = float(np.median(cx.astype(np.float64)))
        cvu = camera_view.strip().upper()
        if cvu == "RIGHT":
            keep = cx.astype(np.float64) < median_x
        else:
            keep = cx.astype(np.float64) > median_x

    by_h = cy[keep]
    bx_h = cx[keep]
    if len(by_h) == 0:
        return out, empty_y, empty_x, None, empty_y, empty_x

    order = np.argsort(bx_h.astype(np.int64), kind="mergesort")
    xs_s = bx_h[order].astype(np.int32, copy=False)
    ys_s = by_h[order].astype(np.int32, copy=False)
    ux, counts = np.unique(xs_s, return_counts=True)
    idx0 = np.concatenate([[0], np.cumsum(counts[:-1])])
    cvu_keep = camera_view.strip().upper()
    if cvu_keep == "RIGHT":
        y_line = np.minimum.reduceat(ys_s, idx0)
    else:
        y_line = np.maximum.reduceat(ys_s, idx0)

    bx_back = ux.astype(np.int32)
    by_back = y_line.astype(np.int32)

    raw = np.stack([by_back.astype(np.int32), bx_back.astype(np.int32)], axis=1)
    xmin = int(bx_back.min())
    xmax = int(bx_back.max())
    ymin_i = int(by_back.min())
    ymax_i = int(by_back.max())
    bk = Back(
        raw_pixels_crop_yx=raw,
        n_pixels=int(raw.shape[0]),
        x_span=xmax - xmin + 1,
        y_span=ymax_i - ymin_i + 1,
        reference_segment=ref_tag,
    )
    by_raw = by_h.astype(np.int32, copy=False)
    bx_raw = bx_h.astype(np.int32, copy=False)
    return out, by_back, bx_back, bk, by_raw, bx_raw
