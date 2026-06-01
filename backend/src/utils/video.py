from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Self

import cv2
import numpy as np

from utils.video_probe import (
    display_dimensions,
    probe_video_stream,
    resolve_rotation_deg,
)

log = logging.getLogger(__name__)


class CameraView(Enum):
    # TOP = "TOP"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    # FRONT = "FRONT"
    # BACK = "BACK"
    # BOTTOM = "BOTTOM"

    @staticmethod
    def from_string(view: str) -> Self:
        return CameraView[view.upper()]


def rotate_frame(frame: np.ndarray, rotation_deg: int) -> np.ndarray:
    """Apply display rotation to a decoded BGR frame."""
    if rotation_deg == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if rotation_deg == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if rotation_deg == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame


class Video:
    def __init__(
        self,
        video_path: str,
        camera_view: CameraView,
        *,
        expected_display_size: tuple[int, int] | None = None,
    ):
        self.video_path = video_path
        self.camera_view = camera_view
        self.video = cv2.VideoCapture(video_path)

        assert self.video.isOpened(), "Cannot open video"

        self.fps = int(self.video.get(cv2.CAP_PROP_FPS))
        self.coded_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.coded_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / float(self.fps) if self.fps else 0.0

        ok, peek = self.video.read()
        frame_size = None
        if ok and peek is not None:
            frame_size = (peek.shape[1], peek.shape[0])
        self._peek_frame: np.ndarray | None = peek if ok else None

        stream_probe = probe_video_stream(Path(video_path))
        probe_deg = stream_probe.rotation_deg if stream_probe else 0

        self.rotation_deg = self._resolve_rotation(
            probe_deg=probe_deg,
            expected_display_size=expected_display_size,
            frame_size=frame_size,
        )
        self.width, self.height = display_dimensions(
            self.coded_width, self.coded_height, self.rotation_deg
        )
        self.shape = (self.width, self.height)

    def _resolve_rotation(
        self,
        *,
        probe_deg: int,
        expected_display_size: tuple[int, int] | None,
        frame_size: tuple[int, int] | None,
    ) -> int:
        rotation_deg = resolve_rotation_deg(
            coded_w=self.coded_width,
            coded_h=self.coded_height,
            probe_deg=probe_deg,
            expected_display_size=expected_display_size,
            frame_size=frame_size,
        )

        if probe_deg != rotation_deg:
            log.info(
                "Rotation for %s: ffprobe=%s° resolved=%s° coded=%sx%s "
                "frame=%s expected=%s",
                self.video_path,
                probe_deg,
                rotation_deg,
                self.coded_width,
                self.coded_height,
                frame_size,
                expected_display_size,
            )
        elif rotation_deg != 0:
            disp_w, disp_h = display_dimensions(
                self.coded_width, self.coded_height, rotation_deg
            )
            log.info(
                "Video %s coded=%sx%s rotation=%s° display=%sx%s",
                self.video_path,
                self.coded_width,
                self.coded_height,
                rotation_deg,
                disp_w,
                disp_h,
            )

        return rotation_deg

    def metadata_for_storage(self) -> dict[str, Any]:
        """Mongo `video_metadata` document (ExerciseSetVideoMetadata schema)."""
        fps = self.fps if self.fps > 0 else 30
        return {
            "camera_view": self.camera_view.value,
            "fps": fps,
            "video_width": self.width,
            "video_height": self.height,
            "total_frames": self.total_frames,
            "duration_sec": self.duration,
        }

    def release(self) -> None:
        """Close the capture without iterating (see :meth:`get_frames`)."""
        cap = self.video
        if cap is not None and getattr(cap, "isOpened", lambda: False)():
            cap.release()

    def get_frames(self):
        count = 0

        if self._peek_frame is not None:
            timestamp = 0.0 if self.fps else 0.0
            yield count, timestamp, rotate_frame(self._peek_frame, self.rotation_deg)
            self._peek_frame = None
            count += 1

        has_next, frame = self.video.read()

        while has_next:
            timestamp = (
                count / float(self.fps)
                if self.fps
                else self.video.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            )
            yield count, timestamp, rotate_frame(frame, self.rotation_deg)
            has_next, frame = self.video.read()
            count += 1

        self.release()
