"""Deadlift: primary rep signal is hip hinge (shoulder–hip–knee).

Limitation: conventional sagittal profile only; sumo / angled cameras may need retuning.
"""

from typing import Dict, Tuple

from utils.video import CameraView
from .base import KeyInterestPoint, KeyInterestPoint2D, KeyInterestPointEnum


class Deadlift(KeyInterestPoint):
    """Rep/set counting uses HIP_HINGE angle (same geometry as squat OUTSIDE_HIP)."""

    PRIMARY_REP_ANGLE_KEY = "HIP_HINGE"

    def get_key_interest_point_enum(self) -> KeyInterestPointEnum:
        return KeyInterestPointEnum(
            **{
                CameraView.LEFT.value: {"HIP_HINGE": (11, 23, 25)},
                CameraView.RIGHT.value: {"HIP_HINGE": (12, 24, 26)},
            }
        )

    def calculate_hip_hinge_angle(
        self, key_points: Tuple, idx_to_coordinates: Dict[int, tuple[float, float]]
    ) -> KeyInterestPoint2D:
        shoulder, hip, knee = key_points

        shoulder_coord = idx_to_coordinates[shoulder]
        hip_coord = idx_to_coordinates[hip]
        hip_x, hip_y = hip_coord
        knee_coord = idx_to_coordinates[knee]

        idx_to_result = {shoulder: shoulder_coord, hip: hip_coord, knee: knee_coord}

        angle = self.calculate_angle(shoulder_coord, hip_coord, knee_coord, outer=True)
        rotation_angle = self.calculate_angle(
            (hip_x + 90, hip_y), hip_coord, knee_coord
        )

        check, colour = None, None
        if angle in range(90, 120):
            check = "GOOD"
            colour = (0, 255, 0)
        elif angle <= 90:
            check = "TOO LOW"
            colour = (255, 0, 0)
        elif angle in range(120, 150):
            check = "LOWER"
            colour = (0, 255, 255)

        return KeyInterestPoint2D(
            idx_to_coordinates=idx_to_result,
            angle=angle,
            rotation_angle=rotation_angle,
            comment=check,
            colour=colour,
        )

    def get_2d_key_points(
        self, result, camera_view: CameraView, img_height: int, img_width: int
    ) -> Dict[str, KeyInterestPoint2D]:
        idx_to_coordinates = {
            idx: (landmark.x * img_width, landmark.y * img_height)
            for idx, landmark in enumerate(result)
        }

        key_points_2d = {}
        for name, key_points in (
            self.get_key_interest_point_enum().dict()[camera_view.value].items()
        ):
            if name == "HIP_HINGE":
                key_points_2d[name] = self.calculate_hip_hinge_angle(
                    key_points, idx_to_coordinates
                )
            else:
                raise ValueError(f"Invalid key point name: {name}")

        return key_points_2d
