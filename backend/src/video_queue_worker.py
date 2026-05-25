"""Shared video queue job processing (Redis drain + RunPod handler)."""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId

from analysis_pipeline import AnalysisPipeline
from database.mongodb import collections as col
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
from utils.video import CameraView, Video
from utils.video_probe import probe_video_duration_sec
from utils.video_web import remux_mp4_for_browser_playback

_ROOT = Path(__file__).resolve().parent

_LOG_LEVEL_NAME = os.environ.get("LOG_LEVEL", "INFO").upper()
_LOGGING_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)
logging.basicConfig(
    level=_LOGGING_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("video_queue_worker")

_DURATION_MISMATCH_WARN_SEC = 1.0
_DURATION_DECODE_FAIL_SEC = 2.0


def print_gpu_status() -> None:
    """Stdout-only CUDA probe for RunPod / Docker debugging."""
    import torch

    print(
        f"[gpu] torch={torch.__version__} cuda_build={torch.version.cuda}",
        flush=True,
    )
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
        yolo_detect_weights=str(pm_root / "yolo26x.pt"),
        yolo_seg_weights=str(pm_root / "yolo26x-seg.pt"),
        yolo_pose_weights=str(pm_root / "yolo26x-pose.pt"),
    )


def _validate_downloaded_video(
    *,
    job_id: str,
    local_path: Path,
    s3_bytes: int,
    camera_view: CameraView,
    upload_metadata: dict | None,
) -> None:
    """Fail fast on truncated downloads; warn on duration probe mismatches."""
    local_path = Path(local_path)
    local_bytes = local_path.stat().st_size
    ffprobe_sec = probe_video_duration_sec(local_path)

    vid = Video(str(local_path.resolve()), camera_view)
    try:
        opencv_duration = vid.duration
        opencv_frames = vid.total_frames
        opencv_fps = vid.fps
    finally:
        vid.release()

    log.info(
        "[%s] video probe s3_bytes=%s local_bytes=%s ffprobe_sec=%s "
        "opencv_fps=%s opencv_frames=%s opencv_duration_sec=%.2f path=%s",
        job_id,
        s3_bytes,
        local_bytes,
        ffprobe_sec,
        opencv_fps,
        opencv_frames,
        opencv_duration,
        local_path,
    )

    if upload_metadata:
        up_dur = upload_metadata.get("duration_sec")
        up_frames = upload_metadata.get("total_frames")
        log.debug(
            "[%s] upload video_metadata duration_sec=%s total_frames=%s",
            job_id,
            up_dur,
            up_frames,
        )
        if isinstance(up_dur, (int, float)) and opencv_duration > 0:
            if abs(float(up_dur) - opencv_duration) > _DURATION_MISMATCH_WARN_SEC:
                log.warning(
                    "[%s] worker OpenCV duration %.2fs differs from upload "
                    "metadata %.2fs",
                    job_id,
                    opencv_duration,
                    float(up_dur),
                )

    if ffprobe_sec is not None and opencv_duration > 0:
        if abs(ffprobe_sec - opencv_duration) > _DURATION_MISMATCH_WARN_SEC:
            log.warning(
                "[%s] ffprobe duration %.2fs vs OpenCV %.2fs",
                job_id,
                ffprobe_sec,
                opencv_duration,
            )
        if (
            ffprobe_sec > opencv_duration + _DURATION_DECODE_FAIL_SEC
            and ffprobe_sec > 5.0
        ):
            raise RuntimeError(
                f"[{job_id}] OpenCV decode duration ({opencv_duration:.2f}s) is much "
                f"shorter than ffprobe ({ffprobe_sec:.2f}s); input may be corrupt "
                "or partially readable"
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

    set_doc = db[col.EXERCISE_SETS].find_one(
        {
            "_id": ObjectId(job.set_id),
            "exercise_id": ObjectId(job.exercise_id),
        }
    )
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

    upload_metadata = None
    if set_doc and isinstance(set_doc.get("video_metadata"), dict):
        upload_metadata = set_doc["video_metadata"]

    log.info(
        "[%s] Job accepted r2_key=%s exercise_key=%s set_status=%s",
        jid,
        job.r2_key,
        job.exercise_key,
        status,
    )
    log.debug("[%s] job payload=%s", jid, job.model_dump())

    local_in = get_temp_file_path(suffix=".mp4")
    local_out = get_temp_file_path(suffix=".mp4")
    local_out_web = get_temp_file_path(suffix=".mp4")
    try:
        log.info("[%s] Download object key=%s", jid, job.r2_key)
        t_dl = time.perf_counter()
        s3_bytes = s3.download_object(job.r2_key, Path(local_in))
        log.info(
            "[%s] Download stage elapsed_sec=%.2f", jid, time.perf_counter() - t_dl
        )

        cam = camera_view_from_job_metadata(job.metadata)
        _validate_downloaded_video(
            job_id=jid,
            local_path=Path(local_in),
            s3_bytes=s3_bytes,
            camera_view=cam,
            upload_metadata=upload_metadata,
        )

        ctx = _pipeline_context(Path(local_in), job)
        log.info(
            "[%s] Pipeline config camera_view=%s conf_threshold=%s detect=%s pose=%s seg=%s",
            jid,
            ctx.camera_view.value,
            ctx.conf_threshold,
            ctx.yolo_detect_weights,
            ctx.yolo_pose_weights,
            ctx.yolo_seg_weights,
        )

        pipeline = AnalysisPipeline(ctx)
        log.info("[%s] Running AnalysisPipeline", jid)
        t_pipe = time.perf_counter()
        overall, pipe_stats = pipeline.run_with_video_overlays(
            mp4_output=Path(local_out),
            output_json_path=None,
            mongodb_persist=None,
        )
        log.info(
            "[%s] Pipeline stage elapsed_sec=%.2f chart_points=%s overall_results=%s %s",
            jid,
            time.perf_counter() - t_pipe,
            len(overall_results_to_pose_chart_data(overall)),
            len(overall.results),
            pipe_stats.summary(),
        )

        chart = overall_results_to_pose_chart_data(overall)
        src_vid = Video(str(Path(local_in).resolve()), ctx.camera_view)
        try:
            vmeta = src_vid.metadata_for_storage()
        finally:
            src_vid.release()

        out_key = processed_video_object_key(job)
        log.info("[%s] Remux processed video for web playback", jid)
        t_remux = time.perf_counter()
        remux_mp4_for_browser_playback(Path(local_out), Path(local_out_web))
        raw_out_bytes = Path(local_out).stat().st_size
        web_out_bytes = Path(local_out_web).stat().st_size
        log.info(
            "[%s] Remux stage elapsed_sec=%.2f raw_out_bytes=%s web_out_bytes=%s",
            jid,
            time.perf_counter() - t_remux,
            raw_out_bytes,
            web_out_bytes,
        )

        log.info("[%s] Upload processed video key=%s", jid, out_key)
        t_up = time.perf_counter()
        s3.upload_object(Path(local_out_web), out_key)
        log.info("[%s] Upload stage elapsed_sec=%.2f", jid, time.perf_counter() - t_up)

        persist_video_job_success(
            db,
            job=job,
            pose_chart_data=chart,
            video_metadata=vmeta,
            processed_video_uri=out_key,
        )
        log.info(
            "[%s] Persisted Mongo + completed processed_video_uri=%s worker_vmeta_duration_sec=%s",
            jid,
            out_key,
            vmeta.get("duration_sec"),
        )
    except Exception as e:
        log.error("[%s] Error processing video: %s", jid, e)
        raise e
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
