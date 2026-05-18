"""Shared types for offline rep / set counting (importable from library code)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CountedSet:
    idx: int
    reps: int
    start_timestamp: float
    end_timestamp: float
    rep_timestamps: list[float] = field(default_factory=list)


@dataclass
class RepSetCountResult:
    exercise_type: str
    camera_view: str
    total_reps: int
    rep_timestamps: list[float]
    sets: list[CountedSet]
