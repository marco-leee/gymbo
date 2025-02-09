import io
import logging
import asyncio
from matplotlib.pylab import f
import numpy as np
import os

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    WorkerType,
    WorkerPermissions,
    cli,
    llm,
    metrics,
    JobRequest,
)
from livekit import rtc
from exercises import ExerciseType
from estimator import Estimator, MediapipeEstimator
from PIL import Image

from utils import LIVEKIT_API_KEY, LIVEKIT_API_SECRET

logger = logging.getLogger("voice-agent")

# os.environ["LIVEKIT_API_KEY"] = LIVEKIT_API_KEY
# os.environ["LIVEKIT_API_SECRET"] = LIVEKIT_API_SECRET

try:
    estimator = MediapipeEstimator(
        model_path=os.path.join("models", "pose_landmarker_full.task")
    )
    # estimator.execute(ExerciseType.SQUAT, "media/prewarm.mp4")
except Exception as e:
    logger.fatal("pose estimator init failed")
    exit(1)


async def process_audio_stream(track: rtc.Track):
    stream = rtc.AudioStream(track)
    async for frame in stream:
        print(frame)
        pass
    await stream.aclose()


async def process_video_stream(track: rtc.Track, ctx: JobContext):
    input_stream = rtc.VideoStream(track)
    # estimator = ctx.proc.userdata["estimator"]

    output_stream = None
    publication = None

    async for frame in input_stream:
        if output_stream is None and publication is None:
            # create a new video track
            video_source = rtc.VideoSource(frame.frame.width, frame.frame.height)
            video_track = rtc.LocalVideoTrack.create_video_track(
                "exercise-analysing-video", video_source
            )
            video_options = rtc.TrackPublishOptions(
                source=rtc.TrackSource.SOURCE_CAMERA,
                simulcast=True,
                video_encoding=rtc.VideoEncoding(
                    max_framerate=30,
                    max_bitrate=3_000_000,
                ),
                video_codec=rtc.VideoCodec.H264,
            )
            publication = await ctx.agent.publish_track(video_track, video_options)

        image = frame.frame.convert(type=rtc.VideoBufferType.BGRA)

        image = Image.frombytes(
            data=image.data,
            size=(frame.frame.width, frame.frame.height),
            mode="RGBA",
        )

        image = np.asarray(image, dtype=np.uint8)

        result = await estimator.detect_image(ExerciseType.SQUAT, image, video_source)

        if result is None:
            continue

        _, annotated_image = result
        print(annotated_image)
        # # TODO: add annotated image to frame and publish
        # annotated_image = rtc.VideoFrame(
        #     width=frame.frame.width,
        #     height=frame.frame.height,
        #     type=rtc.VideoBufferType.BGRA,
        #     data=result.annotated_image.tobytes(),
        # )
        video_source.capture_frame(frame.frame)
        # video_source.capture_frame(annotated_image)
    await input_stream.aclose()
    # await output_stream.aclose()


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.VIDEO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    # audio
    SAMPLE_RATE = 48000
    NUM_CHANNELS = 1  # mono audio
    AMPLITUDE = 2**8 - 1
    SAMPLES_PER_CHANNEL = 480  # 10ms at 48kHz
    audio_source = rtc.AudioSource(SAMPLE_RATE, NUM_CHANNELS)
    audio_track = rtc.LocalAudioTrack.create_audio_track(
        "exercise-analysing-audio", audio_source
    )
    audio_options = rtc.TrackPublishOptions(
        # since the agent is a participant, our audio I/O is its "microphone"
        source=rtc.TrackSource.SOURCE_MICROPHONE,
        # audio_encoding=rt
    )
    audio_publication = await ctx.agent.publish_track(audio_track, audio_options)
    logger.info(f"published audio track {audio_track.name}")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            asyncio.create_task(process_audio_stream(track))
        elif track.kind == rtc.TrackKind.KIND_VIDEO:
            asyncio.create_task(process_video_stream(track, ctx))

    @ctx.room.on("data_received")
    def on_data_received(data: bytes, participant: rtc.Participant):
        logger.info(f"received data from {participant.identity}: {data}")


# async def prewarm(proc: JobProcess):
#     print(proc)
#     try:
#         estimator = MediapipeEstimator(
#             model_path=os.path.join("models", "pose_landmarker_full.task")
#         )
#         # estimator.execute(ExerciseType.SQUAT, "media/prewarm.mp4")
#     except Exception as e:
#         logger.fatal("pose estimator init failed")
#         exit(1)

#     proc.userdata["estimator"] = estimator


async def request(req: JobRequest):
    await req.accept()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            # host=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
            agent_name=f"exercise-agent",
            worker_type=WorkerType.ROOM,
            permissions=WorkerPermissions(
                can_subscribe=True,
                can_publish=True,
                can_publish_data=True,
                can_publish_sources=[
                    rtc.TrackSource.SOURCE_CAMERA,
                    rtc.TrackSource.SOURCE_MICROPHONE,
                    rtc.TrackSource.SOURCE_SCREENSHARE,
                ],
            ),
            entrypoint_fnc=entrypoint,
            # prewarm_fnc=prewarm,
            request_fnc=request,
        ),
    )
