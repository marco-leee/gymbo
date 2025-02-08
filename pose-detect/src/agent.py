import logging
import os
import asyncio
import numpy as np

# from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    WorkerPermissions,
    cli,
    llm,
    metrics,
)
from livekit import rtc


# load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")

# def prewarm(proc: JobProcess):
#     proc.userdata["vad"] = silero.VAD.load()

os.environ["LIVEKIT_API_KEY"] = "devkey"
os.environ["LIVEKIT_API_SECRET"] = "secret"


async def process_audio_stream(track: rtc.Track):
    stream = rtc.AudioStream(track)
    async for frame in stream:
        print(frame)
        pass
    await stream.aclose()


async def process_video_stream(track: rtc.Track, source: rtc.VideoSource):
    input_stream = rtc.VideoStream(track)
    async for frame in input_stream:
        print("list ", frame.frame.data.tolist())
        image = np.frombuffer(frame.frame.data, dtype=np.uint8)
        print("image: ", image)

        source.capture_frame(frame.frame)
    await input_stream.aclose()
    await source.aclose()


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.VIDEO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    # video
    WIDTH = 640
    HEIGHT = 480
    video_source = rtc.VideoSource(WIDTH, HEIGHT)
    video_track = rtc.LocalVideoTrack.create_video_track(
        "exercise-analysing-video", video_source
    )
    video_options = rtc.TrackPublishOptions(
        # since the agent is a participant, our video I/O is its "camera"
        source=rtc.TrackSource.SOURCE_CAMERA,
        simulcast=True,
        # when modifying encoding options, max_framerate and max_bitrate must both be set
        video_encoding=rtc.VideoEncoding(
            max_framerate=30,
            max_bitrate=3_000_000,
        ),
        video_codec=rtc.VideoCodec.H264,
    )
    video_publication = await ctx.agent.publish_track(video_track, video_options)
    logger.info(f"published video track {video_track.name}")

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
            asyncio.create_task(process_video_stream(track, video_source))

    @ctx.room.on("data_received")
    def on_data_received(data: bytes, participant: rtc.Participant):
        logger.info(f"received data from {participant.identity}: {data}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            # agent_name="exercise-agent",
            entrypoint_fnc=entrypoint,
            # load_fnc=
        ),
    )
