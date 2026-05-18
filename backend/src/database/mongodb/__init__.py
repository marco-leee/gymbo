"""MongoDB persistence layer (PyMongo, entity + repository)."""

from database.mongodb.client import (
    get_mongo_client,
    get_mongo_database,
    get_mongo_settings,
    reset_mongo_client_for_tests,
)
from database.mongodb.config import MongoSettings, load_mongo_settings
from database.mongodb.ingest import (
    MongodbPersistConfig,
    overall_results_to_biometric_frames,
    persist_overall_results_json_path,
    persist_pipeline_output,
)

__all__ = [
    "MongoSettings",
    "MongodbPersistConfig",
    "get_mongo_client",
    "get_mongo_database",
    "get_mongo_settings",
    "load_mongo_settings",
    "overall_results_to_biometric_frames",
    "persist_overall_results_json_path",
    "persist_pipeline_output",
    "reset_mongo_client_for_tests",
]
