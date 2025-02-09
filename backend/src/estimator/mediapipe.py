from calendar import c
import time
import mediapipe as mp
import numpy as np
from typing import Any, Generator
from .base import Estimator, EstimatorOutput
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    PoseLandmarkerResult,
    RunningMode,
)

# from mediapipe.tasks.python.vision import PoseLandmarkerResult
from exercises import ExerciseType, Squat
from utils import Video
from livekit import rtc

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
            running_mode=RunningMode.LIVE_STREAM,
        )

    async def detect_image(
        self, type: ExerciseType, image: np.ndarray, video_source: rtc.VideoSource
    ) -> EstimatorOutput | None:
        type_processor = self._exercise_types[type]

        def result_callback(result: Any, output_image: mp.Image, timestamp_ms: int):
            if not result.pose_landmarks:
                return None

            raw_landmark_2d = result.pose_landmarks[0]
            key_interest_points_2d = type_processor.get_2d_key_points(
                raw_landmark_2d, self.camera_view, self.height, self.width
            )
            annotated_image = self.draw_landmark(
                image, raw_landmark_2d, kips=key_interest_points_2d
            )
            
            annotated_image = rtc.VideoFrame(
                width=output_image,
                height=frame.frame.height,
                type=rtc.VideoBufferType.BGRA,
                data=result.annotated_image.tobytes(),
            )

            video_source.capture_frame(annotated_image)

            return EstimatorOutput(
                0, annotated_image, raw_landmark_2d, key_interest_points_2d
            )

        with PoseLandmarker.create_from_options(
            PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=self._model_path),
                running_mode=RunningMode.LIVE_STREAM,
                callback=result_callback,
            )
        ) as landmarker:
            await landmarker.detect_async(
                image=mp.Image(image_format=mp.ImageFormat.SRGB, data=image),
                timestamp_ms=int(time.time() * 1000),
            )

            if not result.pose_landmarks:
                return None

            raw_landmark_2d = result.pose_landmarks[0]
            key_interest_points_2d = type_processor.get_2d_key_points(
                raw_landmark_2d, self.camera_view, self.height, self.width
            )
            annotated_image = self.draw_landmark(
                image, raw_landmark_2d, kips=key_interest_points_2d
            )

        return EstimatorOutput(
            0, annotated_image, raw_landmark_2d, key_interest_points_2d
        )

    def execute(
        self, type: ExerciseType, video: Video
    ) -> Generator[EstimatorOutput, None, None]:
        type_processor = self._exercise_types[type]

        with PoseLandmarker.create_from_options(self._options) as landmarker:
            for idx, frame in video.get_frames():
                result = landmarker.detect(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                )
                raw_landmark_2d = result.pose_landmarks[0]
                key_interest_points_2d = type_processor.get_2d_key_points(
                    raw_landmark_2d, video.camera_view, video.height, video.width
                )
                annotated_image = self.draw_landmark(
                    frame, raw_landmark_2d, kips=key_interest_points_2d
                )
                yield EstimatorOutput(
                    idx, annotated_image, raw_landmark_2d, key_interest_points_2d
                )
