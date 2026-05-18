"""Drain Redis FIFO once (RPOP until empty): download input, run analysis pipeline, update Mongo."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import redis
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import ValidationError

from analysis_pipeline import AnalysisPipeline
from database.mongodb.client import get_mongo_database
from database.mongodb.video_queue_persist import (
    VideoProcessingJob,
    exercise_type_from_catalog_key,
    get_set_status_for_job,
    overall_results_to_pose_chart_data,
    persist_video_job_success,
    processed_video_object_key,
    camera_view_from_job_metadata,
)
from session_context import InputSource, SessionContext
from storage import S3StorageProvider
from utils import (
    S3_ACCESS_KEY,
    S3_BUCKET,
    S3_ENDPOINT,
    S3_SECRET,
    get_temp_file_path,
)
from utils.video import Video

_ROOT = Path(__file__).resolve().parent

_LOG_LEVEL_NAME = os.environ.get("LOG_LEVEL", "INFO").upper()
_LOGGING_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)
logging.basicConfig(
    level=_LOGGING_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("video_queue_worker")


def _redis_connect() -> redis.Redis:
    url = os.environ.get("REDIS_URL")
    if not url:
        raise SystemExit("REDIS_URL is required for the video queue worker")
    return redis.Redis.from_url(url, decode_responses=True)


def _queue_key() -> str:
    return os.environ.get("REDIS_VIDEO_QUEUE_KEY", "video_jobs")


def _pipeline_context(video_path: Path, job: VideoProcessingJob) -> SessionContext:
    cam = camera_view_from_job_metadata(job.metadata)
    etype = exercise_type_from_catalog_key(job.exercise_key)
    pm_root = _ROOT / "pose_models"
    return SessionContext(
        user_id=None,
        exercise_type=etype,
        camera_view=cam,
        input_source=InputSource.VIDEO_FILE,
        video_path=str(video_path.resolve()),
        conf_threshold=0.8,
        yolo_detect_weights=str(pm_root / "yolo26n.pt"),
        yolo_seg_weights=str(pm_root / "yolo26n-seg.pt"),
        yolo_pose_weights=str(pm_root / "yolo26n-pose.pt"),
    )


def _run_single_job(s3: S3StorageProvider, job: VideoProcessingJob) -> None:
    jid = job.job_id
    try:
        ObjectId(job.session_id)
        ObjectId(job.set_id)
    except InvalidId as e:
        log.error("[%s] Invalid ObjectId on session/set: %s", jid, e)
        return

    db = get_mongo_database()
    raw_session = db["sessions"].find_one(
        {"_id": ObjectId(job.session_id), "deleted_at": None}
    )
    if not raw_session:
        log.error("[%s] Session %s not found", jid, job.session_id)
        return

    status = get_set_status_for_job(db=db, job=job)
    if status is None:
        log.error(
            "[%s] Set not found (exercise_id=%s set_id=%s)",
            jid,
            job.exercise_id,
            job.set_id,
        )
        return
    if status != "processing":
        log.warning(
            "[%s] Skipping — set status is %r (expected processing)", jid, status
        )
        return

    local_in = get_temp_file_path(suffix=".mp4")
    local_out = get_temp_file_path(suffix=".mp4")
    try:
        log.info("[%s] Download object key=%s", jid, job.r2_key)
        s3.download_object(job.r2_key, Path(local_in))

        ctx = _pipeline_context(Path(local_in), job)
        pipeline = AnalysisPipeline(ctx)
        log.info("[%s] Running AnalysisPipeline", jid)
        overall = pipeline.run_with_video_overlays(
            mp4_output=Path(local_out),
            output_json_path=None,
            mongodb_persist=None,
        )

        chart = overall_results_to_pose_chart_data(overall)
        src_vid = Video(str(Path(local_in).resolve()), ctx.camera_view)
        try:
            vmeta = src_vid.metadata_for_storage()
        finally:
            src_vid.release()

        out_key = processed_video_object_key(job)
        log.info("[%s] Upload processed video key=%s", jid, out_key)
        s3.upload_object(Path(local_out), out_key)

        persist_video_job_success(
            db,
            job=job,
            pose_chart_data=chart,
            video_metadata=vmeta,
            processed_video_uri=out_key,
        )
        log.info("[%s] Persisted Mongo + completed", jid)
    finally:
        for p in (local_in, local_out):
            try:
                Path(p).unlink(missing_ok=True)
            except OSError:
                pass


def main() -> None:
    try:
        s3 = S3StorageProvider(
            bucket=S3_BUCKET,
            access_key=S3_ACCESS_KEY,
            secret_key=S3_SECRET,
            endpoint_url=S3_ENDPOINT,
        )
    except Exception as e:
        log.critical("S3 init failed: %s", e)
        sys.exit(1)

    redis_client = _redis_connect()
    key = _queue_key()
    try:
        while True:
            payload = redis_client.rpop(key)
            if payload is None:
                log.info("Queue %r drained; exiting", key)
                break
            try:
                data = json.loads(payload)
                job = VideoProcessingJob.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                log.exception("Bad job payload: %s raw=%s", e, payload[:500])
                continue
            try:
                _run_single_job(s3, job)
            except Exception:
                log.exception("[%s] Job failed", job.job_id)
    finally:
        redis_client.close()


if __name__ == "__main__":
    main()
