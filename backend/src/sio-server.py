import datetime
import random
from typing import List
import socketio
import socketio.exceptions
import ulid
import uvicorn
import os
import cv2
import numpy as np
import asyncio

from estimator import MediapipeEstimator
import logging

from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from exercises import ExerciseType
from room import Rooms


root_path = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class Room:
    id: str
    type: ExerciseType
    mobile_id: str
    desktop_id: List[str]


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
        self.rooms = Rooms()
        logger.info("PoseDetectionNamespace initialized")

    async def on_connect(self, sid, environ):
        logger.info(f"Client connecting: {sid}")

    async def on_join_room(self, sid: str, room_id: str, type: str):
        # TODO: Turn this into queue in the future
        if self.rooms.is_max_capacity_reached():
            logger.warning(f"Room full, rejecting client {sid}")
            raise ConnectionRefusedError("Server capacity is full")

        room = self.rooms.get(room_id)
        if room is None:
            self.rooms.add(room_id, sid, type)
            logger.info(f"Added {sid} to room {room_id}")
        else:
            self.rooms.join(room_id, sid, type)
            logger.info(f"Added {sid} to room {room_id}")
            # if len(room) == 1:
            # else:
            #     logger.warning(f"Room {room_id} is full, rejecting client {sid}")
            #     raise ConnectionRefusedError("Service room is full")

        logger.info(f"Sending room_joined event to {sid}")
        await self.emit(
            "room_joined",
            {"message": "Room joined", "room_id": room_id, "sid": sid, "type": type},
            room=sid,
        )

    async def on_leave_room(self, sid: str, room_id: str):
        if self.rooms.is_sid_in_room(room_id, sid):
            self.rooms.leave(room_id, sid)
            logger.info(f"Removed {sid} from room {room_id}")

        if self.rooms.is_room_empty(room_id):
            self.rooms.remove_room(room_id)
            logger.info(f"Removed room {room_id} because it is empty")

    async def on_disconnect(self, sid):
        logger.info(f"Client disconnected: {sid}")
        # Find and remove the client from any rooms they might be in
        for room_id, clients in list(self.rooms.rooms.items()):
            for client_type, client_sid in list(clients.items()):
                if client_sid == sid:
                    self.rooms.leave(room_id, client_type)
                    logger.info(
                        f"Removed disconnected client {sid} from room {room_id}"
                    )
                    if self.rooms.is_room_empty(room_id):
                        self.rooms.remove_room(room_id)
                        logger.info(
                            f"Removed empty room {room_id} after client disconnect"
                        )

    async def on_heartbeat(self, sid):
        logger.debug(f"Heartbeat received from {sid}")

    async def on_set_exercise(self, sid, exercise_id: str):
        logger.info(f"Client {sid} set exercise to {exercise_id}")
        # self.rooms.set_exercise(sid, exercise_id)

    async def on_video_frame(self, sid, data):
        """Handle incoming video frame in binary format"""
        # Debug logging to confirm event receipt
        logger.info(f"Received video frame from {sid}")

        try:
            room_id = data.get("room_id")
            frame = data.get("frame")
            dimensions = data.get("dimensions")  # Get dimensions from client

            if not room_id:
                logger.warning(f"No room_id provided in video frame from {sid}")
                await self.emit("error", {"message": "room_id is required"}, room=sid)
                return

            # Verify that the sender is in a valid room
            room = self.rooms.get(room_id)

            if not room:
                logger.warning(f"Invalid room_id {room_id} from {sid}")
                await self.emit("error", {"message": "Invalid room_id"}, room=sid)
                return

            if not self.rooms.is_any_desktop_client_in_room(room_id):
                logger.warning(f"No desktop client found in room {room_id}")
                await self.emit(
                    "error", {"message": "No desktop client found"}, room=sid
                )
                return

            # Process the frame
            np_frame = np.frombuffer(frame, dtype=np.uint8)

            # Add debug logging to help diagnose the reshape issue
            logger.info(f"Received frame buffer size: {len(np_frame)}")

            # Check if dimensions were provided
            if dimensions:
                width = dimensions.get("width", 640)
                height = dimensions.get("height", 480)
                format = dimensions.get("format", "jpeg")
                logger.info(
                    f"Client provided dimensions: {width}x{height}, format: {format}"
                )
            else:
                width, height = 640, 480
                logger.info("Using default dimensions: 640x480")

            # Calculate the expected size for raw RGB data
            expected_size = width * height * 3

            try:
                if len(np_frame) == expected_size:
                    # If the size matches raw RGB data, reshape normally
                    np_frame = np_frame.reshape((height, width, 3))
                    logger.info(f"Reshaped frame to ({height}, {width}, 3)")
                else:
                    # Assume it's a compressed image format (JPEG/PNG)
                    img = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
                    if img is None:
                        raise ValueError(
                            f"Failed to decode image buffer of size {len(np_frame)}"
                        )

                    # Convert BGR to RGB (OpenCV uses BGR by default)
                    np_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    logger.info(f"Decoded frame using OpenCV, shape: {np_frame.shape}")
            except Exception as reshape_error:
                logger.error(f"Error reshaping frame: {reshape_error}")
                await self.emit(
                    "error",
                    {"message": f"Frame reshape error: {reshape_error}"},
                    room=sid,
                )
                return

            annotated_image, key_interest_points_2d = None, None

            result = estimator.detect_image_custom_params(
                np_frame, ExerciseType.SQUAT, height=height, width=width
            )

            if result is not None:
                annotated_image = result.annotated_image
                key_interest_points_2d = result.key_interest_points_2d
            else:
                logger.info("No pose landmarks detected, sending original frame")
                annotated_image = np_frame
                key_interest_points_2d = {}

            logger.info(
                f"Frame processed, annotated image size: {len(annotated_image)}"
            )

            _, annotated_image = cv2.imencode(".jpg", annotated_image)

            desktop_sids = self.rooms.get_desktop_clients(room_id)
            for desktop_sid in desktop_sids:
                await self.emit(
                    "pose_results",
                    {
                        "time": datetime.datetime.now().timestamp(),
                        "annotated_image": annotated_image.tobytes(),
                        "dimensions": dimensions,
                        "key_interest_points_2d": {
                            k: v.model_dump() for k, v in key_interest_points_2d.items()
                        },
                    },
                    room=desktop_sid,
                )
            logger.info(f"Emitted pose_results to desktop client {desktop_sid}")
        except Exception as e:
            logger.error(f"Error processing frame from {sid}: {str(e)}")
            await self.emit("error", {"message": str(e)}, room=sid)

    async def on_start_stream(self, sid: str, room_id: str):
        """Handle stream start request"""
        logger.info(f"Received start_stream request from {sid} for room {room_id}")

        if self.rooms.get(room_id) is None:
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
    engineio_logger.setLevel(logging.INFO)

    # Enable socketio logging
    socketio_logger = logging.getLogger("socketio")
    socketio_logger.setLevel(logging.INFO)

    sio.register_namespace(PoseDetectionNamespace("/pose-detection"))

    app = socketio.ASGIApp(sio)

    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")


if __name__ == "__main__":
    main()
