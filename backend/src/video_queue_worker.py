"""Shared video queue job processing (Redis drain + RunPod handler)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId

from analysis_pipeline import AnalysisPipeline
from database.mongodb.client import get_mongo_database
from database.mongodb.video_queue_persist import (
    VideoProcessingJob,
    camera_view_from_job_metadata,
    exercise_type_from_catalog_key,
    get_set_status_for_job,
    overall_results_to_pose_chart_data,
    persist_video_job_success,
    processed_video_object_key,
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
from utils.video_web import remux_mp4_for_browser_playback

_ROOT = Path(__file__).resolve().parent

_LOG_LEVEL_NAME = os.environ.get("LOG_LEVEL", "INFO").upper()
_LOGGING_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)
logging.basicConfig(
    level=_LOGGING_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("video_queue_worker")


def print_gpu_status() -> None:
    """Stdout-only CUDA probe for RunPod / Docker debugging."""
    import torch

    available = torch.cuda.is_available()
    print(f"[gpu] cuda_available={available}", flush=True)
    if available:
        print(f"[gpu] device_count={torch.cuda.device_count()}", flush=True)
        print(f"[gpu] device_0={torch.cuda.get_device_name(0)}", flush=True)
    else:
        print("[gpu] no CUDA device visible (CPU path)", flush=True)


def create_s3_provider() -> S3StorageProvider:
    return S3StorageProvider(
        bucket=S3_BUCKET,
        access_key=S3_ACCESS_KEY,
        secret_key=S3_SECRET,
        endpoint_url=S3_ENDPOINT,
    )


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


def run_video_job(s3: S3StorageProvider, job: VideoProcessingJob) -> None:
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
    local_out_web = get_temp_file_path(suffix=".mp4")
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
        log.info("[%s] Remux processed video for web playback", jid)
        remux_mp4_for_browser_playback(Path(local_out), Path(local_out_web))
        log.info("[%s] Upload processed video key=%s", jid, out_key)
        s3.upload_object(Path(local_out_web), out_key)

        persist_video_job_success(
            db,
            job=job,
            pose_chart_data=chart,
            video_metadata=vmeta,
            processed_video_uri=out_key,
        )
        log.info("[%s] Persisted Mongo + completed", jid)
    finally:
        for p in (local_in, local_out, local_out_web):
            try:
                Path(p).unlink(missing_ok=True)
            except OSError:
                pass


def init_s3_or_exit() -> S3StorageProvider:
    try:
        return create_s3_provider()
    except Exception as e:
        log.critical("S3 init failed: %s", e)
        sys.exit(1)
