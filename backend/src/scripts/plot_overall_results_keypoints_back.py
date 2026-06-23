#!/usr/bin/env python3
"""Plot 2D pose keypoints / back polyline from overall_results JSON.

- Default / ``--idx``: one crop frame (skeleton + back polyline).
- ``--timeseries``: figures — key-interest-point 2D coords vs timestamp, KIP joint angles vs
  timestamp, and back-shape vs timestamp (vertex count, polyline arc length and bbox spans in
  crop px; raw back-mask pixel count is not stored in the export).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pipeline.back_profile import landmarks_to_px

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


def _load_results(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _pick_frame(
    results: list[dict[str, Any]], idx: int | None
) -> tuple[int, dict[str, Any]]:
    if idx is not None:
        for r in results:
            if int(r.get("idx", -1)) == idx:
                return idx, r
        raise SystemExit(f"No frame with idx={idx}")
    for r in results:
        bio = r.get("biometrics") or {}
        if bio.get("back_shape"):
            return int(r.get("idx", -1)), r
    raise SystemExit("No frame with biometrics.back_shape; pass --idx explicitly")


def _style_dark_axes(ax: plt.Axes) -> None:
    ax.set_facecolor("#1e1e1e")
    ax.grid(True, color="#444444", linestyle="--", alpha=0.35)
    ax.tick_params(colors="#cccccc")
    for spine in ax.spines.values():
        spine.set_color("#666666")
    ax.set_xlabel(ax.get_xlabel(), color="#cccccc")
    ax.set_ylabel(ax.get_ylabel(), color="#cccccc")
    ax.set_title(ax.get_title(), color="white", fontsize=10)
    leg = ax.get_legend()
    if leg is not None:
        frame = leg.get_frame()
        if frame is not None:
            frame.set_facecolor("#2a2a2a")
            frame.set_edgecolor("#666666")
        for t in leg.get_texts():
            t.set_color("white")


def _kip_coord_series(
    results: list[dict[str, Any]],
) -> dict[str, dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]]]:
    """Per KIP name / landmark idx: parallel ``(t, x, y)`` in crop pixels."""
    series: dict[str, dict[int, list[tuple[float, float, float]]]] = {}
    any_kip = False

    for r in results:
        bio = r.get("biometrics")
        if not bio:
            continue
        kips = bio.get("key_interest_points_2d")
        if not kips or not isinstance(kips, dict):
            continue
        ts = float(r.get("timestamp", 0.0))
        any_kip = True

        for kip_name, payload in kips.items():
            if not isinstance(payload, dict):
                continue
            mp = payload.get("idx_to_coordinates") or {}
            bucket = series.setdefault(kip_name, {})
            for li_str, xy in mp.items():
                try:
                    li = int(li_str)
                except (TypeError, ValueError):
                    continue
                if not isinstance(xy, (list, tuple)) or len(xy) < 2:
                    continue
                bucket.setdefault(li, []).append((ts, float(xy[0]), float(xy[1])))

    if not any_kip:
        return {}

    out: dict[str, dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]]] = {}
    for kip_name, by_idx in series.items():
        out[kip_name] = {}
        for li, triples in sorted(by_idx.items()):
            triples.sort(key=lambda x: x[0])
            tt = np.array([x[0] for x in triples], dtype=np.float64)
            xs = np.array([x[1] for x in triples], dtype=np.float64)
            ys = np.array([x[2] for x in triples], dtype=np.float64)
            out[kip_name][li] = (tt, xs, ys)
    return out


def _kip_angle_series(
    results: list[dict[str, Any]],
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Per KIP name: ``(timestamp_s, angle_deg)`` from stored ``angle`` field."""
    raw: dict[str, list[tuple[float, float]]] = {}
    any_kip = False

    for r in results:
        bio = r.get("biometrics")
        if not bio:
            continue
        kips = bio.get("key_interest_points_2d")
        if not kips or not isinstance(kips, dict):
            continue
        ts = float(r.get("timestamp", 0.0))
        any_kip = True

        for kip_name, payload in kips.items():
            if not isinstance(payload, dict):
                continue
            ang = payload.get("angle")
            if ang is None:
                continue
            try:
                a = float(ang)
            except (TypeError, ValueError):
                continue
            raw.setdefault(kip_name, []).append((ts, a))

    if not any_kip or not raw:
        return {}

    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for kip_name, pairs in raw.items():
        pairs.sort(key=lambda x: x[0])
        tt = np.array([p[0] for p in pairs], dtype=np.float64)
        aa = np.array([p[1] for p in pairs], dtype=np.float64)
        out[kip_name] = (tt, aa)
    return out


