from random import randint
from re import L
import gradio as gr
import os
import logging
import cv2
import uuid

import pandas as pd
from main import BlazePoseEstimator, ExerciseType
from utils import Video
from utils.video import CameraView


logger = logging.getLogger(__name__)
root_path = os.path.dirname(os.path.abspath(__file__))

try:
    estimator = BlazePoseEstimator(
        model_path=os.path.join(root_path, "models", "pose_landmarker_full.task")
    )
except Exception as e:
    logger.fatal("pose estimator init failed")
    exit(1)


def greet(name, camera_views, exercise_type, videos):
    return f"Hello {name}, you have uploaded {len(videos)} videos of {exercise_type} from the {camera_views} view."


df = pd.DataFrame({"frame": [], "angle": [], "key_points": []})
real_time_df = pd.DataFrame({"frame": [], "angle": [], "key_points": []})


def process_video(video: str, camera_views: str):
    print(video, camera_views)
    # TODO: take the str and turn into CameraView
    camera_views = CameraView.RIGHT
    processed_video = Video(video, camera_views)

    fps = processed_video.fps
    width = processed_video.width
    height = processed_video.height

    print(f"FPS: {fps}, Desired FPS: {fps}, Width: {width}, Height: {height}")

    # Use UUID to create a unique video file
    output_video_name = f"output_{uuid.uuid4()}.mp4"

    # Output Video
    video_codec = cv2.VideoWriter_fourcc(*"mp4v")
    output_video = cv2.VideoWriter(output_video_name, video_codec, fps, frameSize=processed_video.shape, isColor=True)  # type: ignore

    global df
    for result in estimator.execute(ExerciseType.SQUAT, processed_video):
        frame_count, annotated_image, _, key_interest_point_2d = result
        output_video.write(annotated_image)

        len_df = len(df)
        for index, (name, kip) in enumerate(key_interest_point_2d.items()):
            i = 0 if (len_df + index) == 0 else len_df + index + 1
            df.loc[i] = [frame_count, kip.angle, name]
            yield None, df

    output_video.release()
    yield output_video_name, df


def main():
    with gr.Blocks(title="Video Analyser") as exercise:
        with gr.Row():
            with gr.Column():
                name = gr.Textbox(label="Name")
                desc = gr.TextArea(
                    label="Description", placeholder="Enter a description"
                )
                exercise_type = gr.Radio(
                    label="Exercise Type", choices=ExerciseType._member_names_
                )
                camera_views = gr.Radio(
                    label="Camera Views", choices=CameraView._member_names_
                )
        line_plot = gr.LinePlot(
            df,
            title="Key Point Interest Angles",
            x="frame",
            y="angle",
            color="key_points",
        )
        with gr.Row():
            with gr.Column():
                input_video = gr.Video(label="Input Video", sources=["upload"])
            with gr.Column():
                output_video = gr.Video(
                    label="Output Video", streaming=False, autoplay=True
                )

        input_video.upload(
            fn=process_video,
            inputs=[input_video, camera_views],
            outputs=[output_video, line_plot],
        )

        submit_btn = gr.Button("Submit")
        submit_btn.click(
            fn=greet,
            inputs=[name, camera_views, exercise_type],
            outputs=[],
            api_name="exercise_analyser",
        )

    with gr.Blocks(title="Real Time Analysis") as real_time_analysis:
        plot = gr.LinePlot(
            real_time_df,
            title="Real Time Key Point Interest Angles",
            x="frame",
            y="angle",
            color="key_points",
        )
        camera = gr.Video(label="Camera", sources=["webcam"])

    main = gr.TabbedInterface([real_time_analysis, exercise], ["Real Time", "Video"])

    # main.launch(auth=("admin", "local"))
    main.launch()


if __name__ == "__main__":
    main()
