"""Persist video queue worker output to app-v2 Mongo (split: exercise_sets + sessions header)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo.database import Database

from models.exercise import ExerciseType
from models.overall_results import OverallResults
from utils.video import CameraView

SESSIONS = "sessions"
EXERCISE_SETS = "exercise_sets"


class VideoProcessingJob(BaseModel):
    session_id: str
    exercise_id: str
    set_id: str
    r2_key: str
    job_id: str
    exercise_key: str | None = None
    metadata: dict[str, str] | None = Field(default=None)


def exercise_type_from_catalog_key(exercise_key: str | None) -> ExerciseType:
    if exercise_key:
        mapping = {
            "squat": ExerciseType.SQUAT,
            "deadlift": ExerciseType.DEADLIFT,
            "lunges": ExerciseType.LUNGE,
        }
        mapped = mapping.get(exercise_key.lower().strip())
        if mapped is not None:
            return mapped
    return ExerciseType.SQUAT


def camera_view_from_job_metadata(metadata: dict[str, str] | None) -> CameraView:
    raw = None
    if metadata:
        raw = metadata.get("camera_view") or metadata.get("CAMERA_VIEW")
    if raw:
        token = raw.strip().upper()
        try:
            return CameraView[token]
        except KeyError:
            pass
    return CameraView.RIGHT


def _split_visible_status(doc: dict[str, Any]) -> str | None:
    app = doc.get("app_status")
    if isinstance(app, str) and app in ("pending", "processing", "completed"):
        return app
    if doc.get("original_video_uri") or doc.get("video_url"):
        return "completed"
    return "pending"


def get_set_status_for_job(*, db: Database, job: VideoProcessingJob) -> str | None:
    doc = db[EXERCISE_SETS].find_one(
        {"_id": ObjectId(job.set_id), "exercise_id": job.exercise_id}
    )
    return _split_visible_status(doc) if doc else None


def overall_results_to_pose_chart_data(overall: OverallResults) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in overall.results:
        if row.biometrics is None:
            continue
        kips = row.biometrics.get("key_interest_points_2d")
        if not isinstance(kips, dict):
            continue
        ik = kips.get("INSIDE_KNEE")
        oh = kips.get("OUTSIDE_HIP")
        if not isinstance(ik, dict) or not isinstance(oh, dict):
            continue
        ia, oa = ik.get("angle"), oh.get("angle")
        if ia is None or oa is None:
            continue
        out.append(
            {
                "frame": row.idx,
                "timestampSec": float(row.timestamp),
                "insideKnee": float(ia),
                "outsideHip": float(oa),
            }
        )
    return out


def processed_video_object_key(job: VideoProcessingJob) -> str:
    return (
        f"session/{job.session_id}/exercises/{job.exercise_id}"
        f"/sets/{job.set_id}/processed.mp4"
    )


def persist_video_job_success(
    db: Database,
    *,
    job: VideoProcessingJob,
    pose_chart_data: list[dict[str, Any]],
    video_metadata: dict[str, Any],
    processed_video_uri: str,
) -> None:
    now = datetime.now(UTC)
    sid = ObjectId(job.session_id)
    sessions_coll = db[SESSIONS]

    r = db[EXERCISE_SETS].update_one(
        {"_id": ObjectId(job.set_id), "exercise_id": job.exercise_id},
        {
            "$set": {
                "pose_chart_data": pose_chart_data,
                "video_metadata": video_metadata,
                "processed_video_uri": processed_video_uri,
                "app_status": "completed",
                "updated_at": now,
            }
        },
    )
    if r.matched_count == 0:
        raise ValueError("exercise_sets row not found for job")
    sessions_coll.update_one(
        {"_id": sid, "deleted_at": None}, {"$set": {"updated_at": now}}
    )
