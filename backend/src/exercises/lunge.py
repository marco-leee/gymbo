"""Lunge: primary rep signal is FRONT_KNEE (hip–knee–ankle).

MVP uses the same sagittal triple as squat INSIDE_KNEE per CameraView; alternating
lunges may need bilateral logic later.
"""

from typing import Dict

from utils.video import CameraView

from .squat import Squat
from .base import KeyInterestPoint2D, KeyInterestPointEnum


class Lunge(Squat):
    PRIMARY_REP_ANGLE_KEY = "FRONT_KNEE"

    def get_key_interest_point_enum(self) -> KeyInterestPointEnum:
        squat_enum = Squat().get_key_interest_point_enum().root
        return KeyInterestPointEnum(
            **{
                CameraView.LEFT.value: {
                    "FRONT_KNEE": squat_enum[CameraView.LEFT.value]["INSIDE_KNEE"],
                },
                CameraView.RIGHT.value: {
                    "FRONT_KNEE": squat_enum[CameraView.RIGHT.value]["INSIDE_KNEE"],
                },
            }
        )

    def get_2d_key_points(
        self, result, camera_view: CameraView, img_height: int, img_width: int
    ) -> Dict[str, KeyInterestPoint2D]:
        raw = super().get_2d_key_points(result, camera_view, img_height, img_width)
        return {"FRONT_KNEE": raw["INSIDE_KNEE"]}
