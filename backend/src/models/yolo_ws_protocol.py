"""Pydantic wire shapes for the `/yolo` Socket.IO namespace."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from models.overall_results import OverallResult


class FrameDimensions(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    format: str | None = None

    @field_validator("format", mode="before")
    @classmethod
    def normalize_format(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).lower().strip()
        if s in ("jpg", "jpeg"):
            return "jpeg"
        if s in ("png", "rgb"):
            return s
        raise ValueError("format must be jpeg, png, or rgb")


class YoloRegisterStream(BaseModel):
    stream_id: str = Field(min_length=1)
    camera_view: str | None = None
    exercise_type: str | None = None


class YoloFrameMeta(BaseModel):
    stream_id: str = Field(min_length=1)
    seq: int = Field(ge=0)
    dimensions: FrameDimensions


class YoloFrameIncoming(BaseModel):
    meta: YoloFrameMeta
    frame: bytes = Field(min_length=1)


class YoloUnregisterStream(BaseModel):
    stream_id: str = Field(min_length=1)


class YoloFrameResult(BaseModel):
    stream_id: str
    seq: int
    t_server: float
    overall: OverallResult | None = None
    error: str | None = None
