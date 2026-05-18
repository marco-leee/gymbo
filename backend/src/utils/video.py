from __future__ import annotations

from enum import Enum
from typing import Any, Self

import cv2


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


class Video:
    def __init__(self, video_path: str, camera_view: CameraView):
        self.video_path = video_path
        self.camera_view = camera_view
        self.video = cv2.VideoCapture(video_path)

        assert self.video.isOpened(), "Cannot open video"

        self.fps = int(self.video.get(cv2.CAP_PROP_FPS))
        self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.shape = (self.width, self.height)
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / float(self.fps) if self.fps else 0.0

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
            yield count, timestamp, frame
            has_next, frame = self.video.read()
            count += 1

        self.release()
