from abc import abstractmethod, ABC
from typing import Dict, NamedTuple, Tuple
import numpy as np
from enum import Enum

from utils import CameraView


class ExerciseType(Enum):
    SQUAT = "SQUAT"
    PUSH_UP = "PUSH_UP"


class KeyInterestPoint2D(NamedTuple):
    idx_to_coordinates: Dict[int, Tuple[int, int]]
    angle: int
    rotation_angle: int
    comment: str
    colour: Tuple[int, int, int]


class KeyInterestPoint(ABC):
    def calculate_angle(self, a, b, c, outer=False) -> int:
        """
        Calculate the angle between three points
        """
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(
            a[1] - b[1], a[0] - b[0]
        )
        angle = np.abs(radians * 180.0 / np.pi)

        if outer or angle > 180:
            angle = 360 - angle

        return int(angle)

    @abstractmethod
    def get_2d_key_points(
        self, result, camera_view: CameraView, img_height: int, img_width: int
    ) -> Dict[str, KeyInterestPoint2D]:
        pass
