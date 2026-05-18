"""Decode YOLO frame blobs (JPEG/PNG/raw RGB/BGR heuristic) for `/yolo` Socket.IO ingress."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from models.yolo_ws_protocol import YoloFrameIncoming, YoloFrameMeta


def frame_bytes_to_bgr(
    frame_buf: bytes, width: int, height: int, fmt: str | None
) -> np.ndarray:
    np_frame = np.frombuffer(frame_buf, dtype=np.uint8)
    expected_size = width * height * 3

    if fmt == "rgb":
        if len(np_frame) != expected_size:
            raise ValueError(
                f"RGB frame size mismatch: got {len(np_frame)}, expected {expected_size}"
            )
        return np_frame.reshape((height, width, 3))

    if len(np_frame) == expected_size and fmt != "jpeg" and fmt != "png":
        return np_frame.reshape((height, width, 3))

    decoded = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
    if decoded is None:
        raise ValueError("Failed to decode compressed frame buffer")
    return decoded


def parse_yolo_frame_event(data: dict[str, Any]) -> YoloFrameIncoming:
    raw = data.get("frame")
    if raw is None:
        raise ValueError("frame binary payload is required")
    if isinstance(raw, memoryview):
        raw = raw.tobytes()
    elif not isinstance(raw, (bytes, bytearray)):
        raise ValueError("frame must be bytes")
    else:
        raw = bytes(raw)

    meta_payload = {k: v for k, v in data.items() if k != "frame"}
    meta = YoloFrameMeta.model_validate(meta_payload)
    return YoloFrameIncoming(meta=meta, frame=raw)
