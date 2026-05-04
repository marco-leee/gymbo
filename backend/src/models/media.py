from typing_extensions import TypedDict
from pydantic import BaseModel, Field, RootModel
from ulid import ULID
from datetime import datetime, UTC
from typing import Dict, List


class Angle(BaseModel):
    degree: int
    comment: str | None = None


class AnglesOfInterest(BaseModel):
    angles: List[Dict[str, Angle]]


class Landmark2DResult(TypedDict):
    idx: int
    x: float
    y: float
    x_score: float
    y_score: float


class Landmark2DResults(BaseModel):
    results: List[List[Landmark2DResult]]


class Landmark3DResult(TypedDict):
    idx: int
    score: float
    x: float
    y: float
    z: float


class Landmark3DResults(BaseModel):
    results: List[List[Landmark3DResult]]


Metadata = RootModel[Dict[str, str]]


Errors = RootModel[Dict[str, str]]


class Media(BaseModel):
    id: ULID
    exercise_id: ULID
    step: str
    camera_view: str
    original_video_location: str
    processed_video_location: str
    pose_detection_model_name: str
    metadata: Metadata
    errors: Errors
    angles_of_interest: AnglesOfInterest
    landmark2d_results: Landmark2DResults
    landmark3d_results: Landmark3DResults
    completed_at: datetime = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now(UTC))
    updated_at: datetime = Field(default_factory=datetime.now(UTC))
    deleted_at: datetime = Field(default=None)
