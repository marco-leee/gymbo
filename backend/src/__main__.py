"""Drain Redis FIFO once (RPOP until empty): download input, run analysis pipeline, update Mongo."""

from __future__ import annotations

import json
import os
import sys

import redis
from pydantic import ValidationError

from database.mongodb.video_queue_persist import VideoProcessingJob
from video_queue_worker import (
    init_s3_or_exit,
    log,
    print_gpu_status,
    run_video_job,
)


def _redis_connect() -> redis.Redis:
    url = os.environ.get("REDIS_URL")
    if not url:
        raise SystemExit("REDIS_URL is required for the video queue worker")
    return redis.Redis.from_url(url, decode_responses=True)


def _queue_key() -> str:
    return os.environ.get("REDIS_VIDEO_QUEUE_KEY", "video_jobs")


def main() -> None:
    print_gpu_status()
    s3 = init_s3_or_exit()
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
                run_video_job(s3, job)
            except Exception:
                log.exception("[%s] Job failed", job.job_id)
    finally:
        redis_client.close()


if __name__ == "__main__":
    main()
