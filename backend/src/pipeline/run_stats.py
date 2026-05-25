"""Aggregated counters from a video overlay pipeline run."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineRunStats:
    frames_decoded: int = 0
    frames_written: int = 0
    frames_ok: int = 0
    status_counts: dict[str, int] = field(default_factory=dict)

    def summary(self) -> str:
        parts = ", ".join(f"{k}={v}" for k, v in sorted(self.status_counts.items()))
        return (
            f"decoded={self.frames_decoded} written={self.frames_written} "
            f"ok={self.frames_ok} status_counts{{{parts}}}"
        )
