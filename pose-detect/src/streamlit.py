from gradio_webrtc import WebRTC
import gradio as gr
import os
import logging
from main import BlazePoseEstimator, ExerciseType
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    RunningMode,
)
import mediapipe as mp

logger = logging.getLogger(__name__)
root_path = os.path.dirname(os.path.abspath(__file__))

BaseOptions = mp.tasks.BaseOptions


try:
    estimator = BlazePoseEstimator(
        model_path=os.path.join(root_path, "models", "pose_landmarker_full.task")
    )
except Exception as e:
    logger.fatal("pose estimator init failed")
    exit(1)


def detect(image):
    # just return the image here
    # _, annotated_image, _, key_interest_point_2d = estimator.detect_image(
    #     ExerciseType.SQUAT, image
    # )

    if image is None:
        return None

    option = PoseLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=os.path.join(
                root_path, "models", "pose_landmarker_full.task"
            )
        ),
        running_mode=RunningMode.IMAGE,
    )

    # print(image)
    # print(image.shape)

    # with PoseLandmarker.create_from_options(option) as landmarker:

    #     result = landmarker.detect(
    #         mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    #     )
    #     print(result)

    #     raw_landmark_2d = result.pose_landmarks[0]
    #     print("1")
    #     key_interest_points_2d = estimator.get_2d_key_points(
    #         raw_landmark_2d, estimator.camera_view, image.shape[1], image.shape[0]
    #     )
    #     print("2")
    #     annotated_image = image
    #     print("3")
    #     print(annotated_image)
    # print("4")

    _, annotated_image, _, key_interest_point_2d = estimator.detect_image(
        ExerciseType.SQUAT, image
    )
    return annotated_image


with gr.Blocks(title="Real Time Analysis") as real_time_analysis:
    with gr.Row():
        image = WebRTC(
            label="WebRTC Stream",
            modality="video",
            mode="send-receive",
        )
        image.stream(fn=detect, inputs=[image], outputs=[image])

main = gr.TabbedInterface([real_time_analysis], ["Real Time"])

main.launch()
