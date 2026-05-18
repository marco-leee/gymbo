"""Persist pipeline outputs (biometrics only) to MongoDB."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bson import ObjectId
from pymongo.database import Database

from database.mongodb.client import get_mongo_database
from database.mongodb.entities import (
    ExerciseSetEntity,
    RepSetSummary,
    SessionMetadata,
    SetBiometricFrameEntity,
    VideoMetadata,
    rep_set_count_result_to_summary,
)
from database.mongodb.repositories.mongo import (
    MongoExerciseSetRepository,
    ensure_mongodb_indexes,
)
from models.exercise import ExerciseType
from models.overall_results import OverallResults
from pipeline.biometrics import FrameBiometricsResult
from rep_set_counter import SetRepCounter
from session_context import InputSource, SessionContext
from utils.video import CameraView, Video


@dataclass
class MongodbPersistConfig:
    """Options when saving one pipeline run as a single exercise set."""

    exercise_id: str
    set_index: int = 0
    compute_rep_summary: bool = True
    use_transactions: bool | None = None
    ensure_indexes: bool = True


def _session_metadata_from_context(ctx: SessionContext) -> SessionMetadata:
    return SessionMetadata(
        user_id=ctx.user_id,
        exercise_type=ctx.exercise_type.value,
        camera_view=ctx.camera_view.value,
        input_source=ctx.input_source.value,
        planned_sets=ctx.planned_sets,
        target_reps_per_set=ctx.target_reps_per_set,
        conf_threshold=ctx.conf_threshold,
        yolo_detect_weights=ctx.yolo_detect_weights,
        yolo_seg_weights=ctx.yolo_seg_weights,
        yolo_pose_weights=ctx.yolo_pose_weights,
    )


def _video_metadata_from_sources(
    video: Video,
    overall: OverallResults,
    *,
    total_frames_override: int | None = None,
) -> VideoMetadata:
    fps = overall.fps if overall.fps is not None else video.fps
    vw = overall.video_width if overall.video_width is not None else video.width
    vh = overall.video_height if overall.video_height is not None else video.height
    tf = total_frames_override
    if tf is None:
        tf = video.total_frames if video.total_frames else None
    duration: float | None = None
    if tf is not None and video.fps:
        duration = float(tf) / float(max(video.fps, 1))
    return VideoMetadata(
        fps=fps,
        video_width=vw,
        video_height=vh,
        total_frames=tf,
        duration_sec=duration,
    )


def overall_results_to_biometric_frames(
    overall: OverallResults,
) -> list[SetBiometricFrameEntity]:
    out: list[SetBiometricFrameEntity] = []
    for row in overall.results:
        if row.biometrics is None:
            continue
        bio = FrameBiometricsResult.model_validate(row.biometrics)
        out.append(
            SetBiometricFrameEntity(
                idx=row.idx,
                timestamp=row.timestamp,
                biometrics=bio,
            )
        )
    return out


def _maybe_rep_summary(overall: OverallResults, *, compute: bool) -> RepSetSummary | None:
    if not compute:
        return None
    try:
        raw = SetRepCounter().analyze_from_biometrics(overall)
        return rep_set_count_result_to_summary(raw)
    except ValueError:
        return None


def persist_pipeline_output(
    *,
    overall_results: OverallResults,
    context: SessionContext,
    video: Video | None,
    original_video_uri: str,
    processed_video_uri: str,
    config: MongodbPersistConfig,
    database: Database | None = None,
    total_frames_override: int | None = None,
    video_metadata_override: VideoMetadata | None = None,
) -> ObjectId:
    """Save one recording: exercise set header + per-frame biometrics (no perception blobs)."""
    db = get_mongo_database() if database is None else database
    if config.ensure_indexes:
        ensure_mongodb_indexes(db)

    rep_summary = _maybe_rep_summary(
        overall_results, compute=config.compute_rep_summary
    )
    if video_metadata_override is not None:
        vmeta = video_metadata_override
    else:
        if video is None:
            raise ValueError("video is required when video_metadata_override is not set")
        vmeta = _video_metadata_from_sources(
            video,
            overall_results,
            total_frames_override=total_frames_override,
        )
    set_entity = ExerciseSetEntity(
        exercise_id=config.exercise_id,
        set_index=config.set_index,
        original_video_uri=original_video_uri,
        processed_video_uri=processed_video_uri,
        session_metadata=_session_metadata_from_context(context),
        video_metadata=vmeta,
        rep_set_summary=rep_summary,
    )
    frames = overall_results_to_biometric_frames(overall_results)
    repo = MongoExerciseSetRepository(
        db, use_transactions=config.use_transactions
    )
    return repo.insert_set_with_frames(set_entity, frames)


def _video_metadata_from_overall(overall: OverallResults, total_frames: int) -> VideoMetadata:
    fps_val = overall.fps or 30
    return VideoMetadata(
        fps=overall.fps,
        video_width=overall.video_width,
        video_height=overall.video_height,
        total_frames=total_frames,
        duration_sec=float(total_frames) / float(max(fps_val, 1)),
    )


def persist_overall_results_json_path(
    json_path: str | Path,
    *,
    exercise_id: str,
    set_index: int = 0,
    original_video_uri: str = "",
    processed_video_uri: str = "",
    database: Database | None = None,
) -> ObjectId:
    """Load ``OverallResults`` JSON and persist biometrics + metadata (no raw ``Video`` required)."""
    path = Path(json_path)
    overall = OverallResults.model_validate_json(path.read_text(encoding="utf-8"))
    et = ExerciseType.from_string(overall.exercise_type or "SQUAT")
    cv = CameraView.from_string(overall.camera_view or "RIGHT")
    ctx = SessionContext(
        user_id=None,
        exercise_type=et,
        camera_view=cv,
        input_source=InputSource.VIDEO_FILE,
        video_path=original_video_uri or None,
    )
    n = len(overall.results)
    vmeta = _video_metadata_from_overall(overall, n)
    cfg = MongodbPersistConfig(
        exercise_id=exercise_id,
        set_index=set_index,
        compute_rep_summary=True,
        ensure_indexes=True,
    )
    return persist_pipeline_output(
        overall_results=overall,
        context=ctx,
        video=None,
        original_video_uri=original_video_uri or str(path.resolve()),
        processed_video_uri=processed_video_uri or str(path.resolve()),
        config=cfg,
        database=database,
        total_frames_override=n,
        video_metadata_override=vmeta,
    )
