import asyncio
import socketio
from utils import Video, CameraView
import os
import numpy as np
import cv2 as cv

root_path = os.path.dirname(os.path.abspath(__file__))

video_path = f"{root_path}/test.mp4"

video = Video(video_path, CameraView.RIGHT)

fourcc = cv.VideoWriter_fourcc(*"mp4v")
new_video = cv.VideoWriter(
    "processed.mp4",
    fourcc=fourcc,
    fps=video.fps,
    frameSize=video.shape,
    isColor=True,
)


class PoseDetectionNamespace(socketio.AsyncClientNamespace):
    def __init__(self):
        super().__init__(namespace="/pose-detection")
        self.heartbeat_task = None
        self.streaming_task = None
        self.should_stream = False
        self.room_joined = False
        self.connect_event = asyncio.Event()

    async def wait_for_connection(self):
        await self.connect_event.wait()
        print("Namespace connection confirmed")

    async def on_connect(self):
        print("Connected to pose-detection namespace")
        self.heartbeat_task = asyncio.create_task(self.send_heartbeats())
        self.connect_event.set()

        # If we already received the room_joined event before connect was complete
        if self.room_joined:
            await self.start_streaming()

    async def send_heartbeats(self):
        while True:
            try:
                await self.emit("heartbeat")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error sending heartbeat: {e}")
                break

    async def on_disconnect(self):
        print("Disconnected from pose-detection namespace")
        self.should_stream = False
        self.room_joined = False
        self.connect_event.clear()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.streaming_task:
            self.streaming_task.cancel()

    async def stream_video(self):
        self.should_stream = True
        print("Starting video streaming...")
        try:
            for idx, frame in video.get_frames():
                if not self.should_stream:
                    break
                print(f"Sending frame {idx}")
                await self.emit("video_frame", {"idx": idx, "frame": frame.tobytes()})
                await asyncio.sleep(0.1)  # Small delay to avoid overwhelming the server
        except Exception as e:
            print(f"Error in stream_video: {e}")
        finally:
            print("Video streaming finished")
            self.should_stream = False
            new_video.release()
            

    async def start_streaming(self):
        """Start the streaming process once we're connected to the room"""
        try:
            print("Requesting stream start...")
            await self.emit("start_stream")
        except Exception as e:
            print(f"Error requesting stream start: {e}")

    async def on_room_joined(self, data):
        print(f"Successfully joined room: {data}")
        self.room_joined = True

        # Only start streaming if the namespace is already connected
        if self.connect_event.is_set():
            await self.start_streaming()
        # Otherwise, it will start in the on_connect handler when ready

    async def on_stream_ready(self, data):
        print("Server ready to receive video stream")
        self.streaming_task = asyncio.create_task(self.stream_video())

    async def on_stream_stopped(self, data):
        print("Stream stopped by server")
        self.should_stream = False

    async def on_pose_results(self, data):
        print(f"Received pose results for frame {data.get('frame_idx')}")
        new_video.write(data.get("annotated_image"))

    async def on_error(self, data):
        print(f"Error from server: {data['message']}")


async def main():
    sio = socketio.AsyncClient(
        logger=True,
        reconnection=True,
        reconnection_attempts=5,
        reconnection_delay=1,
        reconnection_delay_max=5,
    )

    # Register the namespace
    pose_namespace = PoseDetectionNamespace()
    sio.register_namespace(pose_namespace)

    try:
        await sio.connect("http://localhost:10000", namespaces=["/pose-detection"])
        # Wait for the connection to be established before proceeding
        await pose_namespace.wait_for_connection()
        await sio.wait()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await sio.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
