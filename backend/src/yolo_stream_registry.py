"""Registry of active YOLO streams (stream_id ↔ Socket.IO sid or other session key)."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True)
class StreamRecord:
    session_id: str
    camera_view: str
    exercise_type: str


class StreamRegistry:
    """Tracks stream_id ownership and supports session teardown."""

    def __init__(self, max_streams: int) -> None:
        self._max_streams = max_streams
        self._lock = Lock()
        self._by_stream: dict[str, StreamRecord] = {}
        self._by_session: dict[str, set[str]] = {}

    def register(
        self,
        session_id: str,
        stream_id: str,
        *,
        camera_view: str,
        exercise_type: str,
    ) -> tuple[bool, str | None]:
        with self._lock:
            existing = self._by_stream.get(stream_id)
            if existing is not None:
                if existing.session_id == session_id:
                    self._by_stream[stream_id] = StreamRecord(
                        session_id,
                        camera_view,
                        exercise_type,
                    )
                    return True, None
                return False, "stream_id already in use by another session"

            if len(self._by_stream) >= self._max_streams:
                return False, "server stream capacity reached"

            self._by_stream[stream_id] = StreamRecord(
                session_id,
                camera_view,
                exercise_type,
            )
            self._by_session.setdefault(session_id, set()).add(stream_id)
            return True, None

    def unregister(self, session_id: str, stream_id: str) -> bool:
        with self._lock:
            rec = self._by_stream.get(stream_id)
            if rec is None or rec.session_id != session_id:
                return False
            del self._by_stream[stream_id]
            if session_id in self._by_session:
                self._by_session[session_id].discard(stream_id)
                if not self._by_session[session_id]:
                    del self._by_session[session_id]
            return True

    def disconnect_session(self, session_id: str) -> list[str]:
        """Remove all streams for session; return removed stream_ids."""
        with self._lock:
            ids = list(self._by_session.pop(session_id, ()))
            for stream_id in ids:
                self._by_stream.pop(stream_id, None)
            return ids

    def is_owned_by(self, stream_id: str, session_id: str) -> bool:
        rec = self._by_stream.get(stream_id)
        return rec is not None and rec.session_id == session_id

    def stream_count(self) -> int:
        with self._lock:
            return len(self._by_stream)

    def record(self, stream_id: str) -> StreamRecord | None:
        return self._by_stream.get(stream_id)
