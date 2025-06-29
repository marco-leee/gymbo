from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from models import Exercise
from utils import now
from .tables import ExerciseTable, MediaTable
from .base import db_transaction


class PostgresConfig(BaseModel):
    drivername: str
    host: str
    port: int
    user: str
    password: str
    database: str

    def __str__(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class Postgres:
    def __init__(self, config: PostgresConfig):
        # Create the connection string in the correct format
        connection_string = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
        self.engine = create_engine(connection_string)
        session = sessionmaker(bind=self.engine)
        self.session = session()

    def test_connection(self):
        """Test the database connection"""
        try:
            result = self.session.execute(text("SELECT 1"))
            print("Database connection successful!")
            return True
        except SQLAlchemyError as e:
            print(f"Database connection failed: {e}")
            return False
        finally:
            self.session.close()

    # Exercise CRUD operations
    @db_transaction
    def create_exercise(self, exercise_data: Exercise) -> ExerciseTable:
        """Create a new exercise"""
        exercise = ExerciseTable(**exercise_data.model_dump())
        self.session.add(exercise)
        return exercise

    def get_exercise(self, exercise_id: str) -> ExerciseTable:
        """Get exercise by ID"""
        return (
            self.session.query(ExerciseTable)
            .filter(ExerciseTable.id == exercise_id)
            .first()
        )

    @db_transaction
    def update_exercise(self, exercise_id: str, update_data: dict) -> ExerciseTable:
        """Update an exercise"""
        exercise = self.get_exercise(exercise_id)
        if exercise:
            for key, value in update_data.items():
                setattr(exercise, key, value)
            exercise.updated_at = now()
        return exercise

    @db_transaction
    def delete_exercise(self, exercise_id: str) -> bool:
        """Delete an exercise (soft delete)"""
        exercise = self.get_exercise(exercise_id)
        if exercise:
            exercise.deleted_at = now()
            return True
        return False

    # Media CRUD operations
    @db_transaction
    def create_media(self, media_data: dict) -> MediaTable:
        """Create a new media record"""
        media = MediaTable(**media_data)
        self.session.add(media)
        return media

    def get_media(self, media_id: str) -> MediaTable:
        """Get media by ID"""
        return self.session.query(MediaTable).filter(MediaTable.id == media_id).first()

    @db_transaction
    def update_media(self, media_id: str, update_data: dict) -> MediaTable:
        """Update a media record"""
        media = self.get_media(media_id)
        if media:
            for key, value in update_data.items():
                setattr(media, key, value)
            media.updated_at = now()
        return media

    @db_transaction
    def update_media_step(self, media_id: str, step: str) -> MediaTable:
        """Update the step of a media record"""
        media = self.get_media(media_id)
        if media:
            media.step = step
            media.updated_at = now()
        return media

    @db_transaction
    def update_media_error(self, media_id: str, error: Exception) -> MediaTable:
        """Update the error of a media record"""
        media = self.get_media(media_id)
        if media:
            media.errors = {
                **(media.errors if media.errors else {}),
                str(now()): str(error),
            }
            media.updated_at = now()
        return media

    def get_media_by_exercise(self, exercise_id: str) -> list[MediaTable]:
        """Get all media records for an exercise"""
        return (
            self.session.query(MediaTable)
            .filter(
                MediaTable.exercise_id == exercise_id, MediaTable.deleted_at.is_(None)
            )
            .all()
        )

    def close(self):
        """Close the database session"""
        self.session.close()
