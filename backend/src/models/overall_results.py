from typing import Any

from pydantic import BaseModel


class OverallResult(BaseModel):
    idx: int
    timestamp: float
    pose_estimation_result: dict
    segmentation_result: dict
    biometrics: dict[str, Any] | None = None


class OverallResults(BaseModel):
    """Pose pipeline export + metadata so offline rep/set counting can reproduce angles."""

    results: list[OverallResult]
    camera_view: str | None = None
    exercise_type: str | None = None
    video_width: int | None = None
    video_height: int | None = None
    fps: int | None = None
