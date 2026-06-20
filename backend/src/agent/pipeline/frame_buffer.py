"""Ring buffer for latest camera frames."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from threading import Lock

from agent.domain.models import IncomingFrame


class FrameBuffer:
    def __init__(self, *, capacity: int = 3) -> None:
        self._capacity = max(1, capacity)
        self._frames: deque[IncomingFrame] = deque(maxlen=self._capacity)
        self._lock = Lock()
        self.latest_seq = 0
        self.last_received_at: datetime | None = None

    def push(self, frame: IncomingFrame) -> None:
        with self._lock:
            self._frames.append(frame)
            self.latest_seq = max(self.latest_seq, frame.seq)
            self.last_received_at = datetime.now(UTC)

    def latest(self) -> IncomingFrame | None:
        with self._lock:
            if not self._frames:
                return None
            return self._frames[-1]

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._frames) == 0

    def clear(self) -> None:
        with self._lock:
            self._frames.clear()
