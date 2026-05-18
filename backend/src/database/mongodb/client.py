"""Shared PyMongo client and database factory."""

from __future__ import annotations

from pymongo import MongoClient
from pymongo.database import Database

from database.mongodb.config import MongoSettings, load_mongo_settings

_client: MongoClient | None = None
_settings: MongoSettings | None = None


def get_mongo_settings() -> MongoSettings:
    global _settings
    if _settings is None:
        _settings = load_mongo_settings()
    return _settings


def get_mongo_client(settings: MongoSettings | None = None) -> MongoClient:
    """Return a process-wide MongoClient (lazy singleton)."""
    global _client
    if settings is None:
        settings = get_mongo_settings()
    if _client is None:
        _client = MongoClient(settings.uri)
    return _client


def get_mongo_database(
    *,
    client: MongoClient | None = None,
    settings: MongoSettings | None = None,
) -> Database:
    cfg = settings or get_mongo_settings()
    cli = client or get_mongo_client(cfg)
    return cli[cfg.database]


def reset_mongo_client_for_tests() -> None:
    """Close and clear the singleton client (tests only)."""
    global _client, _settings
    if _client is not None:
        _client.close()
        _client = None
    _settings = None
