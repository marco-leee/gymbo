"""Exercise profile registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExerciseProfile:
    exercise_key: str
    vlm_system_prompt: str
    issue_taxonomy: tuple[str, ...]
    prep_message: str
    setup_message: str


_PROFILES: dict[str, ExerciseProfile] = {}


def register_profile(profile: ExerciseProfile) -> None:
    _PROFILES[profile.exercise_key] = profile


def get_profile(exercise_key: str) -> ExerciseProfile:
    key = exercise_key.strip().lower()
    if key not in _PROFILES:
        from agent.exercises.overhead_squat import OVERHEAD_SQUAT_PROFILE

        register_profile(OVERHEAD_SQUAT_PROFILE)
    return _PROFILES.get(key) or _PROFILES["overhead_squat"]
