from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from ultralytics import YOLO

from models.exercise import ExerciseType
from models.overall_results import OverallResult, OverallResults
from pipeline.biometrics import compute_frame_biometrics
from pipeline.from_record import record_to_frame_state
from pipeline.overlays import render_overlays
from pipeline.runner import PerceptionRunConfig, perceive_frame_pipeline
from pipeline.frame_state import FramePerceptionState
from pipeline.run_stats import PipelineRunStats
from session_context import InputSource, SessionContext
from utils import Video
from utils.video import CameraView

log = logging.getLogger("analysis_pipeline")

_DEBUG_FRAME_INTERVAL = 30

if TYPE_CHECKING:
    from database.mongodb.ingest import MongodbPersistConfig
    from pymongo.database import Database

__all__ = [
    "AnalysisPipeline",
    "FramePerceptionState",
    "infer_overall_result_from_bgr",
]


def infer_overall_result_from_bgr(
    frame_bgr: np.ndarray,
    *,
    idx: int,
    timestamp: float,
    conf_threshold: float,
    object_detector: YOLO,
    segmenter: YOLO,
    pose_model: YOLO,
    exercise_type: ExerciseType = ExerciseType.SQUAT,
    camera_view: CameraView = CameraView.RIGHT,
) -> OverallResult | None:
    """Run single-frame detect → pose → seg (same as :meth:`AnalysisPipeline._perceive_frame`)."""
    ctx = SessionContext(
        user_id=None,
        exercise_type=exercise_type,
        camera_view=camera_view,
        input_source=InputSource.VIDEO_FILE,
        video_path=None,
        conf_threshold=conf_threshold,
    )
    pipeline = AnalysisPipeline(ctx)
    state = pipeline._perceive_frame(
        frame_bgr,
        idx,
        timestamp,
        object_detector=object_detector,
        segmenter=segmenter,
        pose_model=pose_model,
    )
    return state.overall_result


class AnalysisPipeline:
    """End-to-end path from session context → perceptions → (future) measurements & feedback."""

    def __init__(self, context: SessionContext):
        self.context = context

    def _perceive_frame(
        self,
        frame: np.ndarray,
        count: int,
        timestamp: float,
        *,
        object_detector: YOLO,
        segmenter: YOLO,
        pose_model: YOLO,
    ) -> FramePerceptionState:
        ctx = self.context
        config = PerceptionRunConfig(
            conf_threshold=ctx.conf_threshold,
            yolo_detect_weights=ctx.yolo_detect_weights,
            yolo_pose_weights=ctx.yolo_pose_weights,
            yolo_seg_weights=ctx.yolo_seg_weights,
        )
        rec = perceive_frame_pipeline(
            frame,
            idx=count,
            timestamp=timestamp,
            object_detector=object_detector,
            pose_model=pose_model,
            segmenter=segmenter,
            config=config,
        )
        return record_to_frame_state(rec, frame)

    def run_with_video_overlays(
        self,
        *,
        mp4_output: str | Path,
        output_json_path: str | Path | None = None,
        mongodb_persist: MongodbPersistConfig | None = None,
        mongodb_database: Database | None = None,
    ) -> tuple[OverallResults, PipelineRunStats]:
        """MP4 writer path: segmentation tint + pose skeleton + person bbox."""
        ctx = self.context

        if ctx.input_source is InputSource.LIVE_STREAM:
            raise NotImplementedError("Live stream input is not wired yet.")
        if not ctx.video_path:
            raise ValueError("video_path is required when input_source is VIDEO_FILE.")

        video = Video(
            ctx.video_path,
            ctx.camera_view,
            expected_display_size=ctx.expected_display_size,
        )
        mp4_path = Path(mp4_output)
        mp4_path.parent.mkdir(parents=True, exist_ok=True)
        if output_json_path:
            Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)

        log.info(
            "Video input path=%s width=%s height=%s fps=%s total_frames=%s duration_sec=%.2f",
            ctx.video_path,
            video.width,
            video.height,
            video.fps,
            video.total_frames,
            video.duration,
        )

        overall_results = OverallResults(
            results=[],
            camera_view=ctx.camera_view.value,
            exercise_type=ctx.exercise_type.value,
            video_width=video.width,
            video_height=video.height,
            fps=video.fps,
        )

        object_detector = YOLO(ctx.yolo_detect_weights)
        segmenter = YOLO(ctx.yolo_seg_weights)
        pose_model = YOLO(ctx.yolo_pose_weights)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            str(mp4_path),
            fourcc,
            max(video.fps, 1),
            (video.width, video.height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Failed to open VideoWriter for {mp4_path}")

        status_counts: dict[str, int] = defaultdict(int)
        frames_decoded = 0
        frames_written = 0
        frames_ok = 0

        try:
            for count, ts, frame in video.get_frames():
                frames_decoded += 1
                st = self._perceive_frame(
                    frame,
                    count,
                    ts,
                    object_detector=object_detector,
                    segmenter=segmenter,
                    pose_model=pose_model,
                )
                status = st.perception_record.status.value
                status_counts[status] += 1

                if count % _DEBUG_FRAME_INTERVAL == 0:
                    log.debug(
                        "frame idx=%s timestamp=%.3f status=%s",
                        count,
                        ts,
                        status,
                    )

                if st.overall_result is not None:
                    frames_ok += 1
                    overall_results.results.append(st.overall_result)

                    bio = compute_frame_biometrics(
                        st,
                        exercise_type=ctx.exercise_type,
                        camera_view=ctx.camera_view,
                    )
                    if bio is not None:
                        st.overall_result.biometrics = bio.model_dump(mode="json")
                else:
                    overall_results.results.append(
                        OverallResult(
                            idx=count,
                            timestamp=ts,
                            pose_estimation_result={},
                            segmentation_result={},
                            biometrics=None,
                        )
                    )

                # Always write a frame: overlays when detected, otherwise original
                vis = render_overlays(frame, st.perception_record)
                writer.write(vis)
                frames_written += 1
        finally:
            writer.release()

        stats = PipelineRunStats(
            frames_decoded=frames_decoded,
            frames_written=frames_written,
            frames_ok=frames_ok,
            status_counts=dict(status_counts),
        )
        log.info("Pipeline finished %s", stats.summary())

        if output_json_path:
            Path(output_json_path).write_text(
                overall_results.model_dump_json(indent=2),
                encoding="utf-8",
            )

        if mongodb_persist is not None:
            from database.mongodb.client import get_mongo_database
            from database.mongodb.ingest import persist_pipeline_output

            db = get_mongo_database() if mongodb_database is None else mongodb_database
            persist_pipeline_output(
                overall_results=overall_results,
                context=ctx,
                video=video,
                original_video_uri=str(ctx.video_path),
                processed_video_uri=str(mp4_path),
                config=mongodb_persist,
                database=db,
            )

        return overall_results, stats
