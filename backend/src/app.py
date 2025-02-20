import gradio as gr
import os
import logging
import cv2
import uuid

import numpy as np
import pandas as pd
from main import MediapipeEstimator, ExerciseType
from utils import Video, CameraView

USER = os.environ.get("USER", None)
PASSWORD = os.environ.get("PASSWORD", None)
AUTH = (USER, PASSWORD) if USER and PASSWORD else None


logger = logging.getLogger(__name__)
root_path = os.path.dirname(os.path.abspath(__file__))

os.path.exists(os.path.join(root_path, "media", "out")) or os.makedirs(
    os.path.join(root_path, "media", "out")
)

try:
    estimator = MediapipeEstimator(
        model_path=os.path.join(root_path, "models", "pose_landmarker_full.task")
    )
except Exception as e:
    logger.fatal("pose estimator init failed")
    exit(1)


def greet(name, camera_views, exercise_type, videos):
    return f"Hello {name}, you have uploaded {len(videos)} videos of {exercise_type} from the {camera_views} view."


df = pd.DataFrame({"frame": [], "angle": [], "key_points": []})
real_time_df = pd.DataFrame({"frame": [], "angle": [], "key_points": []})


def process_video(df: pd.DataFrame):
    def _internal(video: str, exercise_type: str, camera_views: str):
        if exercise_type is None and camera_views is None:
            raise gr.Error("Please select an exercise type and camera view.")

        df = pd.DataFrame({"frame": [], "angle": [], "key_points": []})
        processed_video = Video(video, CameraView.from_string(camera_views))

        fps = processed_video.fps
        width = processed_video.width
        height = processed_video.height

        print(f"FPS: {fps}, Desired FPS: {fps}, Width: {width}, Height: {height}")

        # Use UUID to create a unique video file
        output_video_name = f"media/out/output_{uuid.uuid4()}.mp4"

        # Output Video
        video_codec = cv2.VideoWriter_fourcc(*"mp4v")
        output_video = cv2.VideoWriter(output_video_name, video_codec, fps, frameSize=processed_video.shape, isColor=True)  # type: ignore

        for result in estimator.detect_video(
            ExerciseType.from_string(exercise_type), processed_video
        ):
            frame_count, annotated_image, _, key_interest_point_2d = result
            output_video.write(annotated_image)

            len_df = len(df)
            for index, (name, kip) in enumerate(key_interest_point_2d.items()):
                i = 0 if (len_df + index) == 0 else len_df + index + 1
                df.loc[i] = [frame_count, kip.angle, name]
                yield None, df

        output_video.release()
        yield output_video_name, df

    return _internal


count = 0


def detect(image):
    if image is None:
        return None

    global real_time_df, count
    _, annotated_image, _, key_interest_point_2d = estimator.detect_image(
        ExerciseType.SQUAT, image
    )

    len_df = len(real_time_df)
    for index, (name, kip) in enumerate(key_interest_point_2d.items()):
        i = 0 if (len_df + index) == 0 else len_df + index + 1
        real_time_df.loc[i] = [count, kip.angle, name]

    count += 1
    return (annotated_image, real_time_df)


def main():
    with gr.Blocks(title="Video Analyser") as exercise:
        gr.Markdown(
            """
        # Video Exercise Analyser
        
        ## Instructions
        
        1. Select the exercise type and camera view. If not, will see an error message
        2. Upload a video file in `Input Video` section
        3. Processing will start immediately.
        4. You will see the graph moving but video will only be shown after processing is done.
        5. Keep the page open until the processing is done.
        6. On the output video block below, click the download button to download the processed video.
        7. Refresh the page to start over
        """
        )
        with gr.Row():
            with gr.Column():
                exercise_type = gr.Radio(
                    label="Exercise Type", choices=ExerciseType._member_names_
                )
                camera_views = gr.Radio(
                    label="Camera Views", choices=CameraView._member_names_
                )

        df = pd.DataFrame({"frame": [], "angle": [], "key_points": []})
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
            fn=process_video(df),
            inputs=[input_video, exercise_type, camera_views],
            outputs=[output_video, line_plot],
            concurrency_limit=3,
            concurrency_id="video",
        )

    main = gr.TabbedInterface([exercise], ["Video"])

    main.queue(max_size=10).launch(auth=AUTH)


if __name__ == "__main__":
    main()
