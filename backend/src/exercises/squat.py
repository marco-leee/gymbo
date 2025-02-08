from typing import Dict, Tuple

from utils.video import CameraView
from .base import KeyInterestPoint, KeyInterestPoint2D


class Squat(KeyInterestPoint):
    CAMERA_VIEW_TO_KEY_POINT_INDEX = {
        CameraView.LEFT: {
            "INSIDE_KNEE": (23, 25, 27),  # Left hip, knee, ankle
            "OUTSIDE_HIP": (11, 23, 25),  # Left shoulder, hip, knee
        },
        CameraView.RIGHT: {
            "INSIDE_KNEE": (24, 26, 28),  # Right hip, knee, ankle
            "OUTSIDE_HIP": (12, 24, 26),  # Right shoulder, hip, knee
        },
    }

    def calculate_inside_knee_angle(
        self, key_points: Tuple, idx_to_coordinates: Dict[int, tuple[int, int]]
    ) -> KeyInterestPoint2D:
        hip, knee, ankle = key_points

        hip_coord = idx_to_coordinates[hip]
        knee_coord = idx_to_coordinates[knee]
        knee_x, knee_y = knee_coord
        ankle_coord = idx_to_coordinates[ankle]

        idx_to_result = {hip: hip_coord, knee: knee_coord, ankle: ankle_coord}

        angle = self.calculate_angle(hip_coord, knee_coord, ankle_coord)
        rotation_angle = self.calculate_angle(
            (knee_x + 90, knee_y), knee_coord, ankle_coord
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

    def calculate_outside_hip_angle(
        self, key_points: Tuple, idx_to_coordinates
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
        for name, key_points in self.CAMERA_VIEW_TO_KEY_POINT_INDEX[
            camera_view
        ].items():
            match name:
                case "OUTSIDE_HIP":
                    key_points_2d[name] = self.calculate_outside_hip_angle(
                        key_points, idx_to_coordinates
                    )
                case "INSIDE_KNEE":
                    key_points_2d[name] = self.calculate_inside_knee_angle(
                        key_points, idx_to_coordinates
                    )
                case _:
                    raise ValueError(f"Invalid key point name: {name}")

        return key_points_2d
