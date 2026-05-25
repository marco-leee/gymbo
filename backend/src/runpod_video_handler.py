"""RunPod Serverless queue worker for async video processing jobs."""

from __future__ import annotations

import logging

import runpod

from database.mongodb.video_queue_persist import VideoProcessingJob

log = logging.getLogger("runpod_video_handler")


def parse_runpod_job(job: dict) -> VideoProcessingJob:
    raw = job.get("input")
    if raw is None:
        raise ValueError(
            'Missing job["input"]; submit with RunPod { "input": { ... } }'
        )
    return VideoProcessingJob.model_validate(raw)


_s3 = None


def handler(job: dict) -> dict:
    global _s3
    from video_queue_worker import create_s3_provider, run_video_job

    runpod_id = job.get("id")
    log.debug(
        "RunPod handler entry runpod_id=%s input_keys=%s",
        runpod_id,
        sorted((job.get("input") or {}).keys()),
    )

    if _s3 is None:
        _s3 = create_s3_provider()
    model = parse_runpod_job(job)
    try:
        run_video_job(_s3, model)
    except Exception:
        log.debug("[%s] handler failed runpod_id=%s", model.job_id, runpod_id)
        raise

    log.info("[%s] handler completed status=completed", model.job_id)
    return {"status": "completed", "job_id": model.job_id}


if __name__ == "__main__":
    from video_queue_worker import print_gpu_status

    print_gpu_status()
    runpod.serverless.start({"handler": handler})
