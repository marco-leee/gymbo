"""Repository ports for Mongo-backed exercise / set / frame persistence."""

from __future__ import annotations

from typing import Protocol

from bson import ObjectId

from database.mongodb.entities import ExerciseEntity, ExerciseSetEntity, SetBiometricFrameEntity


class ExerciseRepository(Protocol):
    def save(self, entity: ExerciseEntity) -> str: ...

    def get_by_id(self, exercise_id: str) -> ExerciseEntity | None: ...


class ExerciseSetRepository(Protocol):
    def insert_set_with_frames(
        self,
        set_entity: ExerciseSetEntity,
        frames: list[SetBiometricFrameEntity],
    ) -> ObjectId: ...

    def get_set_by_id(self, set_id: ObjectId) -> dict | None: ...

    def list_sets_for_exercise(self, exercise_id: str) -> list[dict]: ...


class SetBiometricFrameRepository(Protocol):
    def bulk_insert_frames(
        self,
        set_id: ObjectId,
        frames: list[SetBiometricFrameEntity],
    ) -> None: ...
