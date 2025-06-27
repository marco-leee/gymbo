from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def get_processed_video_object_key(self, exercise_id: str, media_id: str) -> str:
        return f"exercises/{exercise_id}/{media_id}/processed.mp4"

    @abstractmethod
    def download_object(self, object_name: str, destination: Path) -> None:
        pass

    @abstractmethod
    def upload_object(self, path: Path, key: str) -> None:
        pass
