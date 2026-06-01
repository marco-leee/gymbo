"""Tests for Video orientation normalization."""

from __future__ import annotations

import numpy as np

from utils.video import CameraView, Video, rotate_frame
from utils.video_probe import VideoStreamProbe, display_dimensions


def test_rotate_frame_90_swaps_shape() -> None:
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    rotated = rotate_frame(frame, 90)
    assert rotated.shape == (1920, 1080, 3)


def test_rotate_frame_0_is_noop() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    assert rotate_frame(frame, 0) is frame


def test_video_applies_rotation_and_display_dimensions(monkeypatch) -> None:
    import utils.video as uv

    class FakeCap:
        def __init__(self, *_args, **_kw):
            self._reads = 0

        def isOpened(self):
            return True

        def get(self, p):
            return {
                uv.cv2.CAP_PROP_FPS: 30.0,
                uv.cv2.CAP_PROP_FRAME_WIDTH: 1920.0,
                uv.cv2.CAP_PROP_FRAME_HEIGHT: 1080.0,
                uv.cv2.CAP_PROP_FRAME_COUNT: 2.0,
            }.get(p, 0.0)

        def read(self):
            self._reads += 1
            if self._reads <= 2:
                return True, np.zeros((1080, 1920, 3), dtype=np.uint8)
            return False, None

        def release(self):
            pass

    monkeypatch.setattr(uv.cv2, "VideoCapture", lambda *_a, **_k: FakeCap())
    monkeypatch.setattr(
        uv,
        "probe_video_stream",
        lambda _path: VideoStreamProbe(1920, 1080, 90),
    )

    vid = Video("/tmp/fake.mp4", CameraView.RIGHT)
    assert vid.coded_width == 1920
    assert vid.coded_height == 1080
    assert vid.rotation_deg == 90
    assert vid.width == 1080
    assert vid.height == 1920
    assert vid.shape == (1080, 1920)

    frames = list(vid.get_frames())
    assert len(frames) == 2
    for _idx, _ts, frame in frames:
        assert frame.shape[:2] == (1920, 1080)


def test_video_ignores_ffprobe_when_expected_matches_coded(monkeypatch) -> None:
    """Regression for portrait phone video with stale ffprobe rotation metadata."""
    import utils.video as uv

    class FakeCap:
        def __init__(self, *_args, **_kw):
            self._reads = 0

        def isOpened(self):
            return True

        def get(self, p):
            return {
                uv.cv2.CAP_PROP_FPS: 30.0,
                uv.cv2.CAP_PROP_FRAME_WIDTH: 480.0,
                uv.cv2.CAP_PROP_FRAME_HEIGHT: 848.0,
                uv.cv2.CAP_PROP_FRAME_COUNT: 2.0,
            }.get(p, 0.0)

        def read(self):
            self._reads += 1
            if self._reads <= 2:
                return True, np.zeros((848, 480, 3), dtype=np.uint8)
            return False, None

        def release(self):
            pass

    monkeypatch.setattr(uv.cv2, "VideoCapture", lambda *_a, **_k: FakeCap())
    monkeypatch.setattr(
        uv,
        "probe_video_stream",
        lambda _path: VideoStreamProbe(480, 848, 270),
    )

    vid = Video(
        "/tmp/fake.mp4",
        CameraView.RIGHT,
        expected_display_size=(480, 848),
    )
    assert vid.rotation_deg == 0
    assert vid.width == 480
    assert vid.height == 848

    frames = list(vid.get_frames())
    assert len(frames) == 2
    for _idx, _ts, frame in frames:
        assert frame.shape[:2] == (848, 480)


def test_video_infers_rotation_from_expected_display_size(monkeypatch) -> None:
    import utils.video as uv

    class FakeCap:
        def __init__(self, *_args, **_kw):
            self._reads = 0

        def isOpened(self):
            return True

        def get(self, p):
            return {
                uv.cv2.CAP_PROP_FPS: 30.0,
                uv.cv2.CAP_PROP_FRAME_WIDTH: 1920.0,
                uv.cv2.CAP_PROP_FRAME_HEIGHT: 1080.0,
                uv.cv2.CAP_PROP_FRAME_COUNT: 1.0,
            }.get(p, 0.0)

        def read(self):
            self._reads += 1
            if self._reads == 1:
                return True, np.zeros((1080, 1920, 3), dtype=np.uint8)
            return False, None

        def release(self):
            pass

    monkeypatch.setattr(uv.cv2, "VideoCapture", lambda *_a, **_k: FakeCap())
    monkeypatch.setattr(
        uv,
        "probe_video_stream",
        lambda _path: VideoStreamProbe(1920, 1080, 0),
    )

    vid = Video(
        "/tmp/fake.mp4",
        CameraView.RIGHT,
        expected_display_size=(1080, 1920),
    )
    assert vid.rotation_deg == 90
    assert display_dimensions(vid.coded_width, vid.coded_height, vid.rotation_deg) == (
        1080,
        1920,
    )


def test_metadata_for_storage_uses_display_dimensions(monkeypatch) -> None:
    import utils.video as uv

    class FakeCap:
        def __init__(self, *_args, **_kw):
            self._reads = 0

        def isOpened(self):
            return True

        def get(self, p):
            return {
                uv.cv2.CAP_PROP_FPS: 30.0,
                uv.cv2.CAP_PROP_FRAME_WIDTH: 1920.0,
                uv.cv2.CAP_PROP_FRAME_HEIGHT: 1080.0,
                uv.cv2.CAP_PROP_FRAME_COUNT: 90.0,
            }.get(p, 0.0)

        def read(self):
            self._reads += 1
            if self._reads == 1:
                return True, np.zeros((1080, 1920, 3), dtype=np.uint8)
            return False, None

        def release(self):
            pass

    monkeypatch.setattr(uv.cv2, "VideoCapture", lambda *_a, **_k: FakeCap())
    monkeypatch.setattr(
        uv,
        "probe_video_stream",
        lambda _path: VideoStreamProbe(1920, 1080, 90),
    )

    vid = Video("/tmp/fake.mp4", CameraView.RIGHT)
    try:
        meta = vid.metadata_for_storage()
    finally:
        vid.release()

    assert meta["video_width"] == 1080
    assert meta["video_height"] == 1920
