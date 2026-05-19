"""Unit tests for video queue persistence helpers."""

from unittest.mock import MagicMock, patch

from bson import ObjectId

from database.mongodb.video_queue_persist import (
    VideoProcessingJob,
    overall_results_to_pose_chart_data,
    persist_set_biometrics,
    persist_video_job_success,
)
from models.overall_results import OverallResult, OverallResults
from utils.video import CameraView, Video


def test_overall_results_to_pose_chart_maps_kips():
    o = OverallResults(
        results=[
            OverallResult(
                idx=0,
                timestamp=0.05,
                pose_estimation_result={},
                segmentation_result={},
                biometrics={
                    "key_interest_points_2d": {
                        "INSIDE_KNEE": {"angle": 91},
                        "OUTSIDE_HIP": {"angle": 102},
                    }
                },
            ),
            OverallResult(
                idx=1,
                timestamp=0.1,
                pose_estimation_result={},
                segmentation_result={},
                biometrics=None,
            ),
        ],
        fps=30,
        video_width=640,
        video_height=480,
        camera_view="RIGHT",
        exercise_type="SQUAT",
    )
    pts = overall_results_to_pose_chart_data(o)
    assert len(pts) == 1
    assert pts[0] == {
        "frame": 0,
        "timestampSec": 0.05,
        "insideKnee": 91.0,
        "outsideHip": 102.0,
    }


def test_video_metadata_for_storage(monkeypatch):
    import utils.video as uv

    class FakeCap:
        def __init__(self, *_args, **_kw):
            pass

        def isOpened(self):
            return True

        def get(self, p):
            return {
                uv.cv2.CAP_PROP_FPS: 30.0,
                uv.cv2.CAP_PROP_FRAME_WIDTH: 640.0,
                uv.cv2.CAP_PROP_FRAME_HEIGHT: 480.0,
                uv.cv2.CAP_PROP_FRAME_COUNT: 90.0,
            }.get(p, 0.0)

        def read(self):
            return False, None

        def release(self):
            pass

    monkeypatch.setattr(uv.cv2, "VideoCapture", lambda *_a, **_k: FakeCap())

    vid = Video("/tmp/not-read.mp4", CameraView.RIGHT)
    try:
        m = vid.metadata_for_storage()
    finally:
        vid.release()
    assert m == {
        "camera_view": "RIGHT",
        "fps": 30,
        "video_width": 640,
        "video_height": 480,
        "total_frames": 90,
        "duration_sec": 3.0,
    }


def test_persist_set_biometrics_upserts_via_repo():
    db = MagicMock()
    set_id = ObjectId()
    chart = [{"frame": 0, "timestampSec": 0.1, "insideKnee": 90.0, "outsideHip": 100.0}]
    repo = MagicMock()

    with patch(
        "database.mongodb.video_queue_persist.set_biometrics_repo", return_value=repo
    ):
        persist_set_biometrics(db, set_id=set_id, pose_chart_data=chart, version=1)

    repo.upsert_pose_chart.assert_called_once_with(set_id, chart, version=1)


def test_persist_video_job_success_writes_set_biometrics_not_exercise_sets_chart():
    session_id = ObjectId()
    set_id = ObjectId()
    exercise_id = ObjectId()
    job = VideoProcessingJob(
        session_id=str(session_id),
        exercise_id=str(exercise_id),
        set_id=str(set_id),
        r2_key="k",
        job_id="j1",
    )
    chart = [{"frame": 0, "timestampSec": 0.1, "insideKnee": 90.0, "outsideHip": 100.0}]
    vmeta = {"camera_view": "RIGHT", "fps": 30}

    db = MagicMock()
    sets_coll = MagicMock()
    sessions_coll = MagicMock()
    sets_update = MagicMock()
    sets_update.matched_count = 1
    sets_coll.update_one.return_value = sets_update

    def get_coll(name):
        if name == "exercise_sets":
            return sets_coll
        if name == "sessions":
            return sessions_coll
        return MagicMock()

    db.__getitem__.side_effect = get_coll

    with patch("database.mongodb.video_queue_persist.persist_set_biometrics") as persist_bio:
        persist_video_job_success(
            db,
            job=job,
            pose_chart_data=chart,
            video_metadata=vmeta,
            processed_video_uri="processed/key.mp4",
        )

    persist_bio.assert_called_once_with(db, set_id=set_id, pose_chart_data=chart, version=1)

    sets_coll.update_one.assert_called_once()
    update_filter, update_doc = sets_coll.update_one.call_args[0]
    assert update_filter == {"_id": set_id, "exercise_id": exercise_id}
    assert "pose_chart_data" not in update_doc["$set"]
    assert update_doc["$set"]["video_metadata"] == vmeta
    assert update_doc["$set"]["processed_video_uri"] == "processed/key.mp4"
    assert update_doc["$set"]["app_status"] == "completed"
    sessions_coll.update_one.assert_called_once()
