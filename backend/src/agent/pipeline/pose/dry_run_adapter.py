"""Dry-run pose adapter (no ML dependencies)."""

from __future__ import annotations

import numpy as np

from agent.domain.models import PoseResult


class DryRunPoseAdapter:
    def estimate(self, frame: np.ndarray) -> PoseResult | None:
        return PoseResult(landmarks={"dry_run": True}, confidence=0.5)


__all__ = ["DryRunPoseAdapter"]
