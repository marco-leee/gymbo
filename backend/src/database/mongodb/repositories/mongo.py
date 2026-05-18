"""PyMongo repository implementations."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo import ASCENDING
from pymongo.client_session import ClientSession
from pymongo.database import Database
from pymongo.errors import OperationFailure

from database.mongodb import collections as col
from database.mongodb.config import load_mongo_settings
from database.mongodb.entities import (
    ExerciseEntity,
    ExerciseSetEntity,
    SetBiometricFrameEntity,
)
from database.mongodb.repositories.ports import (
    ExerciseRepository,
    ExerciseSetRepository,
    SetBiometricFrameRepository,
)


def ensure_mongodb_indexes(db: Database) -> None:
    """Create indexes for exercise / set / biometrics collections (idempotent)."""
    exercise_sets = db[col.EXERCISE_SETS]
    frames = db[col.SET_BIOMETRIC_FRAMES]

    exercise_sets.create_index(
        [("exercise_id", ASCENDING), ("set_index", ASCENDING)],
        unique=True,
        name="uniq_exercise_set_index",
    )
    exercise_sets.create_index([("exercise_id", ASCENDING)], name="by_exercise_id")

    frames.create_index(
        [("set_id", ASCENDING), ("idx", ASCENDING)],
        unique=True,
        name="uniq_set_frame_idx",
    )
    frames.create_index(
        [("set_id", ASCENDING), ("timestamp", ASCENDING)],
        name="by_set_timestamp",
    )


def _frame_payloads_for_set(
    set_id: ObjectId, frames: list[SetBiometricFrameEntity]
) -> list[dict[str, Any]]:
    return [
        {
            "set_id": set_id,
            "idx": fr.idx,
            "timestamp": fr.timestamp,
            "biometrics": fr.biometrics.model_dump(mode="json"),
            "biometrics_version": fr.biometrics_version,
        }
        for fr in frames
    ]


def _insert_set_and_frames_body(
    db: Database,
    set_payload: dict[str, Any],
    frame_payloads: list[dict[str, Any]],
    *,
    session: ClientSession | None,
) -> ObjectId:
    sets_coll = db[col.EXERCISE_SETS]
    frames_coll = db[col.SET_BIOMETRIC_FRAMES]

    if session is None:
        ins = sets_coll.insert_one(set_payload)
        sid = ins.inserted_id
        if frame_payloads:
            frames_coll.insert_many(
                [{**fp, "set_id": sid} for fp in frame_payloads]
            )
        return sid

    ins = sets_coll.insert_one(set_payload, session=session)
    sid = ins.inserted_id
    if frame_payloads:
        frames_coll.insert_many(
            [{**fp, "set_id": sid} for fp in frame_payloads],
            session=session,
        )
    return sid


class MongoExerciseRepository:
    """Persist exercises with string ULID ``_id``."""

    def __init__(self, db: Database) -> None:
        self._db = db
        self._col = db[col.EXERCISES]

    def save(self, entity: ExerciseEntity) -> str:
        doc = entity.model_dump(mode="python")
        eid = doc.pop("id")
        self._col.replace_one({"_id": eid}, {"_id": eid, **doc}, upsert=True)
        return eid

    def get_by_id(self, exercise_id: str) -> ExerciseEntity | None:
        doc = self._col.find_one({"_id": exercise_id})
        if doc is None:
            return None
        d = dict(doc)
        d["id"] = d.pop("_id")
        return ExerciseEntity.model_validate(d)


class MongoExerciseSetRepository:
    """Persist one exercise set and optional per-frame biometrics."""

    def __init__(
        self,
        db: Database,
        *,
        use_transactions: bool | None = None,
    ) -> None:
        self._db = db
        self._sets = db[col.EXERCISE_SETS]
        self._frames = db[col.SET_BIOMETRIC_FRAMES]
        self._use_transactions = use_transactions

    def insert_set_with_frames(
        self,
        set_entity: ExerciseSetEntity,
        frames: list[SetBiometricFrameEntity],
    ) -> ObjectId:
        set_payload = set_entity.model_dump(mode="python")
        frame_payloads: list[dict[str, Any]] = []
        for fr in frames:
            frame_payloads.append(
                {
                    "idx": fr.idx,
                    "timestamp": fr.timestamp,
                    "biometrics": fr.biometrics.model_dump(mode="json"),
                    "biometrics_version": fr.biometrics_version,
                }
            )

        settings = load_mongo_settings()
        use_tx = (
            settings.use_transactions
            if self._use_transactions is None
            else self._use_transactions
        )
        client = self._db.client

        if use_tx:
            try:
                with client.start_session() as session:

                    def txn(sess: ClientSession) -> ObjectId:
                        return _insert_set_and_frames_body(
                            self._db, set_payload, frame_payloads, session=sess
                        )

                    return session.with_transaction(txn)
            except OperationFailure as exc:
                err = str((exc.details or {}).get("errmsg", exc))
                if exc.code != 20 or "transaction" not in err.lower():
                    raise
                # Standalone mongod: retry without a transaction.
                pass

        return _insert_set_and_frames_body(
            self._db, set_payload, frame_payloads, session=None
        )

    def get_set_by_id(self, set_id: ObjectId) -> dict | None:
        return self._sets.find_one({"_id": set_id})

    def list_sets_for_exercise(self, exercise_id: str) -> list[dict]:
        cur = self._sets.find({"exercise_id": exercise_id}).sort(
            "set_index", ASCENDING
        )
        return list(cur)


class MongoSetBiometricFrameRepository:
    """Append per-frame biometrics to an existing exercise set document."""

    def __init__(self, db: Database) -> None:
        self._col = db[col.SET_BIOMETRIC_FRAMES]

    def bulk_insert_frames(
        self,
        set_id: ObjectId,
        frames: list[SetBiometricFrameEntity],
    ) -> None:
        if not frames:
            return
        self._col.insert_many(_frame_payloads_for_set(set_id, frames))


def exercise_repo(db: Database) -> ExerciseRepository:
    return MongoExerciseRepository(db)


def exercise_set_repo(
    db: Database,
    *,
    use_transactions: bool | None = None,
) -> ExerciseSetRepository:
    return MongoExerciseSetRepository(db, use_transactions=use_transactions)


def biometric_frame_repo(db: Database) -> SetBiometricFrameRepository:
    return MongoSetBiometricFrameRepository(db)
