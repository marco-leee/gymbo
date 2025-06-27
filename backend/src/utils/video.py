from enum import Enum
from typing import Self
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
        self.duration = self.total_frames / self.fps

    def get_frames(self):
        has_next, frame = self.video.read()

        count = 0

        while has_next:
            yield count, frame
            has_next, frame = self.video.read()
            count += 1

        self.video.release()
