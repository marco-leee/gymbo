from abc import abstractmethod, ABC
from typing import Dict, NamedTuple, Tuple, TypeAlias
import numpy as np
from pydantic import BaseModel, Field, RootModel

from utils import CameraView


# class KeyInterestPoint2D(NamedTuple):
#     idx_to_coordinates: Dict[int, Tuple[int, int]]
#     angle: int
#     rotation_angle: int
#     comment: str
#     colour: Tuple[int, int, int]

# Type aliases for KeyInterestPoint2D properties

Coordinate: TypeAlias = Tuple[float, float]
CoordinateMap: TypeAlias = Dict[int, Coordinate]
RGBColor: TypeAlias = Tuple[int, int, int] | None
Angle: TypeAlias = int
Comment: TypeAlias = str | None


class KeyInterestPoint2D(BaseModel):
    idx_to_coordinates: CoordinateMap = Field(
        description="Mapping of point indices to their 2D coordinates"
    )
    angle: Angle = Field(
        description="The angle measurement for this key point", ge=0, lt=360
    )
    rotation_angle: Angle = Field(
        description="The rotation angle for this key point", ge=0, lt=360
    )
    comment: Comment = Field(description="Description or label for this key point")
    colour: RGBColor = Field(
        description="RGB color tuple for visualization", min_items=3, max_items=3
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            tuple: list,  # Convert tuples to lists for JSON serialization
        }

    def model_dump_json(self, **kwargs) -> str:
        """Custom JSON serialization that handles tuples and None values"""
        data = self.model_dump()
        # Convert tuples to lists in idx_to_coordinates
        data["idx_to_coordinates"] = {
            k: list(v) for k, v in data["idx_to_coordinates"].items()
        }
        # Convert colour tuple to list if not None
        if data["colour"] is not None:
            data["colour"] = list(data["colour"])
        return super().model_dump_json(**kwargs)

    def validate_rgb(self) -> bool:
        """Validate that all RGB values are between 0 and 255"""
        if self.colour is None:
            return True
        return all(0 <= x <= 255 for x in self.colour)


KeyInterestPointEnum = RootModel[Dict[str, Dict[str, Tuple[int, int, int]]]]


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
    def get_key_interest_point_enum(self) -> KeyInterestPointEnum:
        raise NotImplementedError

    @abstractmethod
    def get_2d_key_points(
        self, result, camera_view: CameraView, img_height: int, img_width: int
    ) -> Dict[str, KeyInterestPoint2D]:
        raise NotImplementedError
