import os
import logging
import time
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
    MAX_RETRY_ERROR,
    MAX_RETRY_COUNT,
    get_temp_file_path,
    now,
)
from database import Postgres, PostgresConfig
from estimator import MediapipeEstimator
from storage import S3StorageProvider

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

    def initializing(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "PREPROCESSING")

    def preprocessing(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "PROCESSING")

    def processing(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "POSTPROCESSING")

    def finalising(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "FINALISING")

    def completed(self, job: dict) -> None:
        self._repo.update_media_step(job["media"]["id"], "COMPLETED")

    def postprocessing(self, result: EstimatorOutput) -> tuple[dict, dict, dict]:
        # frame_count, annotated_image, raw_landmarks, key_interest_point_2d = result

        angle = Angle(idx=0, degree=0)
        l2d = Landmark2DResult(idx=0, x=0, y=0, x_score=0, y_score=0)
        l3d = Landmark3DResult(idx=0, score=0, x=0, y=0, z=0)

        # formatted_landmark_2d = [
        #     {
        #         "landmark_index": idx,
        #         "x": each.x,
        #         "y": each.y,
        #         "x_score": each.visibility,
        #         "y_score": each.visibility,
        #     }
        #     for idx, each in enumerate(result)
        # ]

        return angle, l2d, l3d

    def handle_task(self, job: dict, video_path: str) -> None:

        video = Video(video_path, CameraView.RIGHT)

        temp_video_path = get_temp_file_path(suffix=".mp4")

        new_video = cv.VideoWriter(
            temp_video_path,
            fourcc=cv.VideoWriter_fourcc(*"mp4v"),
            fps=video.fps,
            frameSize=video.shape,
            isColor=True,
        )

        angles_of_interest = AnglesOfInterest({})
        landmark2d_results = Landmark2DResults({})
        landmark3d_results = Landmark3DResults({})

        for result in self._estimator.detect_video(video, ExerciseType.SQUAT):
            if result is None:
                continue

            new_video.write(result.annotated_image)
            frame_count = result.frame_count
            aoi, l2d, l3d = self.postprocessing(result)
            angles_of_interest.root[frame_count] = aoi
            landmark2d_results.root[frame_count] = l2d
            landmark3d_results.root[frame_count] = l3d

        new_video.release()

        self._logger.info(f"Video processed")

        object_key = self.storage_provider.get_processed_video_object_key(
            job["exercise"]["id"], job["media"]["id"]
        )

        self._logger.info(f"Uploading processed video to {object_key}")

        self.storage_provider.upload_object(
            temp_video_path,
            object_key,
        )
        self._logger.info(f"Video uploaded to {object_key}")

        temp_video_path.unlink()
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
            # "angles_of_interest_enum": result.angle_of_interest_enum.model_dump(),
            "angles_of_interest": angles_of_interest.model_dump_json(),
            "landmark2d_results": landmark2d_results.model_dump_json(),
            "landmark3d_results": landmark3d_results.model_dump_json(),
            "completed_at": now(),
        }

        self._repo.update_media(job["media"]["id"], media)

        # TODO: Update the job status

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
        # Turn into a tmp path
        video_path = get_temp_file_path()

        self._logger.info(
            f"Downloading video from {job['media']['original_video_location']}"
        )
        self.storage_provider.download_object(
            job["media"]["original_video_location"], video_path
        )
        self._logger.info(f"Video downloaded to {video_path}")

        self.handle_task(job, video_path)

        # while retry <= MAX_RETRY_COUNT:
        #     try:
        #         if retry > 0:
        #             if retry == MAX_RETRY_COUNT:
        #                 raise MAX_RETRY_ERROR
        #             self._logger.info(f"Retrying task {retry} of {MAX_RETRY_COUNT}")

        #         self.handle_task(job, video_path)
        #     except MAX_RETRY_ERROR:
        #         self._logger.error(MAX_RETRY_ERROR)
        #         break
        #     except Exception as e:
        #         self._logger.error(f"Error processing task: {e}")
        #         retry += 1
        #         time.sleep(3)


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
