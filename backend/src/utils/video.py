from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Self

import cv2
import numpy as np

from utils.video_probe import (
    display_dimensions,
    infer_rotation_from_expected_display,
    probe_video_stream,
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

        self.rotation_deg = self._resolve_rotation(
            Path(video_path), expected_display_size
        )
        self.width, self.height = display_dimensions(
            self.coded_width, self.coded_height, self.rotation_deg
        )
        self.shape = (self.width, self.height)

    def _resolve_rotation(
        self,
        path: Path,
        expected_display_size: tuple[int, int] | None,
    ) -> int:
        stream_probe = probe_video_stream(path)
        rotation_deg = stream_probe.rotation_deg if stream_probe else 0

        if rotation_deg == 0 and expected_display_size is not None:
            expected_w, expected_h = expected_display_size
            inferred = infer_rotation_from_expected_display(
                self.coded_width,
                self.coded_height,
                expected_w,
                expected_h,
            )
            if inferred is not None and inferred != 0:
                log.warning(
                    "No ffprobe rotation for %s; inferring %s° from upload "
                    "metadata display size %sx%s (coded %sx%s)",
                    path,
                    inferred,
                    expected_w,
                    expected_h,
                    self.coded_width,
                    self.coded_height,
                )
                rotation_deg = inferred

        if rotation_deg != 0:
            log.info(
                "Video %s coded=%sx%s rotation=%s° display=%sx%s",
                path,
                self.coded_width,
                self.coded_height,
                rotation_deg,
                *display_dimensions(
                    self.coded_width, self.coded_height, rotation_deg
                ),
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
        has_next, frame = self.video.read()

        count = 0

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
