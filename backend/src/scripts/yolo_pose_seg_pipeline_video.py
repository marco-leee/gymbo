#!/usr/bin/env python3
"""Annotated MP4 + ``OverallResults`` JSON via :class:`~analysis_pipeline.AnalysisPipeline`.

Delegates perception + overlays to ``AnalysisPipeline.run_with_video_overlays`` so JSON
matches ``pipeline.py`` (``rep-set-counter.py``, etc.).

Example::

  cd backend && uv run python src/scripts/yolo_pose_seg_pipeline_video.py \\
    --video src/lunges.MOV --output src/yolo_pose_seg_overlay.mp4 \\
    --output-json src/overall_results_yolo_od.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from analysis_pipeline import AnalysisPipeline  # noqa: E402
from database.mongodb.ingest import MongodbPersistConfig  # noqa: E402
from models.exercise import ExerciseType  # noqa: E402
from session_context import InputSource, SessionContext  # noqa: E402
from utils.video import CameraView  # noqa: E402
from bson import ObjectId  # noqa: E402


def _resolve_video_path(video_arg: Path) -> Path:
    if video_arg.is_file():
        return video_arg
    alt = _SRC / video_arg
    if alt.is_file():
        return alt
    raise SystemExit(f"Video not found: {video_arg}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="YOLO detect + YOLO pose JSON + YOLO seg + MP4 overlay → JSON (OverallResults)."
    )
    parser.add_argument(
        "--video",
        type=Path,
        default=Path("test-videos/squat-right-1.mp4"),
        help="Input video",
    )
    parser.add_argument(
        "--camera-view",
        default="RIGHT",
        help="Camera side (LEFT or RIGHT)",
    )
    parser.add_argument(
        "--exercise-type",
        default="SQUAT",
        help="Stored in JSON like pipeline.py (SQUAT, LUNGE, DEADLIFT)",
    )
    parser.add_argument(
        "--detect-weights",
        type=Path,
        default=_SRC / "pose_models" / "yolo26n.pt",
        help="YOLO detection checkpoint (person box), same role as pipeline.py",
    )
    parser.add_argument(
        "--pose-weights",
        type=Path,
        default=_SRC / "pose_models" / "yolo26n-pose.pt",
        help="YOLO pose checkpoint (JSON pose_landmarks + skeleton overlay)",
    )
    parser.add_argument(
        "--seg-weights",
        type=Path,
        default=_SRC / "pose_models" / "yolo26n-seg.pt",
        help="YOLO segmentation checkpoint",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_SRC / "squat-left-overlay.mp4",
        help="Output MP4",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=_SRC / "overall_results_yolo_od.json",
        help="Output JSON (OverallResults, same shape as pipeline.py)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.5,
        help="Minimum person confidence (same as pipeline.py)",
    )
    args = parser.parse_args()

    video_path = _resolve_video_path(args.video)
    camera_view = CameraView.from_string(args.camera_view)
    exercise_type = ExerciseType.from_string(args.exercise_type)

    ctx = SessionContext(
        user_id=None,
        exercise_type=exercise_type,
        camera_view=camera_view,
        input_source=InputSource.VIDEO_FILE,
        video_path=str(video_path),
        stream_url=None,
        conf_threshold=args.conf,
        yolo_detect_weights=str(args.detect_weights),
        yolo_seg_weights=str(args.seg_weights),
        yolo_pose_weights=str(args.pose_weights),
    )

    pipe = AnalysisPipeline(ctx)
    overall = pipe.run_with_video_overlays(
        mp4_output=args.output,
        output_json_path=args.output_json,
        mongodb_persist=MongodbPersistConfig(
            exercise_id=str(ObjectId()),
            set_index=0,
            compute_rep_summary=True,
            use_transactions=True,
            ensure_indexes=True,
        ),
    )

    cap = cv2.VideoCapture(str(video_path))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    print(f"Wrote {n_frames} frames to {args.output}")
    print(f"Wrote {len(overall.results)} records to {args.output_json}")


if __name__ == "__main__":
    main()
