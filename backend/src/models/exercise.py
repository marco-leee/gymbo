from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from datetime import UTC
from ulid import ULID


class ExerciseType(Enum):
    SQUAT = "SQUAT"
    LUNGE = "LUNGE"
    DEADLIFT = "DEADLIFT"

    def __str__(self):
        return self.value

    @staticmethod
    def from_string(exercise: str):
        return ExerciseType[exercise.upper()]


class Exercise(BaseModel):
    id: ULID
    client_id: ULID
    assessment_id: ULID
    name: str
    description: str
    type: ExerciseType
    comment: str
    created_at: datetime = Field(default_factory=datetime.now(UTC))
    updated_at: datetime = Field(default_factory=datetime.now(UTC))
    deleted_at: datetime = Field(default=None)
