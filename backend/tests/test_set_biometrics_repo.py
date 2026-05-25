"""Tests for MongoSetBiometricsRepository upsert behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from bson import ObjectId

from database.mongodb.repositories.mongo import MongoSetBiometricsRepository


class _FakeSetBiometricsCollection:
    """Minimal in-memory stand-in for set_biometrics update_one upserts."""

    def __init__(self) -> None:
        self.docs: dict[tuple[ObjectId, int], dict] = {}

    def update_one(self, filt, update, upsert=False):
        key = (filt["set_id"], filt["version"])
        if key not in self.docs:
            if not upsert:
                return MagicMock(matched_count=0, modified_count=0)
            doc: dict = {}
            for k, v in update.get("$setOnInsert", {}).items():
                doc[k] = v
            self.docs[key] = doc
        doc = self.docs[key]
        for k, v in update.get("$set", {}).items():
            doc[k] = v
        return MagicMock(matched_count=1, modified_count=1)

    def find_one(self, filt):
        key = (filt["set_id"], filt["version"])
        return self.docs.get(key)


def _repo_with_fake_col() -> tuple[MongoSetBiometricsRepository, _FakeSetBiometricsCollection]:
    col = _FakeSetBiometricsCollection()
    db = MagicMock()
    db.__getitem__.return_value = col
    return MongoSetBiometricsRepository(db), col


def test_upsert_pose_chart_sets_created_at_on_insert():
    repo, col = _repo_with_fake_col()
    set_id = ObjectId()
    chart = [{"frame": 0, "timestampSec": 0.0, "INSIDE_KNEE": 90.0}]

    repo.upsert_pose_chart(set_id, chart, version=1)

    doc = col.find_one({"set_id": set_id, "version": 1})
    assert doc is not None
    assert doc["set_id"] == set_id
    assert doc["version"] == 1
    assert doc["pose_chart_data"] == chart
    assert isinstance(doc["created_at"], datetime)
    assert doc["created_at"].tzinfo is UTC


def test_upsert_pose_chart_preserves_created_at_on_reupsert():
    repo, col = _repo_with_fake_col()
    set_id = ObjectId()
    first_chart = [{"frame": 0, "timestampSec": 0.0, "INSIDE_KNEE": 90.0}]
    second_chart = [{"frame": 1, "timestampSec": 0.1, "INSIDE_KNEE": 95.0}]

    repo.upsert_pose_chart(set_id, first_chart, version=1)
    first_created_at = col.find_one({"set_id": set_id, "version": 1})["created_at"]

    repo.upsert_pose_chart(set_id, second_chart, version=1)
    doc = col.find_one({"set_id": set_id, "version": 1})

    assert doc["created_at"] == first_created_at
    assert doc["pose_chart_data"] == second_chart
