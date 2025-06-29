import mediapipe as mp
import numpy as np
from typing import Any, Generator

from utils.video import CameraView
from .base import Estimator, EstimatorOutput
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    RunningMode,
)

from models.exercise import ExerciseType
from exercises import Squat
from utils import Video

BaseOptions = mp.tasks.BaseOptions


class MediapipeEstimator(Estimator, Video):
    _model_path: str
    _excluded_index_list: frozenset[int] = frozenset(list(range(11)))
    _connections = frozenset(
        [(c.start, c.end) for c in PoseLandmarksConnections.POSE_LANDMARKS]
    )
    _exercise_types = {ExerciseType.SQUAT: Squat()}

    def __init__(self, model_path: str):
        self._model_path = model_path

        self._options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self._model_path),
            running_mode=RunningMode.IMAGE,
        )

    # TODO: Add a function for livestream prediction

    def detect_image(
        self,
        image: np.ndarray,
        type: ExerciseType = None,
    ) -> EstimatorOutput | None:
        type_processor = None

        if type is not None:
            type_processor = self._exercise_types[type]

        with PoseLandmarker.create_from_options(self._options) as landmarker:
            result = landmarker.detect(
                image=mp.Image(image_format=mp.ImageFormat.SRGB, data=image),
            )

            # Avoid confusion with None
            if not result.pose_landmarks:
                return None

            raw_landmark_2d = result.pose_landmarks[0]

            key_interest_points_2d = None

            if type_processor is not None:
                key_interest_points_2d = type_processor.get_2d_key_points(
                    raw_landmark_2d, self.camera_view, self.height, self.width
                )
            annotated_image = self.draw_landmark(
                image, raw_landmark_2d, kips=key_interest_points_2d
            )

        return EstimatorOutput(
            0, annotated_image, raw_landmark_2d, key_interest_points_2d
        )

    def detect_image_custom_params(
        self,
        image: np.ndarray,
        type: ExerciseType = None,
        camera_view: CameraView = CameraView.RIGHT,
        height: int = 1080,
        width: int = 1920,
    ) -> EstimatorOutput | None:
        type_processor = None

        if type is not None:
            type_processor = self._exercise_types[type]

        with PoseLandmarker.create_from_options(self._options) as landmarker:
            result = landmarker.detect(
                image=mp.Image(image_format=mp.ImageFormat.SRGB, data=image),
            )

            # Avoid confusion with None
            if not result.pose_landmarks:
                return None

            raw_landmark_2d = result.pose_landmarks[0]

            key_interest_points_2d = None

            if type_processor is not None:
                key_interest_points_2d = type_processor.get_2d_key_points(
                    raw_landmark_2d, camera_view, height, width
                )
            annotated_image = self.draw_landmark(
                image, raw_landmark_2d, kips=key_interest_points_2d
            )

        return EstimatorOutput(
            0, annotated_image, raw_landmark_2d, key_interest_points_2d
        )

    def detect_video(
        self, video: Video, type: ExerciseType = None
    ) -> Generator[EstimatorOutput, None, None]:
        type_processor = None
        angle_of_interest_enum = None

        if type is not None:
            type_processor = self._exercise_types[type]
            angle_of_interest_enum = type_processor.get_key_interest_point_enum()

        with PoseLandmarker.create_from_options(self._options) as landmarker:
            for idx, frame in video.get_frames():
                result = landmarker.detect(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                )

                if not result.pose_landmarks:
                    continue

                raw_landmark_2d = result.pose_landmarks[0]

                key_interest_points_2d = None

                if type_processor is not None:
                    key_interest_points_2d = type_processor.get_2d_key_points(
                        raw_landmark_2d, video.camera_view, video.height, video.width
                    )

                annotated_image = self.draw_landmark(
                    frame, raw_landmark_2d, kips=key_interest_points_2d
                )

                yield EstimatorOutput(
                    idx,
                    annotated_image,
                    raw_landmark_2d,
                    key_interest_points_2d,
                    angle_of_interest_enum,
                )
