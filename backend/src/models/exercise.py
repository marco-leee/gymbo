from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from datetime import UTC
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
    id: str
    client_id: str
    assessment_id: str
    name: str
    description: str
    type: ExerciseType
    comment: str
    created_at: datetime = Field(default_factory=datetime.now(UTC))
    updated_at: datetime = Field(default_factory=datetime.now(UTC))
    deleted_at: datetime = Field(default=None)
