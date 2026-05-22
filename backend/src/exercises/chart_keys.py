from models.exercise import ExerciseType
from rep_counter.registry import get_rep_spec
from utils.video import CameraView


def pose_chart_kip_names(
    exercise_type: ExerciseType, camera_view: CameraView
) -> tuple[str, ...]:
    processor = get_rep_spec(exercise_type).processor
    view_kips = processor.get_key_interest_point_enum().root.get(camera_view.value, {})
    return tuple(view_kips.keys())
