"""JPEG decode and frame preprocessing."""

from __future__ import annotations

import base64

import cv2
import numpy as np

from agent.domain.models import FrameSnapshot, IncomingFrame


def decode_jpeg(jpeg_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Failed to decode JPEG frame")
    return frame


def encode_frame_b64(frame_bgr: np.ndarray, *, quality: int = 85) -> str:
    ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Failed to encode frame as JPEG")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def incoming_to_snapshot(frame: IncomingFrame, frame_index: int) -> FrameSnapshot:
    b64 = base64.b64encode(frame.jpeg_bytes).decode("ascii")
    return FrameSnapshot(
        frame_index=frame_index,
        timestamp_sec=frame.timestamp_sec,
        frame_b64=b64,
        seq=frame.seq,
    )


def decode_incoming(frame: IncomingFrame) -> np.ndarray:
    return decode_jpeg(frame.jpeg_bytes)
