"""Pipeline port protocols."""

from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np

from agent.domain.models import (
    FrameSnapshot,
    MergedObservationState,
    PoseResult,
    VLMFrameResult,
    VoiceOutEvent,
)


class VLMContext(Protocol):
    merged_state: MergedObservationState
    set_number: int
    exercise_type: str
    recent_coaching: list[dict]


class PosePort(Protocol):
    def estimate(self, frame: np.ndarray) -> PoseResult | None: ...


class VLMPort(Protocol):
    def analyze(
        self,
        *,
        frames: Sequence[FrameSnapshot],
        context: VLMContext,
    ) -> VLMFrameResult: ...


class CueGeneratorPort(Protocol):
    def generate(
        self,
        *,
        event: VoiceOutEvent,
        state: MergedObservationState,
    ) -> str: ...
