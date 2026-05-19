#!/usr/bin/env python3
"""
Offline tool: stream overall_results.json, split the person mask using pose bones,
overlay colors on the segmented region(s), draw the full BlazePose skeleton, and
write an MP4.

Use ``--analysis back`` (default) for **below-mouth–above-hip** vertical band ∩ person mask,
ipso-lateral shoulder–hip reference (**12→24** when camera RIGHT, **11→23** when LEFT),
and a **half-plane** split (nose anchor). Half-plane back pixels are reduced to one **polyline**
per occupied column (**RIGHT**: min ``y`` per ``x``, **LEFT**: max ``y`` per ``x``), sorted by ``x``
and drawn **solid red**; the same vertices are exported in **`Back`** and optional NPZ manifests.

``--pixels-out DIR`` saves compressed ``*.npz`` with ``crop_y``/``crop_x`` (row/col in crop)
and ``full_frame_*`` coords plus ``back_pixel_manifest.json``.

Large exports need ``ijson`` (``uv pip install ijson``). Example:

  cd backend && uv run python src/scripts/body_part_overlay_video.py

Imports ``pipeline.back_profile`` for shared back-geometry helpers.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator, Literal

import cv2
import numpy as np

# Repo scripts: ensure ``src/`` is importable (same pattern as ``tests/conftest.py``).
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pipeline.back_profile import (
    LM_L_HIP,
    LM_L_SHOULDER,
    LM_MOUTH_LEFT,
    LM_MOUTH_RIGHT,
    LM_NOSE,
    LM_R_HIP,
    LM_R_SHOULDER,
    Back,
    back_region_halfplane_mask,
    landmarks_to_px,
    resolve_shoulder_hip_reference,
)

# --- MediaPipe Pose Landmarker landmark index → name (33 keypoints).
MEDIAPIPE_POSE_LANDMARK_INDEX: tuple[str, ...] = (
    "nose",
    "left eye (inner)",
    "left eye",
    "left eye (outer)",
    "right eye (inner)",
    "right eye",
    "right eye (outer)",
    "left ear",
    "right ear",
    "mouth (left)",
    "mouth (right)",
    "left shoulder",
    "right shoulder",
    "left elbow",
    "right elbow",
    "left wrist",
    "right wrist",
    "left pinky",
    "right pinky",
    "left index",
    "right index",
    "left thumb",
    "right thumb",
    "left hip",
    "right hip",
    "left knee",
    "right knee",
    "left ankle",
    "right ankle",
    "left heel",
    "right heel",
    "left foot index",
    "right foot index",
)

AnalysisMode = Literal["full", "back"]

# BlazePose skeleton for drawing — same topology as PoseLandmarksConnections.POSE_LANDMARKS.
POSE_SKELETON_EDGES: list[tuple[int, int]] = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 7),
    (0, 4),
    (4, 5),
    (5, 6),
    (6, 8),
    (9, 10),
    (11, 12),
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),
    (17, 19),
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),
    (18, 20),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (24, 26),
    (25, 27),
    (26, 28),
    (27, 29),
    (28, 30),
    (29, 31),
    (30, 32),
    (27, 31),
    (28, 32),
]

# Body part ids 1..K — label 0 = unlabeled / outside mask
PART_NAMES: list[str] = [
    "head",
    "torso",
    "left_upper_arm",
    "right_upper_arm",
    "left_forearm",
    "right_forearm",
    "left_hand",
    "right_hand",
    "left_thigh",
    "right_thigh",
    "left_shin",
    "right_shin",
    "left_foot",
    "right_foot",
]

# (body_part_id 1-based, landmark_index_a, landmark_index_b)
BONE_SEGMENTS: list[tuple[int, int, int]] = [
    # head (1)
    (1, 0, 1),
    (1, 1, 2),
    (1, 2, 3),
    (1, 3, 7),
    (1, 0, 4),
    (1, 4, 5),
    (1, 5, 6),
    (1, 6, 8),
    (1, 9, 10),
    (1, 0, 7),
    (1, 0, 8),
    (1, 7, 8),
    # torso (2)
    (2, 11, 12),
    (2, 11, 23),
    (2, 12, 24),
    (2, 23, 24),
    # arms
    (3, 11, 13),
    (4, 12, 14),
    (5, 13, 15),
    (6, 14, 16),
    (7, 15, 17),
    (7, 15, 19),
    (7, 15, 21),
    (8, 16, 18),
    (8, 16, 20),
    (8, 16, 22),
    # legs
    (9, 23, 25),
    (10, 24, 26),
    (11, 25, 27),
    (12, 26, 28),
    (13, 27, 29),
    (13, 29, 31),
    (13, 27, 31),
    (14, 28, 30),
    (14, 30, 32),
    (14, 28, 32),
]


# Accent for back-mode landmark dots / skeleton accents (BGR).
BACK_SEGMENT_OVERLAY_BGR: tuple[int, int, int] = (80, 200, 255)

# Solid back profile polyline (BGR) and thickness in ``--analysis back``.
BACK_POLYLINE_BGR: tuple[int, int, int] = (0, 0, 255)
BACK_POLYLINE_THICKNESS = 3

BACK_HIGHLIGHT_LANDMARKS: tuple[int, ...] = (
    LM_MOUTH_LEFT,
    LM_MOUTH_RIGHT,
    LM_L_HIP,
    LM_R_HIP,
    LM_L_SHOULDER,
    LM_R_SHOULDER,
    LM_NOSE,
)


def sniff_camera_view_from_json(json_path: Path, max_scan_bytes: int = 16_388_608) -> str | None:
    """Read optional root ``camera_view`` from JSON without full parse."""
    try:
        with json_path.open("rb") as f:
            snippet = f.read(max_scan_bytes).decode("utf-8", errors="ignore")
        m = re.search(r'"camera_view"\s*:\s*"([^"]+)"', snippet)
        if not m:
            return None
        return m.group(1).strip().upper()
    except OSError:
        return None


def _part_bgr(part_id: int) -> tuple[int, int, int]:
    """Distinct BGR for part_id 1..14."""
    if part_id <= 0:
        return (0, 0, 0)
    hue = int(((part_id - 1) * 180) / max(len(PART_NAMES), 1)) % 180
    hsv = np.uint8([[[hue, 200, 255]]])
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])


def iter_results(path: Path) -> Iterator[dict[str, Any]]:
    size = path.stat().st_size
    if size > 64 * 1024 * 1024:
        try:
            import ijson  # type: ignore[import-not-found]
        except ImportError as e:
            raise SystemExit(
                "File is large; install ijson for streaming: pip install ijson"
            ) from e
        with path.open("rb") as f:
            yield from ijson.items(f, "results.item")
    else:
        with path.open() as f:
            data = json.load(f)
            for r in data["results"]:
                yield r


def scan_canvas_and_fps(path: Path) -> tuple[int, int, float]:
    """Light-weight scan: avoid loading base64 blobs. Large files use ijson."""
    max_w, max_h = 0, 0
    ts: list[float] = []

    def _fps_from_ts() -> float:
        fps = 30.0
        if len(ts) >= 2:
            ts_sorted = np.sort(np.array(ts, dtype=np.float64))
            diffs = np.diff(ts_sorted)
            diffs = diffs[diffs > 1e-9]
            if len(diffs) > 0:
                med = float(np.median(diffs))
                if med > 0:
                    fps = min(120.0, max(5.0, 1.0 / med))
        return fps

    if path.stat().st_size <= 64 * 1024 * 1024:
        with path.open() as f:
            data = json.load(f)
        for r in data.get("results", []):
            seg = r.get("segmentation_result") or {}
            xy = seg.get("frame_crop_xyxy") or [0, 0, 0, 0]
            x2, y2 = int(xy[2]), int(xy[3])
            max_w = max(max_w, x2)
            max_h = max(max_h, y2)
            t = r.get("timestamp")
            if isinstance(t, (int, float)):
                ts.append(float(t))
        return max(max_w, 1), max(max_h, 1), _fps_from_ts()

    try:
        import ijson  # type: ignore[import-not-found]
    except ImportError as e:
        raise SystemExit(
            "Large JSON requires ijson (pip install ijson) for metadata scan"
        ) from e

    with path.open("rb") as f:
        for xy in ijson.items(f, "results.item.segmentation_result.frame_crop_xyxy"):
            _x1, _y1, x2, y2 = (int(v) for v in xy)
            max_w = max(max_w, x2)
            max_h = max(max_h, y2)

    with path.open("rb") as f:
        for t in ijson.items(f, "results.item.timestamp"):
            if isinstance(t, (int, float)):
                ts.append(float(t))

    return max(max_w, 1), max(max_h, 1), _fps_from_ts()


def decode_crop_and_mask(
    seg: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    cw = int(seg["mask_width"])
    ch = int(seg["mask_height"])
    crop_raw = base64.standard_b64decode(seg["crop_bgr_raw_base64"])
    crop = np.frombuffer(crop_raw, dtype=np.uint8).reshape((ch, cw, 3))
    mask_raw = base64.standard_b64decode(seg["mask_raw_base64"])
    mask = np.frombuffer(mask_raw, dtype=np.uint8).reshape((ch, cw))
    x1, y1, x2, y2 = (int(v) for v in seg["frame_crop_xyxy"])
    return crop, mask, (x1, y1, x2, y2)


def _segments_for_assignment(
    pts_xy: np.ndarray,
    good: np.ndarray,
    analysis: AnalysisMode,
) -> tuple[list[tuple[float, float, float, float]], list[int]]:
    if analysis != "full":
        return [], []

    seg_rows: list[tuple[float, float, float, float]] = []
    part_ids: list[int] = []

    for pid, a, b in BONE_SEGMENTS:
        if not good[a] or not good[b]:
            continue
        ax, ay = pts_xy[a, 0], pts_xy[a, 1]
        bx, by = pts_xy[b, 0], pts_xy[b, 1]
        seg_rows.append((ax, ay, bx, by))
        part_ids.append(pid)
    return seg_rows, part_ids


def draw_shoulder_hip_reference(
    image_bgr: np.ndarray,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> None:
    h_im, w_im = image_bgr.shape[:2]
    pa = (
        int(np.clip(round(ax), 0, w_im - 1)),
        int(np.clip(round(ay), 0, h_im - 1)),
    )
    pb = (
        int(np.clip(round(bx), 0, w_im - 1)),
        int(np.clip(round(by), 0, h_im - 1)),
    )
    cv2.line(image_bgr, pa, pb, (255, 255, 255), 4, cv2.LINE_AA)
    cv2.line(image_bgr, pa, pb, (0, 0, 255), 2, cv2.LINE_AA)


def save_back_pixels_npz(
    pixels_dir: Path,
    frame_idx: int,
    timestamp: float,
    ys: np.ndarray,
    xs: np.ndarray,
    crop_h: int,
    crop_w: int,
    full_y1: int,
    full_x1: int,
) -> str:
    """Write ``crop_*`` / ``full_frame_*`` `(y,x)` coordinates (back-mode = polyline vertices)."""
    pixels_dir.mkdir(parents=True, exist_ok=True)
    path = pixels_dir / f"back_px_{frame_idx:06d}.npz"
    fy = np.asarray(ys, dtype=np.int64) + int(full_y1)
    fx = np.asarray(xs, dtype=np.int64) + int(full_x1)
    np.savez_compressed(
        path,
        frame_idx=np.int64(frame_idx),
        timestamp=np.float64(timestamp),
        crop_y=np.asarray(ys, dtype=np.int32),
        crop_x=np.asarray(xs, dtype=np.int32),
        full_frame_y=fy.astype(np.int32),
        full_frame_x=fx.astype(np.int32),
        crop_shape=np.array([crop_h, crop_w], dtype=np.int32),
    )
    return path.name


def assign_body_parts_mask(
    mask_u8: np.ndarray,
    landmarks: list[dict[str, Any]],
    w: int,
    h: int,
    vis_thresh: float,
    chunk: int = 48_000,
    analysis: AnalysisMode = "full",
) -> np.ndarray:
    pts_xy, good = landmarks_to_px(landmarks, w, h, vis_thresh)
    seg_rows, part_ids = _segments_for_assignment(pts_xy, good, analysis)
    out = np.zeros((h, w), dtype=np.uint8)
    ys, xs = np.where(mask_u8 > 0)
    if len(xs) == 0 or len(seg_rows) == 0:
        return out
    seg_arr = np.array(seg_rows, dtype=np.float64)
    part_arr = np.array(part_ids, dtype=np.int32)
    ab = seg_arr[:, 2:4] - seg_arr[:, 0:2]
    ab_sq = np.maximum((ab**2).sum(axis=1), 1e-12)

    for start in range(0, len(xs), chunk):
        sl = slice(start, start + chunk)
        xc = xs[sl].astype(np.float64)
        yc = ys[sl].astype(np.float64)
        p = np.stack([xc, yc], axis=1)
        ap = p[None, :, :] - seg_arr[:, None, 0:2]
        t = (ap * ab[:, None, :]).sum(axis=2) / ab_sq[:, None]
        t = np.clip(t, 0.0, 1.0)
        proj = seg_arr[:, None, 0:2] + t[:, :, None] * ab[:, None, :]
        dist_sq = ((p[None, :, :] - proj) ** 2).sum(axis=2)
        best = np.argmin(dist_sq, axis=0)
        out[ys[sl], xs[sl]] = part_arr[best].astype(np.uint8)
    return out


def blend_part_colors(
    crop_bgr: np.ndarray,
    labels: np.ndarray,
    alpha: float,
    analysis: AnalysisMode,
) -> np.ndarray:
    overlay = crop_bgr.copy()
    if analysis == "back":
        m = labels == 1
        if np.any(m):
            col = np.array(BACK_SEGMENT_OVERLAY_BGR, dtype=np.float64)
            overlay[m] = (overlay[m].astype(np.float64) * (1 - alpha) + col * alpha).astype(
                np.uint8
            )
        return overlay

    for pid in range(1, len(PART_NAMES) + 1):
        m = labels == pid
        if not np.any(m):
            continue
        col = np.array(_part_bgr(pid), dtype=np.float64)
        overlay[m] = (overlay[m].astype(np.float64) * (1 - alpha) + col * alpha).astype(
            np.uint8
        )
    return overlay


def draw_pose(
    image_bgr: np.ndarray,
    landmarks: list[dict[str, Any]],
    w: int,
    h: int,
    vis_thresh: float,
    analysis: AnalysisMode,
) -> None:
    pts, good = landmarks_to_px(landmarks, w, h, vis_thresh)

    muted = (88, 88, 92)
    outline = (200, 200, 205)
    highlight_line = BACK_SEGMENT_OVERLAY_BGR

    for a, b in POSE_SKELETON_EDGES:
        if not good[a] or not good[b]:
            continue
        pa = (int(round(pts[a, 0])), int(round(pts[a, 1])))
        pb = (int(round(pts[b, 0])), int(round(pts[b, 1])))
        thickness = 1 if analysis == "back" else 2
        inner = muted if analysis == "back" else (40, 200, 40)
        oc = outline if analysis == "back" else (255, 255, 255)
        cv2.line(image_bgr, pa, pb, oc, thickness + 1, cv2.LINE_AA)
        cv2.line(image_bgr, pa, pb, inner, thickness, cv2.LINE_AA)

    for i in range(33):
        if not good[i]:
            continue
        p = (int(round(pts[i, 0])), int(round(pts[i, 1])))
        if analysis == "back":
            extra = i in BACK_HIGHLIGHT_LANDMARKS
            r = 7 if extra else 3
            fill = BACK_SEGMENT_OVERLAY_BGR if extra else (160, 160, 170)
            cv2.circle(image_bgr, p, r + 2, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.circle(image_bgr, p, r, fill, -1, cv2.LINE_AA)
            if extra:
                cv2.circle(image_bgr, p, r, (0, 0, 0), 1, cv2.LINE_AA)
        else:
            cv2.circle(image_bgr, p, 5, (0, 220, 255), -1, cv2.LINE_AA)
            cv2.circle(image_bgr, p, 5, (0, 0, 0), 1, cv2.LINE_AA)


def render_frame(
    seg: dict[str, Any],
    pose: dict[str, Any],
    vis_thresh: float,
    blend: float,
    analysis: AnalysisMode,
    camera_view: str,
) -> tuple[np.ndarray, dict[str, Any] | None]:
    crop, mask, _ = decode_crop_and_mask(seg)
    ch, cw = crop.shape[:2]
    lm_groups = pose.get("pose_landmarks")
    if not lm_groups:
        return crop, None
    landmarks = lm_groups[0]
    if not landmarks or len(landmarks) < 33:
        return crop, None

    extras: dict[str, Any] | None = None
    if analysis == "back":
        _labels, by, bx, bk, _by_raw, _bx_raw = back_region_halfplane_mask(
            mask,
            landmarks,
            ch,
            cw,
            vis_thresh,
            camera_view=camera_view,
        )
        vis = crop.copy()
        draw_pose(vis, landmarks, cw, ch, vis_thresh, analysis=analysis)
        px_rf, gd_rf = landmarks_to_px(landmarks, cw, ch, vis_thresh)
        ref = resolve_shoulder_hip_reference(px_rf, gd_rf, camera_view)
        if ref is not None:
            a0, b0, _tag = ref
            draw_shoulder_hip_reference(
                vis, float(a0[0]), float(a0[1]), float(b0[0]), float(b0[1])
            )
        if len(bx) >= 2:
            poly = np.stack([bx, by], axis=1).astype(np.int32)
            poly_cv = poly.reshape(-1, 1, 2)
            cv2.polylines(
                vis,
                [poly_cv],
                isClosed=False,
                color=BACK_POLYLINE_BGR,
                thickness=BACK_POLYLINE_THICKNESS,
                lineType=cv2.LINE_AA,
            )
        elif len(bx) == 1:
            p = (int(bx[0]), int(by[0]))
            cv2.circle(
                vis,
                p,
                max(3, BACK_POLYLINE_THICKNESS + 2),
                BACK_POLYLINE_BGR,
                -1,
                lineType=cv2.LINE_AA,
            )
        extras = {
            "back_crop_y": by,
            "back_crop_x": bx,
            "n_back_px": int(len(by)),
            "back": bk,
        }
        return vis, extras

    labels = assign_body_parts_mask(mask, landmarks, cw, ch, vis_thresh, analysis="full")
    vis = blend_part_colors(crop, labels, blend, analysis=analysis)
    draw_pose(vis, landmarks, cw, ch, vis_thresh, analysis=analysis)
    return vis, None


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    default_json = script_dir.parent / "overall_results.json"

    ap = argparse.ArgumentParser(
        description="Render torso/back or full-body segmented overlay + BlazePose skeleton from overall_results.json",
    )
    ap.add_argument(
        "--input-json",
        type=Path,
        default=default_json,
        help="Path to overall_results.json (large files need ijson)",
    )
    ap.add_argument(
        "--output-video",
        "-o",
        type=Path,
        default=None,
        help="Output video (.mp4). Default: back_segment_overlay.mp4 or body_part_overlay.mp4",
    )
    ap.add_argument(
        "--analysis",
        choices=["back", "full"],
        default="back",
        help=(
            "back: half-plane back profile as solid red polyline + skeleton; "
            "full: 14-part bones"
        ),
    )
    ap.add_argument(
        "--camera-view",
        choices=["LEFT", "RIGHT"],
        default=None,
        help="RIGHT or LEFT: chooses ipsilateral hip→shoulder segment; default from JSON or RIGHT",
    )
    ap.add_argument(
        "--pixels-out",
        type=Path,
        default=None,
        help="Directory: per-frame .npz back pixels + back_pixel_manifest.json",
    )
    ap.add_argument("--fps", type=float, default=None,
                    help="Override FPS (default: infer from timestamps)")
    ap.add_argument(
        "--visibility",
        type=float,
        default=0.5,
        help="Landmark visibility threshold (0-1)",
    )
    ap.add_argument(
        "--blend",
        type=float,
        default=0.38,
        help="Alpha for body-part color overlay on crop",
    )
    ap.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Stop after this many frames (for testing)",
    )
    args = ap.parse_args()

    inp = args.input_json.expanduser()
    if not inp.is_file():
        print(f"Input not found: {inp}", file=sys.stderr)
        raise SystemExit(1)

    analysis: AnalysisMode = args.analysis  # type: ignore[assignment]
    camera_eff = (
        args.camera_view or sniff_camera_view_from_json(inp) or "RIGHT"
    ).strip().upper()
    out_path = args.output_video
    if out_path is None:
        name = (
            "back_segment_overlay.mp4"
            if analysis == "back"
            else "body_part_overlay.mp4"
        )
        out_path = script_dir.parent / name

    print("Pass 1: canvas size and FPS …", flush=True)
    max_w, max_h, fps_guess = scan_canvas_and_fps(inp)
    fps = args.fps if args.fps is not None else fps_guess
    print(f"  canvas {max_w}x{max_h}, fps={fps:.2f}", flush=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_path = out_path.expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (max_w, max_h))
    if not writer.isOpened():
        print(f"Failed to open VideoWriter for {out_path}", file=sys.stderr)
        raise SystemExit(1)

    print(f"  camera_view (reference line): {camera_eff}", flush=True)

    n = 0
    print("Pass 2: rendering …", flush=True)
    manifest: list[dict[str, Any]] = []
    try:
        for obj in iter_results(inp):
            seg = obj.get("segmentation_result")
            pose = obj.get("pose_estimation_result")
            if not seg or not pose:
                continue
            try:
                vis, fb_extras = render_frame(
                    seg,
                    pose,
                    args.visibility,
                    args.blend,
                    analysis=analysis,
                    camera_view=camera_eff,
                )
            except Exception as e:  # noqa: BLE001
                print(f"  frame skip: {e}", file=sys.stderr)
                continue
            ch, cw = vis.shape[:2]
            xy = seg.get("frame_crop_xyxy") or [0, 0, cw, ch]
            x1, y1 = int(xy[0]), int(xy[1])

            if (
                args.pixels_out is not None
                and analysis == "back"
                and fb_extras is not None
                and fb_extras.get("n_back_px", 0) > 0
            ):
                fn = save_back_pixels_npz(
                    args.pixels_out.expanduser(),
                    int(obj.get("idx", n)),
                    float(obj.get("timestamp", 0.0)),
                    fb_extras["back_crop_y"],
                    fb_extras["back_crop_x"],
                    ch,
                    cw,
                    y1,
                    x1,
                )
                b = fb_extras.get("back")
                row: dict[str, Any] = {
                    "idx": int(obj.get("idx", n)),
                    "timestamp": float(obj.get("timestamp", 0.0)),
                    "n_back_pixels": int(fb_extras["n_back_px"]),
                    "npz_file": fn,
                }
                if isinstance(b, Back):
                    row["reference_segment"] = b.reference_segment
                    row["x_span"] = b.x_span
                    row["y_span"] = b.y_span
                manifest.append(row)

            canvas = np.zeros((max_h, max_w, 3), dtype=np.uint8)
            y_end = min(y1 + ch, max_h)
            x_end = min(x1 + cw, max_w)
            crop_h = y_end - y1
            crop_w = x_end - x1
            if crop_h > 0 and crop_w > 0:
                canvas[y1:y_end, x1:x_end] = vis[:crop_h, :crop_w]

            writer.write(canvas)
            n += 1
            if n % 50 == 0:
                print(f"  {n} frames", flush=True)
            if args.max_frames is not None and n >= args.max_frames:
                break
    finally:
        writer.release()

    if manifest and args.pixels_out is not None:
        man_path = args.pixels_out.expanduser() / "back_pixel_manifest.json"
        man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Wrote {len(manifest)} back-pixel records manifest → {man_path}")

    print(f"Done. Wrote {n} frames to {out_path}")


if __name__ == "__main__":
    main()
