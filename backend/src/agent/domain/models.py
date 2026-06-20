"""Domain models for the AI trainer agent."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    CREATED = "created"
    PREPARING = "preparing"
    SETUP = "setup"
    ACTIVE = "active"
    RESTING = "resting"
    PAUSED = "paused"
    FEEDBACK = "feedback"
    ENDED = "ended"


class RunPhase(StrEnum):
    PREPARE = "prepare"
    SETUP = "setup"
    SET_IN_PROGRESS = "set_in_progress"
    REST = "rest"
    FEEDBACK = "feedback"
    SESSION_COMPLETE = "session_complete"


REP_PHASES = ("setup", "descending", "bottom", "ascending", "lockout", "rest")
SEVERITIES = ("none", "minor", "moderate", "critical")


class ExerciseRunConfig(BaseModel):
    planned_sets: int = 3
    target_reps_per_set: int = 10
    rest_duration_sec: int = 60
    rest_needed: bool = True
    frame_sample_rate_fps: float = 1.0
    voice_repeat_threshold: int = 3
    exercise_type: str = "overhead_squat"


class VLMFrameResult(BaseModel):
    frame_index: int = 0
    timestamp_sec: float = 0.0
    in_rep: bool = False
    rep_phase: str = "setup"
    observations: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    severity: Literal["none", "minor", "moderate", "critical"] = "none"
    confidence: float = 0.0
    rep_completed: bool = False
    action: Literal["observe", "voice_out"] = "observe"
    voice_reason: str | None = None
    focus_issue: str | None = None


class MergedObservationState(BaseModel):
    completed_reps: int = 0
    total_session_reps: int = 0
    rep_phase: str = "setup"
    in_rep: bool = False
    active_issues: list[str] = Field(default_factory=list)
    frame_results: list[VLMFrameResult] = Field(default_factory=list)
    recurring_issues: dict[str, int] = Field(default_factory=dict)


class VoiceRepeatState(BaseModel):
    last_voiced_issue: str | None = None
    repeat_count: int = 0
    threshold: int = 3


class VoiceOutEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    set_number: int = 1
    focus_issue: str
    reason: str
    severity: str = "moderate"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    frame_seq: int = 0


class VoiceOutDecision(StrEnum):
    SPEAK = "speak"
    SKIP = "skip"
    INCREMENT = "increment"


class FrameSnapshot(BaseModel):
    frame_index: int
    timestamp_sec: float
    frame_b64: str
    seq: int = 0


class IncomingFrame(BaseModel):
    seq: int
    timestamp_sec: float
    jpeg_bytes: bytes
    width: int = 640
    height: int = 480


class PoseResult(BaseModel):
    landmarks: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    annotated_b64: str | None = None


class CoachingEventRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    message: str
    focus_issue: str
    trigger_reason: str = ""
    severity: str = "moderate"
    set_number: int = 1
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dedup_repeat_count: int | None = None


class SafetyEventRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    source: Literal["set_check", "global_monitor"] = "set_check"
    severity: str = "critical"
    description: str
    halted_session: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CoachedExerciseRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    gymbo_session_id: str
    session_exercise_id: str
    trainer_id: str
    client_id: str
    exercise_type: str = "overhead_squat"
    status: RunStatus = RunStatus.CREATED
    config: ExerciseRunConfig = Field(default_factory=ExerciseRunConfig)
    merged_observation_state: MergedObservationState = Field(
        default_factory=MergedObservationState
    )
    current_set_number: int = 1
    completed_sets: int = 0
    voice_repeat_state: VoiceRepeatState = Field(default_factory=VoiceRepeatState)
    phase: RunPhase = RunPhase.PREPARE
    started_at: datetime | None = None
    ended_at: datetime | None = None
    exercise_feedback: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
