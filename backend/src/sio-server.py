import socketio
import socketio.exceptions
import ulid
import uvicorn
import os

from yaml import emit
from estimator import MediapipeEstimator
import logging
import numpy as np


root_path = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


try:
    estimator = MediapipeEstimator(
        model_path=os.path.join(root_path, "models", "pose_landmarker_lite.task")
    )
except Exception as e:
    logger.fatal("pose estimator init failed", e)
    exit(1)


class PoseDetectionNamespace(socketio.AsyncNamespace):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processing_sids = set()  # Track which clients are being processed
        logger.info("PoseDetectionNamespace initialized")

    async def on_connect(self, sid, environ):
        logger.info(f"Client connecting: {sid}, current rooms: {self.processing_sids}")

        if len(self.processing_sids) >= 2:
            logger.warning(f"Room full, rejecting client {sid}")
            raise ConnectionRefusedError("Room is full")

        if sid not in self.processing_sids:
            self.processing_sids.add(sid)
            logger.info(f"Added {sid} to processing_sids")

        logger.info(f"Sending room_joined event to {sid}")
        await self.emit("room_joined", {"message": "Room joined"}, room=sid)

    async def on_disconnect(self, sid):
        logger.info(f"Client disconnected: {sid}")
        if sid in self.processing_sids:
            self.processing_sids.remove(sid)
            logger.info(f"Removed {sid} from processing_sids")

    async def on_heartbeat(self, sid):
        logger.debug(f"Heartbeat received from {sid}")

    async def on_video_frame(self, sid, data):
        """Handle incoming video frame in binary format"""
        if sid not in self.processing_sids:
            logger.warning(f"Unauthorized stream attempt from {sid}")
            await self.emit("error", {"message": "Not authorized to stream"}, room=sid)
            return

        try:
            idx = data.get("idx")
            frame = data.get("frame")

            result = estimator.detect_image(frame)

            await self.emit(
                "pose_results", {"annotated_image": result.annotated_image}, room=sid
            )

        except Exception as e:
            logger.error(f"Error processing frame from {sid}: {str(e)}")
            await self.emit("error", {"message": str(e)}, room=sid)

    async def on_start_stream(self, sid):
        """Handle stream start request"""
        logger.info(f"Received start_stream request from {sid}")

        if sid not in self.processing_sids:
            logger.warning(f"Unauthorized start_stream attempt from {sid}")
            await self.emit("error", {"message": "Not authorized to stream"}, room=sid)
            return

        logger.info(f"Client {sid} authorized to stream, sending stream_ready")
        await self.emit(
            "stream_ready", {"message": "Ready to receive frames"}, room=sid
        )

    async def on_stop_stream(self, sid):
        """Handle stream stop request"""
        logger.info(f"Received stop_stream request from {sid}")
        if sid in self.processing_sids:
            self.processing_sids.remove(sid)
            logger.info(f"Removed {sid} from processing_sids")
        await self.emit("stream_stopped", {"message": "Stream stopped"}, room=sid)


def main():
    """
    Basic functions
    1. Allow clients to connect, max 2 client. Each client has an unique id, isolated from each other.
    2. Clients send video stream to server for processing, server returns annotated image and results.
    3. Clients will also send heartbeats to server to keep the connection alive.
    4. Server will send instructions to client, such as start, stop, pause, resume, etc.
    5. Server will send error messages to client.

    Advanced functions
    1. Waiting room for clients to join the queue.
    """

    sio = socketio.AsyncServer(
        logger=True,
        cors_allowed_origins="*",
        async_mode="asgi",
        max_http_buffer_size=1e8,  # 100MB max buffer for video frames
    )

    # Enable engineio logging
    engineio_logger = logging.getLogger("engineio")
    engineio_logger.setLevel(logging.DEBUG)

    # Enable socketio logging
    socketio_logger = logging.getLogger("socketio")
    socketio_logger.setLevel(logging.DEBUG)

    sio.register_namespace(PoseDetectionNamespace("/pose-detection"))

    app = socketio.ASGIApp(sio)

    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="debug")


if __name__ == "__main__":
    main()
