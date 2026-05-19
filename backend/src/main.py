import os
import logging
import time
from pathlib import Path
from typing import Dict, List
import mediapipe as mp
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarkerResult
from estimator.base import EstimatorOutput
from models.exercise import ExerciseType
from models.media import (
    Angle,
    AnglesOfInterest,
    Landmark2DResults,
    Landmark3DResults,
    Landmark2DResult,
    Landmark3DResult,
)
from utils import (
    Video,
    CameraView,
    S3_ACCESS_KEY,
    S3_BUCKET,
    S3_ENDPOINT,
    S3_SECRET,
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    MaxRetryError,
    MAX_RETRY_COUNT,
    get_temp_file_path,
    now,
)
from utils.video_web import remux_mp4_for_browser_playback
from database import Postgres, PostgresConfig
from estimator import MediapipeEstimator
from storage import S3StorageProvider
from utils.error import MaxRetryError

import cv2 as cv


BaseOptions = mp.tasks.BaseOptions

root_path = os.path.dirname(os.path.abspath(__file__))


class PoseEstimationWorker:
    def __init__(
        self,
        repo: Postgres,
        storage_provider: S3StorageProvider,
        estimator: MediapipeEstimator,
    ) -> None:
        self._repo = repo
        self._estimator = estimator
        self.storage_provider = storage_provider
        self._logger = logging.getLogger(self.__class__.__name__)

    def queuing(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "INITIALIZING")

    def initializing(self, job: dict) -> Path:
        video_path = get_temp_file_path()

        self._logger.info(
            f"Downloading video from {job['media']['original_video_location']}"
        )
        self.storage_provider.download_object(
            job["media"]["original_video_location"], video_path
        )
        self._logger.info(f"Video downloaded to {video_path}")
        self._repo.update_media_step(job["media"]["id"], "PREPROCESSING")

        return video_path

    def preprocessing(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "PROCESSING")

    def processing(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "POSTPROCESSING")

    def finalising(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "FINALISING")

    def completed(self, job: dict) -> None:
        self._logger.info(f"Media {job['media']['id']} completed")
        self._repo.update_media_step(job["media"]["id"], "COMPLETED")

    def postprocessing(
        self, result: EstimatorOutput
    ) -> tuple[Dict[str, Angle], List[Landmark2DResult]]:
        raw_landmarks = result.raw_landmarks
        key_interest_point_2d = result.key_interest_points_2d

        angle = {
            key: Angle(
                degree=key_interest_point_2d[key].angle,
                comment=key_interest_point_2d[key].comment,
            )
            for key in key_interest_point_2d
        }

        l2d = [
            Landmark2DResult(
                idx=idx,
                x=each.x,
                y=each.y,
                x_score=each.visibility,
                y_score=each.visibility,
            )
            for idx, each in enumerate(raw_landmarks)
        ]

        return angle, l2d

    def handle_task(self, job: dict, video_path: Path) -> None:
        camera_view = CameraView.RIGHT

        video = Video(video_path, camera_view)

        temp_video_path = get_temp_file_path(suffix=".mp4")

        new_video = cv.VideoWriter(
            temp_video_path,
            fourcc=cv.VideoWriter_fourcc(*"mp4v"),
            fps=video.fps,
            frameSize=video.shape,
            isColor=True,
        )

        angles_of_interest = AnglesOfInterest(angles=[])
        landmark2d_results = Landmark2DResults(results=[])

        for result in self._estimator.detect_video(video, ExerciseType.SQUAT):
            if result is None:
                continue

            new_video.write(result.annotated_image)
            aoi, l2d = self.postprocessing(result)
            angles_of_interest.angles.append(aoi)
            landmark2d_results.results.append(l2d)

        new_video.release()

        self._logger.info(f"Video processed")

        object_key = self.storage_provider.get_processed_video_object_key(
            job["exercise"]["id"], job["media"]["id"]
        )

        temp_web_path = get_temp_file_path(suffix=".mp4")
        try:
            self._logger.info("Remuxing processed video for web playback")
            remux_mp4_for_browser_playback(Path(temp_video_path), Path(temp_web_path))
            self._logger.info(f"Uploading processed video to {object_key}")
            self.storage_provider.upload_object(Path(temp_web_path), object_key)
            self._logger.info(f"Video uploaded to {object_key}")
        finally:
            Path(temp_web_path).unlink(missing_ok=True)

        Path(temp_video_path).unlink(missing_ok=True)
        video_path.unlink()

        self._logger.info(f"Videos deleted")

        # TODO: Save the result to the database
        media = {
            "media_metadata": {
                "height": video.height,
                "width": video.width,
                "fps": video.fps,
                "total_frames": video.total_frames,
                "duration": video.duration,
            },
            "processed_video_location": object_key,
            "angles_of_interest_enum": result.angle_of_interest_enum.model_dump()[
                camera_view.value
            ],
            "angles_of_interest": angles_of_interest.model_dump()["angles"],
            "landmark2d_results": landmark2d_results.model_dump()["results"],
            "completed_at": now(),
        }

        self._repo.update_media(job["media"]["id"], media)

        # TODO: Update the job status

        self.completed(job)

    def run(self):
        retry = 0
        # TODO: Pull job from queue
        exercise_id = "01jy02c1rg9vqtrg63gxrf9r02"
        media_id = "01jy02c1rnw7pztj1k1tg2h4t2"
        client_id = "01jy0296v80knvff83dcwgaf7r"
        job = {
            "exercise": {
                "id": exercise_id,
            },
            "media": {
                "id": media_id,
                "original_video_location": "inputs/01jy2m5jva6gzy38f24hzkmrm2.mp4",
            },
        }
        # TODO: Parse the string
        # TODO: Validate the schema
        self.queuing(job)
        # Turn into a tmp path
        video_path = self.initializing(job)

        while retry <= MAX_RETRY_COUNT:
            try:
                if retry > 0:
                    if retry == MAX_RETRY_COUNT:
                        raise MaxRetryError()
                    self._logger.info(f"Retrying task {retry} of {MAX_RETRY_COUNT}")

                self.handle_task(job, video_path)
                break
            except MaxRetryError as e:
                self._logger.error(e)
                self._repo.update_media_error(media_id, e)
                break
            except Exception as e:
                self._logger.error(f"Error processing task: {e}")
                self._repo.update_media_error(media_id, e)
                retry += 1
                time.sleep(3)


