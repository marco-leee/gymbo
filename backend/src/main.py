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
from utils import Video, CameraView, S3_ACCESS_KEY, S3_BUCKET, S3_ENDPOINT, S3_SECRET
from storage import S3StorageProvider, StorageProvider
import cv2 as cv

from estimator import Estimator, MediapipeEstimator

BaseOptions = mp.tasks.BaseOptions

root_path = os.path.dirname(os.path.abspath(__file__))


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
        video_path = f"{root_path}/test.mp4"

        video = Video(video_path, CameraView.RIGHT)

        fourcc = cv.VideoWriter_fourcc(*"mp4v")
        new_video = cv.VideoWriter(
            "processed.mp4",
            fourcc=fourcc,
            fps=video.fps,
            frameSize=video.shape,
            isColor=True,
        )

        for result in self._estimator.detect_video(ExerciseType.SQUAT, video):
            if result is None:
                continue

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
        s3 = S3StorageProvider(
            bucket=S3_BUCKET,
            access_key=S3_ACCESS_KEY,
            secret_key=S3_SECRET,
            endpoint_url=S3_ENDPOINT,
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
        estimator = MediapipeEstimator(
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
