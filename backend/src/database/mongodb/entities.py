"""Domain models for MongoDB exercise / set / biometrics persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from models.rep_set_count import RepSetCountResult
from pipeline.biometrics import FrameBiometricsResult


class CountedSetSummary(BaseModel):
    """Embedded rep/set segment (mirrors ``CountedSet``)."""

    idx: int
    reps: int
    start_timestamp: float
    end_timestamp: float
    rep_timestamps: list[float] = Field(default_factory=list)


class RepSetSummary(BaseModel):
    """Embedded ``RepSetCountResult`` for one exercise set recording."""

    exercise_type: str
    camera_view: str
    total_reps: int
    rep_timestamps: list[float]
    sets: list[CountedSetSummary]


def rep_set_count_result_to_summary(r: RepSetCountResult) -> RepSetSummary:
    return RepSetSummary(
        exercise_type=r.exercise_type,
        camera_view=r.camera_view,
        total_reps=r.total_reps,
        rep_timestamps=list(r.rep_timestamps),
        sets=[
            CountedSetSummary(
                idx=s.idx,
                reps=s.reps,
                start_timestamp=s.start_timestamp,
                end_timestamp=s.end_timestamp,
                rep_timestamps=list(s.rep_timestamps),
            )
            for s in r.sets
        ],
    )


class SessionMetadata(BaseModel):
    """Subset of ``SessionContext`` stored on each exercise set."""

    model_config = {"extra": "ignore"}

    user_id: str | None = None
    exercise_type: str
    camera_view: str
    input_source: str
    planned_sets: int | None = None
    target_reps_per_set: int | None = None
    conf_threshold: float
    yolo_detect_weights: str | None = None
    yolo_seg_weights: str | None = None
    yolo_pose_weights: str | None = None
    pose_detection_model_name: str | None = None


class VideoMetadata(BaseModel):
    """Geometry and timing for the source video."""

    model_config = {"extra": "ignore"}

    fps: int | None = None
    video_width: int | None = None
    video_height: int | None = None
    total_frames: int | None = None
    duration_sec: float | None = None


class ExerciseEntity(BaseModel):
    """Exercise row mirrored from domain ``Exercise`` (ULID strings)."""

    model_config = {"extra": "ignore"}

    id: str
    client_id: str
    assessment_id: str
    name: str
    description: str
    type: str
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


class ExerciseSetEntity(BaseModel):
    """One set / recording under an exercise (persisted without Mongo _id)."""

    model_config = {"extra": "ignore"}

    exercise_id: str
    set_index: int
    original_video_uri: str
    processed_video_uri: str
    session_metadata: SessionMetadata
    video_metadata: VideoMetadata
    rep_set_summary: RepSetSummary | None = None
    schema_version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SetBiometricFrameEntity(BaseModel):
    """One frame’s derived biometrics for a set (no raw perception)."""

    model_config = {"extra": "ignore"}

    idx: int
    timestamp: float
    biometrics: FrameBiometricsResult
    biometrics_version: int = 1