def main() -> None:
    logger = logging.getLogger(__name__)

    try:
        # TODO: Use storage factory
        s3 = S3StorageProvider(
            bucket=S3_BUCKET,
            access_key=S3_ACCESS_KEY,
            secret_key=S3_SECRET,
            endpoint_url=S3_ENDPOINT,
        )
        logger.info("S3 initialized")
    except Exception as e:
        logger.fatal("S3 init failed: ", e)
        exit(1)

    try:
        # TODO: Use database factory
        config = PostgresConfig(
            drivername="postgresql",
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        repo = Postgres(config)
        logger.info("Postgres initialized")
    except Exception as e:
        logger.fatal("Postgres init failed: ", e)
        exit(1)

    try:
        # TODO: Use pose detection factory
        estimator = MediapipeEstimator(
            model_path=os.path.join(
                root_path, "pose_models", "pose_landmarker_full.task"
            )
        )
        logger.info("Mediapipe estimator initialized")
    except Exception as e:
        logger.fatal("Mediapipe estimator init failed: ", e)
        exit(1)

    try:
        worker = PoseEstimationWorker(
            repo=repo, storage_provider=s3, estimator=estimator
        )
        logger.info("Pose estimation worker initialized")
    except Exception as e:
        logger.fatal("Pose estimation worker init failed: ", e)
        exit(1)

    try:
        worker.run()
    except Exception as e:
        logger.fatal("Worker run fatal error: ", e)
        exit(1)


if __name__ == "__main__":
    main()
