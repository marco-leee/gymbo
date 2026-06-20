"""Rolling frame history for VLM context."""

from __future__ import annotations

from agent.domain.models import FrameSnapshot

FRAME_HISTORY_LIMIT = 4


class FrameHistory:
    def __init__(self, *, limit: int = FRAME_HISTORY_LIMIT) -> None:
        self._limit = limit
        self._history: list[FrameSnapshot] = []

    def append(self, snapshot: FrameSnapshot) -> list[FrameSnapshot]:
        self._history.append(snapshot)
        self._history = self._history[-self._limit :]
        return list(self._history)

    def prior_frames(self) -> list[FrameSnapshot]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()
