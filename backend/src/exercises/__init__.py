from models.exercise import ExerciseType

from .base import KeyInterestPoint, KeyInterestPoint2D, KeyInterestPointEnum
from .deadlift import Deadlift
from .lunge import Lunge
from .squat import Squat

__all__ = [
    "Deadlift",
    "ExerciseType",
    "KeyInterestPoint",
    "KeyInterestPoint2D",
    "KeyInterestPointEnum",
    "Lunge",
    "Squat",
]
