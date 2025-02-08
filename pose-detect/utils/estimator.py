from abc import abstractmethod, ABC
from typing import Dict, NamedTuple, Generator, Tuple
import numpy as np
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarkerResult
import cv2 as cv


class KeyInterestPoint2D(NamedTuple):
    idx_to_coordinates: Dict[int, Tuple[int, int]]
    angle: int
    rotation_angle: int
    comment: str
    colour: Tuple[int, int, int]


class EstimatorOutput(NamedTuple):
    frame_count: int
    annotated_image: np.ndarray
    raw_landmarks: PoseLandmarkerResult
    key_interest_points_2d: Dict[str, KeyInterestPoint2D]


class Estimator(ABC):
    _connections: frozenset[(int, int)]
    _excluded_index_list: frozenset[int]

    def calculate_angle(self, a, b, c, outer=False):
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

        return angle

    def draw_angle(
        self,
        image: np.ndarray,
        angle: int,
        center=None,
        rotation_angle: int = None,
        label_text: str = None,
        label_colour=None,
    ):
        if center and rotation_angle:
            cv.ellipse(
                image, center, (30, 30), rotation_angle, 0, angle, (0, 255, 0), 2
            )

        cv.putText(
            image,
            format(angle, ".1f"),
            tuple(np.add(center, [-100, 10])),
            cv.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        if label_text and label_colour:
            cv.putText(
                image,
                label_text,
                tuple(np.add(center, [-100, 30])),
                cv.FONT_HERSHEY_SIMPLEX,
                0.6,
                label_colour,
                2,
            )

    def draw_landmark(
        self,
        image: np.ndarray,
        landmarks,
        kips: Dict[str, KeyInterestPoint2D],
        vis_threshold=0.6,
        presence_threshold=0.6,
    ):
        annotated_image = np.copy(image)

        # If no landmarks, return the original image
        if not landmarks:
            return annotated_image

        # Get image height and width
        height, width, _ = annotated_image.shape

        # Convert landmarks to coordinates / pixel values (x, y) where x and y are equal to math.floor
        landmark_to_coordinates = lambda landmark: (
            int(landmark.x * width),
            int(landmark.y * height),
        )
        # Filter out landmarks with low confidence and return a dictionary of idx to coordinates / pixel
        # idx 0 to 10 are related to the face, not needed here
        idx_to_coordinates = {
            idx: landmark_to_coordinates(landmark)
            for idx, landmark in enumerate(landmarks)
            if idx not in self._excluded_index_list
        }

        # Draw landmarks
        for landmark in idx_to_coordinates.values():
            cv.circle(annotated_image, landmark, 7, (40, 116, 107), -1)

        # Draw connections
        for idx1, idx2 in self._connections:
            if idx1 not in idx_to_coordinates or idx2 not in idx_to_coordinates:
                continue

            cv.line(
                annotated_image,
                idx_to_coordinates[idx1],
                idx_to_coordinates[idx2],
                (255, 255, 255),
                2,
            )

        for key_interest_point in kips.values():
            _, center, _ = key_interest_point.idx_to_coordinates.values()
            self.draw_angle(
                annotated_image,
                key_interest_point.angle,
                (int(center[0]), int(center[1])),
                key_interest_point.rotation_angle,
                key_interest_point.comment,
                key_interest_point.colour,
            )

        return annotated_image

    @abstractmethod
    def execute(
        self, path: str, is_video: bool
    ) -> Generator[EstimatorOutput, None, None]:
        pass
