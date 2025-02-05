import os
import logging
from typing import Generator
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    RunningMode,
)
from repo import CoreRepo, MongoCoreRepo
from exercises import ExerciseType, Squat
from storage import S3StorageProvider, StorageProvider
import cv2 as cv
from utils import Video, CameraView, EstimatorOutput, Estimator

BaseOptions = mp.tasks.BaseOptions

root_path = os.path.dirname(os.path.abspath(__file__))


class BlazePoseEstimator(Estimator, Video):
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

    def detect_image(self, type: ExerciseType, image: np.ndarray) -> EstimatorOutput:
        type_processor = self._exercise_types[type]
        
        with PoseLandmarker.create_from_options(self._options) as landmarker:
            result = landmarker.detect(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
            )
            raw_landmark_2d = result.pose_landmarks[0]
            key_interest_points_2d = type_processor.get_2d_key_points(
                raw_landmark_2d, self.camera_view, self.height, self.width
            )
            annotated_image = self.draw_landmark(
                image, raw_landmark_2d, kips=key_interest_points_2d
            )
        
        return EstimatorOutput(0, annotated_image, raw_landmark_2d, key_interest_points_2d)

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


class PoseEstimationWorker:
    def __init__(
        self, repo: CoreRepo, storage_provider: StorageProvider, estimator: Estimator
    ) -> None:
        self._repo = repo
        self._estimator = estimator
        self.storage_provider = storage_provider
        self._logger = logging.getLogger(self.__class__.__name__)

    def postprocessing(self, result):
        formatted_landmark_2d = [
            {
                "landmark_index": idx,
                "x": each.x,
                "y": each.y,
                "x_score": each.visibility,
                "y_score": each.visibility,
            }
            for idx, each in enumerate(result)
        ]

        return formatted_landmark_2d

    def handle_task(self) -> None:
        # TODO: Implement processing
        while True:
            # TODO: iterate on the steps
            break

    def run(self):
        # TODO: Pull job from queue

        # TODO: Parse the string

        # TODO: Validate the schema

        # TODO: Turn into a tmp path
        video_path = f"{root_path}/media/test.mp4"

        video = Video(video_path, CameraView.RIGHT)

        fourcc = cv.VideoWriter_fourcc(*"mp4v")
        new_video = cv.VideoWriter(
            "processed.mp4",
            fourcc=fourcc,
            fps=video.fps,
            frameSize=video.shape,
            isColor=True,
        )

        for result in self._estimator.execute(ExerciseType.SQUAT, video):
            frame_count, annotated_image, raw_landmarks, key_interest_point_2d = result
            formatted_landmarks = self.postprocessing(raw_landmarks)

            new_video.write(annotated_image)

        new_video.release()
        # TODO: Upload the video to the cloud
        self.storage_provider.upload_object(video_path, "videos/upload/processed.mp4")
        os.remove(video_path)
        # TODO: Save the result to the database
        # TODO: Update the job status


def main() -> None:
    logger = logging.getLogger(__name__)

    try:
        access_key = "RFbPRwd0jI499M1bi2S0"
        secret_key = "dIefcszHPiUwLqf28U9XGAZs6WLLMLjQd3P1wCrl"
        s3 = S3StorageProvider(
            bucket="exercise-analyser",
            access_key=access_key,
            secret_key=secret_key,
            endpoint_url="http://localhost:9000",
        )
    except Exception as e:
        logger.fatal("pose detection worker init failed: ", e)
        exit(1)

    try:
        db = "exercise_analyser"
        conn_str = f"mongodb://admin:local@localhost:27017/{db}"
        repo = MongoCoreRepo(conn_str, db)
    except Exception as e:
        logger.fatal("cassandra repo init failed")
        exit(1)

    try:
        estimator = BlazePoseEstimator(
            model_path=os.path.join(root_path, "models", "pose_landmarker_full.task")
        )
    except Exception as e:
        logger.fatal("pose estimator init failed", e)
        exit(1)

    try:
        worker = PoseEstimationWorker(
            repo=repo, storage_provider=s3, estimator=estimator
        )
    except Exception as e:
        logger.fatal("pose detection worker init failed: ", e)
        exit(1)

    try:
        worker.run()
    except Exception as e:
        logger.fatal("worker run fatal error: ", e)
        exit(1)


if __name__ == "__main__":
    main()
