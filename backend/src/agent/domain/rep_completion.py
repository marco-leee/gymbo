"""Rep and set completion policies."""

from __future__ import annotations


def is_set_complete(completed_reps: int, target_reps: int) -> bool:
    return completed_reps >= target_reps


def has_more_sets(current_set: int, planned_sets: int) -> bool:
    return current_set < planned_sets
