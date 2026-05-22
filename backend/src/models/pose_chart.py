from typing import Literal

from typing_extensions import TypedDict

KipName = Literal["INSIDE_KNEE", "OUTSIDE_HIP", "HIP_HINGE", "FRONT_KNEE"]


class PoseChartPoint(TypedDict, total=False):
    frame: int
    timestampSec: float
    INSIDE_KNEE: float | None
    OUTSIDE_HIP: float | None
    HIP_HINGE: float | None
    FRONT_KNEE: float | None
