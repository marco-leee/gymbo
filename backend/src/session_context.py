from dataclasses import dataclass
from enum import Enum

from models.exercise import ExerciseType
from utils.video import CameraView


class InputSource(Enum):
    VIDEO_FILE = "video_file"
    LIVE_STREAM = "live_stream"


@dataclass
class SessionContext:
    """Inputs and session metadata passed into the analysis pipeline."""

    user_id: str | None
    exercise_type: ExerciseType
    camera_view: CameraView
    input_source: InputSource
    video_path: str | None = None
    stream_url: str | None = None
    planned_sets: int | None = None
    target_reps_per_set: int | None = None
    conf_threshold: float = 0.8
    yolo_detect_weights: str = "pose_models/yolo26n.pt"
    yolo_seg_weights: str = "pose_models/yolo26n-seg.pt"
    yolo_pose_weights: str = "pose_models/yolo26n-pose.pt"
