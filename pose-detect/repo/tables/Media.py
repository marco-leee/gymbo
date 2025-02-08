from calendar import c
from typing import Dict
from pymongo.database import Collection, Database
from pydantic import BaseModel, Field
from pydantic_extra_types.ulid import UlidType
from datetime import datetime, timezone
from bson.codec_options import TypeRegistry, CodecOptions, TypeCodec

from utils.video import CameraView


class CameraViewCodec(TypeCodec):
    python_type = CameraView
    bson_type = str

    def transform_python(self, value):
        return CameraView(value)

    def transform_bson(self, value):
        return value.value


type_registry = TypeRegistry([CameraViewCodec()])
codec_options = CodecOptions(type_registry=type_registry)


class Media(BaseModel):
    _id: str
    exercise_id: UlidType
    original_video_location: str = Field(min_length=1)
    processed_video_location: str | None = Field(default=None)
    step: str = Field(min_length=1)
    camera_view: CameraView
    pose_detection_model_name: str = Field(min_length=1)
    metadata: Dict[str, str]
    errors: Dict[str, str] | None = Field(default=None)
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))
    completed_at: datetime | None = Field(default=None)


class MediaRepo:
    __table_name__ = "media"

    def get_collection(db: Database) -> Collection:
        return db.get_collection(MediaRepo.__table_name__, codec_options=codec_options)

    @staticmethod
    def get_by_id(db: Database, media_id: str) -> Media:
        collection = MediaRepo.get_collection(db)
        req = collection.find_one({"_id": media_id})
        return Media(**req)

    @staticmethod
    def create(db: Database, media: Media) -> Media:
        collection = MediaRepo.get_collection(db)
        req = collection.insert_one(media.model_dump())
        media._id = req.inserted_id
        return media

    @staticmethod
    def update(db: Database, media: Media) -> Media:
        collection = MediaRepo.get_collection(db)
        req = collection.update_one({"_id": media._id}, {"$set": media.model_dump()})
        print(req.raw_result)
        return media
