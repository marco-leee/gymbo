"""Video worker download validation and pipeline frame accounting."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from pipeline.enums import FramePerceptionStatus
from pipeline.frame_state import FramePerceptionState
from pipeline.run_stats import PipelineRunStats
from pipeline.schemas import FramePerceptionRecord, FrameSize
from storage.S3 import S3StorageProvider


def test_s3_download_raises_on_size_mismatch(tmp_path: Path) -> None:
    provider = S3StorageProvider("b", "ak", "sk", endpoint_url="http://localhost:9000")
    provider.client = MagicMock()
    provider.client.head_object.return_value = {
        "ContentLength": 100,
        "ContentType": "video/mp4",
        "ETag": '"abc"',
    }
    dest = tmp_path / "video.mp4"

    def _write_short(_bucket: str, _key: str, path: str) -> None:
        Path(path).write_bytes(b"x" * 50)

    provider.client.download_file.side_effect = _write_short

    with pytest.raises(ValueError, match="size mismatch"):
        provider.download_object("session/foo/video.mp4", dest)


def test_s3_download_returns_content_length(tmp_path: Path) -> None:
    provider = S3StorageProvider("b", "ak", "sk", endpoint_url="http://localhost:9000")
    provider.client = MagicMock()
    provider.client.head_object.return_value = {"ContentLength": 4, "ContentType": "video/mp4"}

    def _write_exact(_bucket: str, _key: str, path: str) -> None:
        Path(path).write_bytes(b"1234")

    provider.client.download_file.side_effect = _write_exact
    dest = tmp_path / "video.mp4"
    assert provider.download_object("k", dest) == 4
    assert dest.stat().st_size == 4


@patch("video_queue_worker.Video")
@patch("video_queue_worker.probe_video_duration_sec", return_value=4.0)
def test_validate_downloaded_video_warns_on_upload_metadata_mismatch(
    mock_probe: MagicMock,
    mock_video_cls: MagicMock,
) -> None:
    from video_queue_worker import _validate_downloaded_video
    from utils.video import CameraView

    mock_vid = MagicMock()
    mock_vid.duration = 4.0
    mock_vid.total_frames = 120
    mock_vid.fps = 30
    mock_vid.coded_width = 1920
    mock_vid.coded_height = 1080
    mock_vid.width = 1080
    mock_vid.height = 1920
    mock_vid.rotation_deg = 90
    mock_video_cls.return_value = mock_vid

    path = Path("/tmp/fake.mp4")
    with patch.object(Path, "stat") as mock_stat:
        mock_stat.return_value = MagicMock(st_size=1000)
        _validate_downloaded_video(
            job_id="job-1",
            local_path=path,
            s3_bytes=1000,
            camera_view=CameraView.RIGHT,
            upload_metadata={"duration_sec": 10.0, "total_frames": 300},
        )


@patch("video_queue_worker.Video")
@patch("video_queue_worker.probe_video_duration_sec", return_value=4.0)
def test_validate_downloaded_video_warns_on_display_dimension_mismatch(
    mock_probe: MagicMock,
    mock_video_cls: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    from video_queue_worker import _validate_downloaded_video
    from utils.video import CameraView

    caplog.set_level(logging.WARNING)

    mock_vid = MagicMock()
    mock_vid.duration = 4.0
    mock_vid.total_frames = 120
    mock_vid.fps = 30
    mock_vid.coded_width = 1920
    mock_vid.coded_height = 1080
    mock_vid.width = 1080
    mock_vid.height = 1920
    mock_vid.rotation_deg = 90
    mock_video_cls.return_value = mock_vid

    path = Path("/tmp/fake.mp4")
    with patch.object(Path, "stat") as mock_stat:
        mock_stat.return_value = MagicMock(st_size=1000)
        _validate_downloaded_video(
            job_id="job-1",
            local_path=path,
            s3_bytes=1000,
            camera_view=CameraView.RIGHT,
            upload_metadata={
                "duration_sec": 4.0,
                "video_width": 720,
                "video_height": 1280,
            },
        )

    assert any(
        "normalized display dimensions" in record.message for record in caplog.records
    )


@patch("video_queue_worker.Video")
@patch("video_queue_worker.probe_video_duration_sec", return_value=45.0)
def test_validate_downloaded_video_raises_on_ffprobe_opencv_gap(
    mock_probe: MagicMock,
    mock_video_cls: MagicMock,
) -> None:
    from video_queue_worker import _validate_downloaded_video
    from utils.video import CameraView

    mock_vid = MagicMock()
    mock_vid.duration = 4.0
    mock_vid.total_frames = 120
    mock_vid.fps = 30
    mock_video_cls.return_value = mock_vid

    path = Path("/tmp/fake.mp4")
    with patch.object(Path, "stat") as mock_stat:
        mock_stat.return_value = MagicMock(st_size=5000)
        with pytest.raises(RuntimeError, match="shorter than ffprobe"):
            _validate_downloaded_video(
                job_id="job-1",
                local_path=path,
                s3_bytes=5000,
                camera_view=CameraView.RIGHT,
                upload_metadata=None,
            )


def test_pipeline_run_stats_summary() -> None:
    stats = PipelineRunStats(
        frames_decoded=100,
        frames_written=100,
        frames_ok=40,
        status_counts={"ok": 40, "no_detections": 60},
    )
    text = stats.summary()
    assert "decoded=100" in text
    assert "written=100" in text
    assert "ok=40" in text


@patch("analysis_pipeline.render_overlays", side_effect=lambda frame, _rec: frame)
@patch("analysis_pipeline.YOLO")
@patch("analysis_pipeline.Video")
def test_run_with_video_overlays_writes_every_decoded_frame(
    mock_video_cls: MagicMock,
    mock_yolo: MagicMock,
    _mock_render: MagicMock,
    tmp_path: Path,
) -> None:
    from analysis_pipeline import AnalysisPipeline
    from session_context import InputSource, SessionContext
    from models.exercise import ExerciseType
    from utils.video import CameraView

    frames = [
        (0, 0.0, np.zeros((48, 64, 3), dtype=np.uint8)),
        (1, 0.033, np.zeros((48, 64, 3), dtype=np.uint8)),
        (2, 0.066, np.zeros((48, 64, 3), dtype=np.uint8)),
    ]

    mock_vid = MagicMock()
    mock_vid.width = 64
    mock_vid.height = 48
    mock_vid.fps = 30
    mock_vid.duration = 0.1
    mock_vid.total_frames = 3
    mock_vid.get_frames.return_value = iter(frames)
    mock_video_cls.return_value = mock_vid

    mock_writer = MagicMock()
    mock_writer.isOpened.return_value = True

    fail_rec = FramePerceptionRecord(
        idx=0,
        timestamp=0.0,
        frame=FrameSize(width=64, height=48),
        status=FramePerceptionStatus.NO_DETECTIONS,
    )

    def fake_perceive(frame, count, timestamp, **kwargs):
        return FramePerceptionState(None, None, None, None, fail_rec)

    ctx = SessionContext(
        user_id=None,
        exercise_type=ExerciseType.SQUAT,
        camera_view=CameraView.RIGHT,
        input_source=InputSource.VIDEO_FILE,
        video_path=str(tmp_path / "in.mp4"),
        conf_threshold=0.8,
    )
    pipe = AnalysisPipeline(ctx)
    pipe._perceive_frame = fake_perceive  # type: ignore[method-assign]

    out_mp4 = tmp_path / "out.mp4"
    with patch("analysis_pipeline.cv2.VideoWriter", return_value=mock_writer):
        _overall, stats = pipe.run_with_video_overlays(mp4_output=out_mp4)

    assert stats.frames_decoded == 3
    assert stats.frames_written == 3
    assert stats.frames_ok == 0
    assert mock_writer.write.call_count == 3
