from dataclasses import dataclass

from exercises.base import KeyInterestPoint
from exercises import Squat, Lunge, Deadlift
from models.exercise import ExerciseType


@dataclass(frozen=True)
class ExerciseRepSpec:
    processor: KeyInterestPoint
    primary_rep_angle_key: str


_EXERCISE_REP_REGISTRY: dict[ExerciseType, ExerciseRepSpec] = {
    ExerciseType.SQUAT: ExerciseRepSpec(Squat(), Squat.PRIMARY_REP_ANGLE_KEY),
    ExerciseType.LUNGE: ExerciseRepSpec(Lunge(), Lunge.PRIMARY_REP_ANGLE_KEY),
    ExerciseType.DEADLIFT: ExerciseRepSpec(Deadlift(), Deadlift.PRIMARY_REP_ANGLE_KEY),
}


def get_rep_spec(exercise_type: ExerciseType) -> ExerciseRepSpec:
    try:
        return _EXERCISE_REP_REGISTRY[exercise_type]
    except KeyError as e:
        raise KeyError(f"No rep-counter spec for exercise: {exercise_type}") from e