def _polyline_arc_length_crop(pl: object) -> float:
    """Euclidean length along ``polyline_crop_yx`` ([row,col] per vertex)."""
    if not pl or not isinstance(pl, list) or len(pl) < 2:
        return float("nan")
    arr = np.asarray(pl, dtype=np.float64)
    dr = np.diff(arr[:, 0])
    dc = np.diff(arr[:, 1])
    return float(np.sum(np.hypot(dr, dc)))


def _back_series(
    results: list[dict[str, Any]],
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Timestamps, n_vertices, spans, centroid, polyline arc length in crop px (NaN if no back)."""
    ts_: list[float] = []
    nv: list[float] = []
    sx: list[float] = []
    sy: list[float] = []
    mx: list[float] = []
    my: list[float] = []
    arc: list[float] = []
    for r in results:
        ts_.append(float(r.get("timestamp", 0.0)))
        bio = r.get("biometrics") or {}
        b = bio.get("back_shape")
        if not b or not isinstance(b, dict):
            nv.append(np.nan)
            sx.append(np.nan)
            sy.append(np.nan)
            mx.append(np.nan)
            my.append(np.nan)
            arc.append(np.nan)
            continue
        n = float(b.get("n_vertices", 0) or 0)
        nv.append(n)
        sx.append(float(b.get("x_span", np.nan)))
        sy.append(float(b.get("y_span", np.nan)))
        pl = b.get("polyline_crop_yx")
        arc.append(_polyline_arc_length_crop(pl if isinstance(pl, list) else []))
        if pl and len(pl) > 0:
            arr = np.asarray(pl, dtype=np.float64)
            my.append(float(np.mean(arr[:, 0])))
            mx.append(float(np.mean(arr[:, 1])))
        else:
            mx.append(np.nan)
            my.append(np.nan)
    return (
        np.asarray(ts_, dtype=np.float64),
        np.asarray(nv, dtype=np.float64),
        np.asarray(sx, dtype=np.float64),
        np.asarray(sy, dtype=np.float64),
        np.asarray(mx, dtype=np.float64),
        np.asarray(my, dtype=np.float64),
        np.asarray(arc, dtype=np.float64),
    )


def _plot_kip_timeseries(
    json_path: Path,
    results: list[dict[str, Any]],
    out: Path | None,
) -> Path:
    by_kip = _kip_coord_series(results)
    if not by_kip:
        raise SystemExit("No key_interest_points_2d in any frame; cannot plot KIP timeseries.")

    names = sorted(by_kip.keys())
    n = len(names)
    fig, axes = plt.subplots(n, 2, figsize=(11, 3.8 * n), dpi=120, sharex=True)
    fig.patch.set_facecolor("#1e1e1e")
    if n == 1:
        axes = np.array([axes])

    cmap = plt.colormaps["tab10"]

    for row, kip_name in enumerate(names):
        ax_x, ax_y = axes[row, 0], axes[row, 1]
        ax_x.set_facecolor("#1e1e1e")
        ax_y.set_facecolor("#1e1e1e")
        by_idx = by_kip[kip_name]
        for j, (li, (tt, xs, ys)) in enumerate(sorted(by_idx.items())):
            col = cmap((j % 10) / max(9.0, float(len(by_idx) - 1)))
            ax_x.plot(tt, xs, label=f"idx {li} x", color=col, linewidth=1.6)
            ax_y.plot(tt, ys, label=f"idx {li} y", color=col, linewidth=1.6, linestyle="--")
        ax_x.set_ylabel("x (crop px)")
        ax_y.set_ylabel("y (crop px)")
        ax_x.set_title(f"{kip_name} — x vs time")
        ax_y.set_title(f"{kip_name} — y vs time")
        ax_x.legend(loc="upper right", fontsize=8, framealpha=0.9)
        ax_y.legend(loc="upper right", fontsize=8, framealpha=0.9)
        for ax in (ax_x, ax_y):
            _style_dark_axes(ax)
        if row == n - 1:
            ax_x.set_xlabel("timestamp (s)")
            ax_y.set_xlabel("timestamp (s)")

    fig.suptitle(
        "Key interest points (2D crop pixels) vs timestamp",
        color="white",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    path_out = out or (json_path.parent / f"{json_path.stem}_kip_vs_time.png")
    fig.savefig(path_out, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return path_out


def plot_kip_angle_timeseries(
    stem_path: Path,
    results: list[dict[str, Any]],
    out: Path | None,
) -> Path:
    """Plot KIP joint angles vs timestamp; save PNG and return output path."""
    by_kip = _kip_angle_series(results)
    if not by_kip:
        raise SystemExit(
            "No key_interest_points_2d with 'angle' in any frame; cannot plot KIP angles."
        )

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=120)
    fig.patch.set_facecolor("#1e1e1e")
    ax.set_facecolor("#1e1e1e")

    cmap = plt.colormaps["tab10"]
    names = sorted(by_kip.keys())
    for j, kip_name in enumerate(names):
        tt, aa = by_kip[kip_name]
        col = cmap((j % 10) / max(9.0, float(len(names) - 1)))
        ax.plot(tt, aa, label=kip_name, color=col, linewidth=1.8, marker="o", markersize=3)

    ax.set_xlabel("timestamp (s)")
    ax.set_ylabel("angle (°)")
    ax.set_title("Key interest points — joint angle vs time")
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    _style_dark_axes(ax)
    fig.suptitle(
        "KIP angles (from biometrics) vs timestamp",
        color="white",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    path_out = out or (stem_path.parent / f"{stem_path.stem}_kip_angle_vs_time.png")
    fig.savefig(path_out, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return path_out


def _plot_kip_angle_timeseries(
    json_path: Path,
    results: list[dict[str, Any]],
    out: Path | None,
) -> Path:
    return plot_kip_angle_timeseries(json_path, results, out)


def _plot_back_timeseries(
    json_path: Path,
    results: list[dict[str, Any]],
    out: Path | None,
) -> Path:
    ts, nv, x_span, y_span, pmx, pmy, arc_len = _back_series(results)
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), dpi=120, sharex=True)
    fig.patch.set_facecolor("#1e1e1e")

    ax0, ax1 = axes
    ax0.set_facecolor("#1e1e1e")
    ax1.set_facecolor("#1e1e1e")

    ax0.plot(ts, nv, color="#ff6699", linewidth=1.8, label="n_vertices (polyline)")
    ax0.set_ylabel("vertex count")
    ax0.set_title("Back shape — polyline vertices vs time")
    ax0_t = ax0.twinx()
    ax0_t.set_facecolor("#1e1e1e")
    ax0_t.plot(
        ts,
        arc_len,
        color="#ffaa00",
        alpha=0.9,
        linewidth=1.5,
        label="polyline length (crop px)",
    )
    ax0_t.plot(ts, x_span, color="#66ccff", alpha=0.85, linewidth=1.4, label="x_span (px)")
    ax0_t.plot(ts, y_span, color="#99ee66", alpha=0.85, linewidth=1.4, label="y_span (px)")
    ax0_t.set_ylabel("px", color="#cccccc")
    ax0_t.tick_params(axis="y", colors="#cccccc")
    ax0_t.spines["right"].set_color("#666666")
    _style_dark_axes(ax0)
    lines0, lab0 = ax0.get_legend_handles_labels()
    lines1, lab1 = ax0_t.get_legend_handles_labels()
    ax0.legend(lines0 + lines1, lab0 + lab1, loc="upper right", facecolor="#2a2a2a", edgecolor="#666666", labelcolor="white")

    ax1.plot(ts, pmx, color="#ffcc33", linewidth=1.6, label="mean polyline x (crop)")
    ax1.plot(ts, pmy, color="#cc9933", linewidth=1.6, linestyle="--", label="mean polyline y (crop)")
    ax1.set_xlabel("timestamp (s)")
    ax1.set_ylabel("pixel")
    ax1.set_title("Back polyline centroid (crop) vs time")
    _style_dark_axes(ax1)
    ax1.legend(loc="upper right")

    fig.suptitle(
        "Back profile vs timestamp (vertices, bbox spans, polyline length; mask pixel count not in JSON)",
        color="#aaaaaa",
        fontsize=10,
        y=1.01,
    )
    fig.tight_layout()
    path_out = out or (json_path.parent / f"{json_path.stem}_back_vs_time.png")
    fig.savefig(path_out, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return path_out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("json_path", type=Path)
    ap.add_argument(
        "--idx",
        type=int,
        default=None,
        help="Frame index (matches top-level 'idx' in each result)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output PNG for single-frame plot (default: next to JSON with derived name)",
    )
    ap.add_argument(
        "--timeseries",
        action="store_true",
        help="Write KIP vs time and back vs time figures",
    )
    ap.add_argument(
        "--out-kip-time",
        type=Path,
        default=None,
        help="Output path for key-interest-point timeseries figure",
    )
    ap.add_argument(
        "--out-back-time",
        type=Path,
        default=None,
        help="Output path for back-metrics timeseries figure",
    )
    ap.add_argument(
        "--out-kip-angle",
        type=Path,
        default=None,
        help="Output path for KIP angle vs timestamp figure (--timeseries)",
    )
    ap.add_argument(
        "--vis-thresh",
        type=float,
        default=0.5,
        help="Landmark visibility threshold for skeleton/keypoints",
    )
    ap.add_argument(
        "--no-labels",
        action="store_true",
        help="Omit landmark index annotations",
    )
    args = ap.parse_args()

    data = _load_results(args.json_path)
    results = data["results"]

    written: list[Path] = []

    if args.timeseries:
        p1 = _plot_kip_timeseries(args.json_path, results, args.out_kip_time)
        p_ang = _plot_kip_angle_timeseries(args.json_path, results, args.out_kip_angle)
        p2 = _plot_back_timeseries(args.json_path, results, args.out_back_time)
        written.extend([p1, p_ang, p2])

    do_single = (not args.timeseries) or (args.idx is not None)
    if do_single:
        _, frame = _pick_frame(results, args.idx)

        seg = frame["segmentation_result"]
        bio = frame.get("biometrics") or {}
        pose = frame["pose_estimation_result"]
        cw = int(seg["mask_width"])
        ch = int(seg["mask_height"])

        lm_groups = pose.get("pose_landmarks") or []
        if not lm_groups or not lm_groups[0]:
            if not args.timeseries:
                raise SystemExit("Missing pose_landmarks")
        else:
            landmarks = lm_groups[0]

            pts_xy, good = landmarks_to_px(
                landmarks, cw, ch, args.vis_thresh
            )

            back = bio.get("back_shape")
            poly_x = poly_y = None
            if back and back.get("polyline_crop_yx"):
                arr = np.asarray(back["polyline_crop_yx"], dtype=np.float64)
                poly_y = arr[:, 0]
                poly_x = arr[:, 1]

            fig, ax = plt.subplots(figsize=(8, 10), dpi=120)
            ax.set_facecolor("#1e1e1e")
            fig.patch.set_facecolor("#1e1e1e")

            for a, b in POSE_SKELETON_EDGES:
                if not good[a] or not good[b]:
                    continue
                ax.plot(
                    [pts_xy[a, 0], pts_xy[b, 0]],
                    [pts_xy[a, 1], pts_xy[b, 1]],
                    color="#4a90d9",
                    linewidth=2,
                    alpha=0.85,
                )

            vis_pts = pts_xy[good]
            ax.scatter(
                vis_pts[:, 0],
                vis_pts[:, 1],
                c="#ffcc33",
                s=28,
                zorder=5,
                edgecolors="#222222",
                linewidths=0.4,
            )

            if not args.no_labels:
                for i in range(33):
                    if not good[i]:
                        continue
                    ax.annotate(
                        str(i),
                        (pts_xy[i, 0], pts_xy[i, 1]),
                        fontsize=5,
                        color="#dddddd",
                        alpha=0.75,
                    )

            if poly_x is not None and poly_y is not None and len(poly_x) > 0:
                ax.plot(
                    poly_x,
                    poly_y,
                    color="#ff3366",
                    linewidth=2.5,
                    label="back polyline (crop)",
                )
                ax.scatter(poly_x, poly_y, c="#ff6666", s=14, zorder=6)

            ax.set_xlim(0, cw)
            ax.set_ylim(ch, 0)
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True, color="#444444", linestyle="--", alpha=0.35)
            ax.set_xlabel("x (crop px)", color="#cccccc")
            ax.set_ylabel("y (crop px)", color="#cccccc")
            fidx = frame.get("idx")
            title = f"frame idx={fidx}  back_polyline={'yes' if poly_x is not None else 'no'}"
            if back and isinstance(back, dict):
                title += f"  ref={back.get('reference_segment', '')}"
            ax.set_title(title, color="white", fontsize=11)
            ax.tick_params(colors="#cccccc")
            for spine in ax.spines.values():
                spine.set_color("#666666")
            if poly_x is not None:
                ax.legend(
                    loc="upper right",
                    facecolor="#2a2a2a",
                    edgecolor="#666666",
                    labelcolor="white",
                )

            out = args.out
            if out is None:
                out = (
                    args.json_path.parent
                    / f"{args.json_path.stem}_keypoints_back_idx{fidx}.png"
                )

            fig.tight_layout()
            fig.savefig(out, facecolor=fig.get_facecolor())
            plt.close(fig)
            written.append(out)
    if not written:
        raise SystemExit(
            "Nothing to write: use --timeseries and/or --idx (default frame uses first back_shape)."
        )

    for p in written:
        print(p)


if __name__ == "__main__":
    main()
