from pymongo import MongoClient
from pymongo.database import Database

from repo.tables.Exercise import ExerciseRepo
from .Repo import ExternalClient


class MongoDB(ExternalClient):
    _client: MongoClient = None

    def __init__(self, conn_str: str, db: str):
        super().__init__(conn_str)
        self.db = db

    def connect(self):
        if self._client is not None:
            self.logger.warning("Already connected to MongoDB")
            return

        client = MongoClient(self.conn_str)

        try:
            info = client.server_info()
            self.logger.info(f"Connected to MongoDB: {info}")
            self._client = client
        except Exception as e:
            self.logger.error("MongoDB connection failed", e)
            raise e

    def get_instance(self) -> Database:
        if self._client is None:
            raise Exception("MongoDB not connected")

        return self._client[self.db]

    def health_check(self):
        print("health check")

    def is_connected(self) -> bool:
        return True

    def close(self):
        self._client.close()
        self._client = None
