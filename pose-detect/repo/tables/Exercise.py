from datetime import datetime, timezone
from pymongo.database import Collection, Database
from pydantic import BaseModel, Field
from pydantic_extra_types.ulid import UlidType
from bson.codec_options import TypeRegistry, CodecOptions, TypeCodec

from exercises import ExerciseType


class ExerciseTypeCodec(TypeCodec):
    python_type = ExerciseType
    bson_type = str

    def transform_python(self, value):
        return ExerciseType(value)

    def transform_bson(self, value):
        return value.value


type_registry = TypeRegistry([ExerciseTypeCodec()])
codec_options = CodecOptions(type_registry=type_registry)


class Exercise(BaseModel):
    _id: str
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    type: ExerciseType
    client_id: UlidType = Field(
        title="Client ID",
    )
    trainer_id: str = Field(
        default=None,
        title="Trainer ID",
    )
    comment: str | None = Field(
        default=None,
        title="Comment about the exercise",
    )
    created_at: datetime = Field(default=datetime.now(timezone.utc))
    updated_at: datetime = Field(default=datetime.now(timezone.utc))


class ExerciseRepo:
    __table_name__ = "exercise"

    def get_collection(db: Database) -> Collection:
        return db.get_collection(
            ExerciseRepo.__table_name__, codec_options=codec_options
        )

    @staticmethod
    def get_by_id(db: Database, exercise_id: str) -> Exercise:
        collection = ExerciseRepo.get_collection(db)
        req = collection.find_one({"_id": exercise_id})
        return Exercise(**req)

    @staticmethod
    def create(db: Database, exercise: Exercise) -> Exercise:
        collection = ExerciseRepo.get_collection(db)
        req = collection.insert_one(exercise.model_dump())
        exercise._id = req.inserted_id
        return exercise

    @staticmethod
    def update(db: Database, exercise: Exercise) -> Exercise:
        collection = ExerciseRepo.get_collection(db)
        req = collection.update_one(
            {"_id": exercise._id}, {"$set": exercise.model_dump()}
        )
        print(req)
        return exercise
