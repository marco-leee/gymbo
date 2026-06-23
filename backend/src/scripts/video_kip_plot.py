#!/usr/bin/env python3
"""Run pose estimation on a video, compute KIPs, and save a KIP angle vs time plot.

Example::

  cd backend && uv run python src/scripts/video_kip_plot.py src/test.mp4
  cd backend && uv run python src/scripts/video_kip_plot.py --video src/test.mp4 --out /tmp/kips.png
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_SCRIPTS = _SRC / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from analysis_pipeline import AnalysisPipeline  # noqa: E402
from models.exercise import ExerciseType  # noqa: E402
from plot_overall_results_keypoints_back import plot_kip_angle_timeseries  # noqa: E402
from session_context import InputSource, SessionContext  # noqa: E402
from utils.video import CameraView  # noqa: E402
from video_queue_worker import yolo26_weight_paths  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("video_kip_plot")


def _resolve_video_path(video_arg: Path) -> Path:
    if video_arg.is_file():
        return video_arg.resolve()
    alt = _SRC / video_arg
    if alt.is_file():
        return alt.resolve()
    raise SystemExit(f"Video not found: {video_arg}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pose estimation + KIP biometrics → KIP angle vs time PNG."
    )
    parser.add_argument(
        "video",
        nargs="?",
        type=Path,
        default=None,
        help="Input video path",
    )
    parser.add_argument(
        "--video",
        type=Path,
        default=None,
        dest="video_flag",
        help="Input video path (alternative to positional)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output PNG (default: {video_stem}_kip_angle_vs_time.png next to input)",
    )
    parser.add_argument(
        "--exercise-type",
        default="SQUAT",
        help="Exercise type for KIP selection (SQUAT, LUNGE, DEADLIFT)",
    )
    parser.add_argument(
        "--camera-view",
        default="RIGHT",
        help="Camera side (LEFT or RIGHT)",
    )
    parser.add_argument(
        "--model-size",
        default="n",
        choices=("n", "s", "m", "l", "x"),
        help="YOLO26 model size (default: n)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.8,
        help="Minimum person confidence threshold",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional OverallResults JSON output for debugging",
    )
    args = parser.parse_args()

    video_arg = args.video_flag or args.video
    if video_arg is None:
        parser.error("video path is required (positional or --video)")

    video_path = _resolve_video_path(video_arg)
    camera_view = CameraView.from_string(args.camera_view)
    exercise_type = ExerciseType.from_string(args.exercise_type)
    detect, seg, pose = yolo26_weight_paths(_SRC / "pose_models", args.model_size)

    ctx = SessionContext(
        user_id=None,
        exercise_type=exercise_type,
        camera_view=camera_view,
        input_source=InputSource.VIDEO_FILE,
        video_path=str(video_path),
        conf_threshold=args.conf,
        yolo_detect_weights=detect,
        yolo_seg_weights=seg,
        yolo_pose_weights=pose,
    )

    log.info(
        "Running pipeline video=%s exercise=%s camera=%s model_size=%s",
        video_path,
        exercise_type.value,
        camera_view.value,
        args.model_size,
    )
    overall, stats = AnalysisPipeline(ctx).run(output_json_path=args.output_json)
    log.info("Pipeline %s", stats.summary())

    results = [r.model_dump(mode="json") for r in overall.results]
    out_path = args.out or (
        video_path.parent / f"{video_path.stem}_kip_angle_vs_time.png"
    )
    plot_path = plot_kip_angle_timeseries(video_path, results, out_path)

    print(f"Wrote KIP angle plot: {plot_path}")
    print(
        f"frames_decoded={stats.frames_decoded} "
        f"frames_ok={stats.frames_ok} "
        f"status_counts={stats.status_counts}"
    )
    if args.output_json:
        print(f"Wrote JSON: {args.output_json}")


if __name__ == "__main__":
    main()
