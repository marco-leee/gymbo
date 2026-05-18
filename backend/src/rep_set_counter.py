#!/usr/bin/env python3
"""Offline rep / set counting from pipeline `overall_results.json`.

Loads pose_landmarks per frame, recomputes the exercise primary joint angle (squat knee,
lunge front knee, deadlift hip hinge), smooths it, then **segments the timeline into sets**
using adaptive motion activity (rolling angle variability vs robust baseline). **Reps are
counted only inside each set** via hysteresis on the primary angle.

Limitations: long static holds mid-set can resemble rest and split a set; very slow
eccentrics reduce activity and may fragment segmentation. Tune ``activity_k`` / angles if needed.
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict, dataclass
from math import ceil
from pathlib import Path
from statistics import mean, median
from types import SimpleNamespace

from models.exercise import ExerciseType
from models.overall_results import OverallResults
from models.rep_set_count import CountedSet, RepSetCountResult
from rep_counter.registry import get_rep_spec
from utils.video import CameraView


@dataclass(frozen=True)
class RepThresholds:
    angle_high: float
    angle_low: float
    smoothing_window: int = 5
    activity_k: float = 3.5
    min_set_duration_s: float = 1.0
    merge_gap_s: float = 0.3
    rep_spacing_frac: float = 0.35


DEFAULT_THRESHOLDS: dict[ExerciseType, RepThresholds] = {
    ExerciseType.SQUAT: RepThresholds(angle_high=148.0, angle_low=105.0),
    ExerciseType.LUNGE: RepThresholds(angle_high=148.0, angle_low=105.0),
    ExerciseType.DEADLIFT: RepThresholds(angle_high=158.0, angle_low=125.0),
}


def landmarks_from_pose_dict(pose_landmarks: object) -> list[SimpleNamespace] | None:
    if not pose_landmarks or not isinstance(pose_landmarks, list):
        return None
    group = pose_landmarks[0]
    if not group:
        return None
    return [SimpleNamespace(**lm) for lm in group]


def extract_angle_series(
    data: OverallResults,
    exercise_type: ExerciseType,
    camera_view: CameraView,
    video_width: int,
    video_height: int,
) -> list[tuple[float, float]]:
    spec = get_rep_spec(exercise_type)
    primary = spec.primary_rep_angle_key
    processor = spec.processor
    series: list[tuple[float, float]] = []
    for row in data.results:
        pose = row.pose_estimation_result.get("pose_landmarks")
        lm = landmarks_from_pose_dict(pose)
        if lm is None:
            continue
        kips = processor.get_2d_key_points(lm, camera_view, video_height, video_width)
        kip = kips.get(primary)
        if kip is None:
            continue
        series.append((row.timestamp, float(kip.angle)))
    return series


def extract_angle_series_from_biometrics(
    data: OverallResults,
    exercise_type: ExerciseType,
) -> list[tuple[float, float]]:
    """Primary joint angle over time from stored ``biometrics`` (no raw pose)."""
    spec = get_rep_spec(exercise_type)
    primary = spec.primary_rep_angle_key
    series: list[tuple[float, float]] = []
    for row in data.results:
        bio = row.biometrics
        if not bio or not isinstance(bio, dict):
            continue
        kips = bio.get("key_interest_points_2d")
        if not kips or not isinstance(kips, dict):
            continue
        kip = kips.get(primary)
        if not kip or not isinstance(kip, dict):
            continue
        ang = kip.get("angle")
        if ang is None:
            continue
        series.append((row.timestamp, float(ang)))
    return series


def smooth_series(
    series: list[tuple[float, float]], window: int
) -> list[tuple[float, float]]:
    if not series or window <= 1:
        return series
    w = window if window % 2 == 1 else window + 1
    half = w // 2
    out: list[tuple[float, float]] = []
    for i in range(len(series)):
        lo = max(0, i - half)
        hi = min(len(series), i + half + 1)
        avg = mean(series[j][1] for j in range(lo, hi))
        out.append((series[i][0], avg))
    return out


def median_sample_dt(
    series: list[tuple[float, float]], fps_fallback: float | None
) -> float:
    if len(series) < 2:
        if fps_fallback and fps_fallback > 0:
            return 1.0 / fps_fallback
        return 1.0 / 30.0
    dts = [
        series[i][0] - series[i - 1][0]
        for i in range(1, len(series))
        if series[i][0] > series[i - 1][0]
    ]
    if not dts:
        if fps_fallback and fps_fallback > 0:
            return 1.0 / fps_fallback
        return 1.0 / 30.0
    return float(median(dts))


def _scaled_mad(values: list[float], med: float) -> float:
    devs = [abs(v - med) for v in values]
    m = median(devs)
    return float(m * 1.4826) if m > 0 else 0.0


def rolling_std_angles(angles: list[float], half_win: int) -> list[float]:
    n = len(angles)
    out: list[float] = []
    for i in range(n):
        lo = max(0, i - half_win)
        hi = min(n, i + half_win + 1)
        chunk = angles[lo:hi]
        if len(chunk) < 2:
            out.append(0.0)
        else:
            out.append(statistics.pstdev(chunk))
    return out


def runs_from_mask(active: list[bool]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    i = 0
    n = len(active)
    while i < n:
        while i < n and not active[i]:
            i += 1
        if i >= n:
            break
        j = i
        while j < n and active[j]:
            j += 1
        runs.append((i, j))
        i = j
    return runs


def merge_adjacent_runs(
    runs: list[tuple[int, int]], max_gap_samples: int
) -> list[tuple[int, int]]:
    if not runs:
        return []
    merged: list[list[int]] = [list(runs[0])]
    for s, e in runs[1:]:
        _, pe = merged[-1]
        if s - pe <= max_gap_samples:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return [(m[0], m[1]) for m in merged]


def segment_sets_activity(
    smoothed: list[tuple[float, float]],
    *,
    activity_k: float,
    min_set_duration_s: float,
    merge_gap_s: float,
    fps_fallback: float | None,
) -> list[tuple[int, int]]:
    """Return half-open index ranges into ``smoothed`` that form one working set each."""
    n = len(smoothed)
    if n == 0:
        return []

    dt_med = median_sample_dt(smoothed, fps_fallback)
    angles = [s[1] for s in smoothed]

    win = max(3, int(round(0.5 / dt_med)))
    if win % 2 == 0:
        win += 1
    half_win = win // 2

    activity = rolling_std_angles(angles, half_win)
    med_act = median(activity)
    mad = _scaled_mad(activity, med_act)
    thresh = med_act + activity_k * mad if mad > 1e-12 else med_act + 1e-9
    active_mask = [a > thresh for a in activity]

    if not any(active_mask):
        return [(0, n)]

    runs = runs_from_mask(active_mask)
    merge_gap_samples = max(1, int(round(merge_gap_s / dt_med)))
    runs = merge_adjacent_runs(runs, merge_gap_samples)

    min_samples = max(1, ceil(min_set_duration_s / dt_med))
    filtered = [(s, e) for s, e in runs if e - s >= min_samples]

    if not filtered:
        return [(0, n)]

    return filtered


def estimate_rep_spacing_samples(
    segment: list[tuple[float, float]],
    angle_low: float,
    dt_med: float,
) -> int:
    """Typical sample spacing between descent phases in this segment (for debouncing)."""
    angles = [a for _, a in segment]
    if len(angles) < 4:
        return max(3, int(round(0.4 / dt_med)))

    crossings: list[int] = []
    for i in range(1, len(angles)):
        if angles[i] <= angle_low < angles[i - 1]:
            crossings.append(i)
    if len(crossings) >= 2:
        gaps = [crossings[j] - crossings[j - 1] for j in range(1, len(crossings))]
        return max(3, int(median(gaps)))

    mins: list[int] = []
    for i in range(1, len(angles) - 1):
        if (
            angles[i] <= angle_low
            and angles[i] <= angles[i - 1]
            and angles[i] <= angles[i + 1]
        ):
            mins.append(i)
    if len(mins) >= 2:
        gaps = [mins[j] - mins[j - 1] for j in range(1, len(mins))]
        return max(3, int(median(gaps)))

    return max(3, int(round(0.4 / dt_med)))


def count_reps_in_segment(
    segment: list[tuple[float, float]],
    angle_high: float,
    angle_low: float,
    min_idx_gap: int,
) -> list[float]:
    """Timestamps when the athlete completes a rep inside this segment (index debouncing)."""
    rep_times: list[float] = []
    in_rep = False
    armed = True
    last_completion_idx = -(10**9)

    for idx, (t, ang) in enumerate(segment):
        if armed and ang <= angle_low:
            in_rep = True
            armed = False
        elif in_rep and ang >= angle_high:
            if idx - last_completion_idx >= min_idx_gap:
                rep_times.append(t)
                last_completion_idx = idx
            in_rep = False
            armed = True

    return rep_times


class SetRepCounter:
    """Segments timeline by motion activity, then counts reps per segment."""

    def thresholds_for(self, exercise_type: ExerciseType) -> RepThresholds:
        return DEFAULT_THRESHOLDS[exercise_type]

    def analyze(
        self,
        data: OverallResults,
        *,
        exercise_type: ExerciseType | None = None,
        camera_view: CameraView | None = None,
        video_width: int | None = None,
        video_height: int | None = None,
        fps: float | None = None,
        thresholds: RepThresholds | None = None,
    ) -> RepSetCountResult:
        et_raw = exercise_type.value if exercise_type is not None else data.exercise_type
        if not et_raw:
            raise ValueError(
                "exercise_type missing: add pipeline metadata or pass ExerciseType explicitly"
            )
        resolved_et = (
            exercise_type
            if exercise_type is not None
            else ExerciseType.from_string(et_raw)
        )

        cam_raw = camera_view.value if camera_view is not None else data.camera_view
        if not cam_raw:
            raise ValueError(
                "camera_view missing: add pipeline metadata or pass CameraView explicitly"
            )
        resolved_cam = (
            camera_view
            if camera_view is not None
            else CameraView.from_string(cam_raw)
        )

        w = video_width if video_width is not None else data.video_width
        h = video_height if video_height is not None else data.video_height
        if w is None or h is None:
            raise ValueError(
                "video dimensions missing: add pipeline metadata or pass video_width / video_height"
            )

        thr = thresholds or self.thresholds_for(resolved_et)

        fps_fallback = fps if fps is not None else (float(data.fps) if data.fps else None)

        raw_series = extract_angle_series(
            data, resolved_et, resolved_cam, int(w), int(h)
        )
        smoothed = smooth_series(raw_series, thr.smoothing_window)

        return self._rep_set_result_from_smoothed(
            smoothed,
            resolved_et=resolved_et,
            resolved_cam=resolved_cam,
            fps_fallback=fps_fallback,
            thr=thr,
        )

    def analyze_from_biometrics(
        self,
        data: OverallResults,
        *,
        exercise_type: ExerciseType | None = None,
        camera_view: CameraView | None = None,
        fps: float | None = None,
        thresholds: RepThresholds | None = None,
    ) -> RepSetCountResult:
        """Like :meth:`analyze` but reads angles from ``OverallResult.biometrics`` only."""
        et_raw = exercise_type.value if exercise_type is not None else data.exercise_type
        if not et_raw:
            raise ValueError(
                "exercise_type missing: add pipeline metadata or pass ExerciseType explicitly"
            )
        resolved_et = (
            exercise_type
            if exercise_type is not None
            else ExerciseType.from_string(et_raw)
        )

        cam_raw = camera_view.value if camera_view is not None else data.camera_view
        if not cam_raw:
            raise ValueError(
                "camera_view missing: add pipeline metadata or pass CameraView explicitly"
            )
        resolved_cam = (
            camera_view
            if camera_view is not None
            else CameraView.from_string(cam_raw)
        )

        thr = thresholds or self.thresholds_for(resolved_et)
        fps_fallback = fps if fps is not None else (float(data.fps) if data.fps else None)

        raw_series = extract_angle_series_from_biometrics(data, resolved_et)
        smoothed = smooth_series(raw_series, thr.smoothing_window)

        return self._rep_set_result_from_smoothed(
            smoothed,
            resolved_et=resolved_et,
            resolved_cam=resolved_cam,
            fps_fallback=fps_fallback,
            thr=thr,
        )

    def _rep_set_result_from_smoothed(
        self,
        smoothed: list[tuple[float, float]],
        *,
        resolved_et: ExerciseType,
        resolved_cam: CameraView,
        fps_fallback: float | None,
        thr: RepThresholds,
    ) -> RepSetCountResult:
        set_ranges = segment_sets_activity(
            smoothed,
            activity_k=thr.activity_k,
            min_set_duration_s=thr.min_set_duration_s,
            merge_gap_s=thr.merge_gap_s,
            fps_fallback=fps_fallback,
        )

        dt_med = median_sample_dt(smoothed, fps_fallback)

        counted_sets: list[CountedSet] = []
        all_rep_times: list[float] = []

        for set_idx, (i0, i1) in enumerate(set_ranges, start=1):
            segment = smoothed[i0:i1]
            spacing = estimate_rep_spacing_samples(segment, thr.angle_low, dt_med)
            min_idx_gap = max(3, int(round(thr.rep_spacing_frac * spacing)))

            reps_t = count_reps_in_segment(
                segment,
                thr.angle_high,
                thr.angle_low,
                min_idx_gap,
            )
            all_rep_times.extend(reps_t)

            t_start = segment[0][0]
            t_end = segment[-1][0]
            counted_sets.append(
                CountedSet(
                    idx=set_idx,
                    reps=len(reps_t),
                    start_timestamp=t_start,
                    end_timestamp=t_end,
                    rep_timestamps=reps_t,
                )
            )

        all_rep_times.sort()

        return RepSetCountResult(
            exercise_type=resolved_et.value,
            camera_view=resolved_cam.value,
            total_reps=len(all_rep_times),
            rep_timestamps=all_rep_times,
            sets=counted_sets,
        )


def _threshold_overrides_from_args(
    args: argparse.Namespace, resolved_et: ExerciseType
) -> RepThresholds | None:
    if (
        args.angle_high is None
        and args.angle_low is None
        and args.smoothing_window is None
        and args.activity_k is None
        and args.min_set_duration is None
        and args.merge_gap is None
        and args.rep_spacing_frac is None
    ):
        return None

    base = DEFAULT_THRESHOLDS[resolved_et]
    return RepThresholds(
        angle_high=float(args.angle_high)
        if args.angle_high is not None
        else base.angle_high,
        angle_low=float(args.angle_low)
        if args.angle_low is not None
        else base.angle_low,
        smoothing_window=int(args.smoothing_window)
        if args.smoothing_window is not None
        else base.smoothing_window,
        activity_k=float(args.activity_k)
        if args.activity_k is not None
        else base.activity_k,
        min_set_duration_s=float(args.min_set_duration)
        if args.min_set_duration is not None
        else base.min_set_duration_s,
        merge_gap_s=float(args.merge_gap)
        if args.merge_gap is not None
        else base.merge_gap_s,
        rep_spacing_frac=float(args.rep_spacing_frac)
        if args.rep_spacing_frac is not None
        else base.rep_spacing_frac,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-path",
        default="overall_results.json",
        help="Pipeline JSON path",
    )
    parser.add_argument(
        "--exercise-type",
        help="Override ExerciseType when absent from JSON (SQUAT, LUNGE, DEADLIFT)",
    )
    parser.add_argument("--camera-view", help="Override LEFT / RIGHT when absent")
    parser.add_argument("--video-width", type=int, help="Override width when absent")
    parser.add_argument("--video-height", type=int, help="Override height when absent")
    parser.add_argument(
        "--fps",
        type=float,
        help="Fallback frame spacing when timestamps are sparse (uses JSON fps if omitted)",
    )
    parser.add_argument("--angle-high", type=float)
    parser.add_argument("--angle-low", type=float)
    parser.add_argument("--smoothing-window", type=int)
    parser.add_argument("--activity-k", type=float, dest="activity_k")
    parser.add_argument("--min-set-duration", type=float, dest="min_set_duration")
    parser.add_argument("--merge-gap", type=float, dest="merge_gap")
    parser.add_argument("--rep-spacing-frac", type=float, dest="rep_spacing_frac")
    args = parser.parse_args()

    path = Path(args.json_path)
    data = OverallResults.model_validate_json(path.read_text())

    et_override = (
        ExerciseType.from_string(args.exercise_type) if args.exercise_type else None
    )
    cam_override = (
        CameraView.from_string(args.camera_view) if args.camera_view else None
    )

    resolved_et = et_override or (
        ExerciseType.from_string(data.exercise_type) if data.exercise_type else None
    )
    if resolved_et is None:
        parser.error(
            "exercise_type missing: set pipeline metadata or pass --exercise-type"
        )

    thr = _threshold_overrides_from_args(args, resolved_et)

    counter = SetRepCounter()
    result = counter.analyze(
        data,
        exercise_type=et_override,
        camera_view=cam_override,
        video_width=args.video_width,
        video_height=args.video_height,
        fps=args.fps,
        thresholds=thr,
    )

    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
