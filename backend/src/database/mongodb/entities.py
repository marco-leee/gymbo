"""Domain models for MongoDB exercise / set / biometrics persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from typing import Any

from pydantic import BaseModel, Field, model_validator

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


class VideoMetadata(BaseModel):
    """Geometry, camera, and timing for the source video."""

    model_config = {"extra": "ignore"}

    camera_view: str | None = None
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
    session_id: str
    name: str
    description: str
    type: str
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _legacy_assessment_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and "session_id" not in data and data.get("assessment_id"):
            data = {**data, "session_id": data["assessment_id"]}
        return data


class ExerciseSetEntity(BaseModel):
    """One set / recording under an exercise (persisted without Mongo _id)."""

    model_config = {"extra": "ignore"}

    exercise_id: str
    set_index: int
    original_video_uri: str
    processed_video_uri: str
    pose_detection_model_name: str | None = None
    video_metadata: VideoMetadata
    rep_set_summary: RepSetSummary | None = None
    schema_version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="before")
    @classmethod
    def _legacy_session_metadata(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        legacy = data.pop("session_metadata", None)
        if not isinstance(legacy, dict):
            return data
        cam = legacy.pop("camera_view", None)
        pdm = legacy.pop("pose_detection_model_name", None)
        vm = data.get("video_metadata")
        if cam is not None:
            if isinstance(vm, dict):
                merged = dict(vm)
                if merged.get("camera_view") in (None, ""):
                    merged["camera_view"] = cam
                data["video_metadata"] = merged
            else:
                data["video_metadata"] = {"camera_view": cam}
        if pdm is not None and "pose_detection_model_name" not in data:
            data["pose_detection_model_name"] = pdm
        return data


class SetBiometricFrameEntity(BaseModel):
    """One frame’s derived biometrics for a set (no raw perception)."""

    model_config = {"extra": "ignore"}

    idx: int
    timestamp: float
    biometrics: FrameBiometricsResult
    biometrics_version: int = 1
