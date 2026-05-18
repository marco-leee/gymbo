"""Unit tests for video queue persistence helpers."""

from models.overall_results import OverallResult, OverallResults
from utils.video import CameraView, Video

from database.mongodb.video_queue_persist import overall_results_to_pose_chart_data


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
