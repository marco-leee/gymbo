"""Pydantic wire models for trainer Socket.IO events."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TrainerRegisterPayload(BaseModel):
    run_id: str
    gymbo_session_id: str
    session_exercise_id: str
    client_id: str
    exercise_type: str = "overhead_squat"
    camera_view: str = "LEFT"
    config: dict[str, Any] = Field(default_factory=dict)


class TrainerRegisteredPayload(BaseModel):
    run_id: str
    session_exercise_id: str
    status: str
    config: dict[str, Any]


class FrameDimensions(BaseModel):
    width: int = 640
    height: int = 480
    format: str = "jpeg"


class FrameMeta(BaseModel):
    run_id: str
    seq: int
    timestamp_sec: float
    dimensions: FrameDimensions = Field(default_factory=FrameDimensions)


class TrainerFramePayload(BaseModel):
    meta: FrameMeta
    frame: str  # base64 JPEG


class TrainerControlPayload(BaseModel):
    run_id: str
    action: Literal["resume", "end", "end_set", "end_rest", "emergency_ack"]


class TrainerUnregisterPayload(BaseModel):
    run_id: str


class TrainerPingPayload(BaseModel):
    run_id: str


class TrainerErrorPayload(BaseModel):
    code: str
    message: str
    run_id: str | None = None
