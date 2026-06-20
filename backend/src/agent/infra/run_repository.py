"""MongoDB repository for coached exercise runs and event logs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from agent.domain.models import (
    CoachedExerciseRun,
    CoachingEventRecord,
    RunStatus,
    SafetyEventRecord,
)
from database.mongodb import collections as col
from database.mongodb.client import get_mongo_database


def ensure_trainer_indexes(db: Database) -> None:
    runs = db[col.COACHED_EXERCISE_RUNS]
    coaching = db[col.COACHING_EVENTS]
    safety = db[col.SAFETY_EVENTS]

    runs.create_index(
        [("gymbo_session_id", ASCENDING), ("session_exercise_id", ASCENDING)],
        name="by_session_exercise",
    )
    runs.create_index(
        [("trainer_id", ASCENDING), ("created_at", DESCENDING)],
        name="by_trainer_created",
    )
    coaching.create_index(
        [("run_id", ASCENDING), ("timestamp", ASCENDING)],
        name="by_run_timestamp",
    )
    safety.create_index(
        [("run_id", ASCENDING), ("timestamp", ASCENDING)],
        name="by_run_timestamp",
    )


class RunRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db
        self._indexes_ensured = False

    @property
    def db(self) -> Database:
        if self._db is None:
            self._db = get_mongo_database()
        if not self._indexes_ensured:
            ensure_trainer_indexes(self._db)
            self._indexes_ensured = True
        return self._db

    def _runs(self):
        return self.db[col.COACHED_EXERCISE_RUNS]

    def _coaching(self):
        return self.db[col.COACHING_EVENTS]

    def _safety(self):
        return self.db[col.SAFETY_EVENTS]

    def create_run(self, run: CoachedExerciseRun) -> CoachedExerciseRun:
        doc = run.model_dump(mode="json")
        doc["_id"] = run.id
        self._runs().insert_one(doc)
        return run

    def get_run(self, run_id: str) -> CoachedExerciseRun | None:
        doc = self._runs().find_one({"_id": run_id})
        if not doc:
            return None
        doc["id"] = doc.pop("_id")
        return CoachedExerciseRun.model_validate(doc)

    def update_run(self, run: CoachedExerciseRun) -> None:
        run.updated_at = datetime.now(UTC)
        doc = run.model_dump(mode="json")
        run_id = doc.pop("id")
        self._runs().update_one({"_id": run_id}, {"$set": doc})

    def find_active_for_exercise(
        self, gymbo_session_id: str, session_exercise_id: str
    ) -> CoachedExerciseRun | None:
        doc = self._runs().find_one(
            {
                "gymbo_session_id": gymbo_session_id,
                "session_exercise_id": session_exercise_id,
                "status": {"$nin": [RunStatus.ENDED.value]},
            }
        )
        if not doc:
            return None
        doc["id"] = doc.pop("_id")
        return CoachedExerciseRun.model_validate(doc)

    def save_coaching_event(self, event: CoachingEventRecord) -> None:
        doc = event.model_dump(mode="json")
        doc["_id"] = event.id
        self._coaching().insert_one(doc)

    def save_safety_event(self, event: SafetyEventRecord) -> None:
        doc = event.model_dump(mode="json")
        doc["_id"] = event.id
        self._safety().insert_one(doc)

    def list_coaching_events(
        self, run_id: str, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        coll = self._coaching()
        total = coll.count_documents({"run_id": run_id})
        cursor = (
            coll.find({"run_id": run_id})
            .sort("timestamp", ASCENDING)
            .skip(offset)
            .limit(limit)
        )
        events = []
        for doc in cursor:
            doc["id"] = doc.pop("_id")
            events.append(doc)
        return events, total

    def list_safety_events(self, run_id: str) -> list[dict[str, Any]]:
        cursor = self._safety().find({"run_id": run_id}).sort("timestamp", ASCENDING)
        events = []
        for doc in cursor:
            doc["id"] = doc.pop("_id")
            events.append(doc)
        return events

    def list_coaching_for_run(self, run_id: str) -> list[CoachingEventRecord]:
        events, _ = self.list_coaching_events(run_id, limit=1000)
        return [CoachingEventRecord.model_validate(e) for e in events]
