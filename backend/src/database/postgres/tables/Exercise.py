from sqlalchemy import Column, String, DateTime
from datetime import datetime, UTC
from .base import Base


class ExerciseTable(Base):
    __tablename__ = "exercise"
    id = Column(String, primary_key=True)
    client_id = Column(String, nullable=False)
    assessment_id = Column(String, nullable=True)
    name = Column(String)
    description = Column(String)
    type = Column(String)
    comment = Column(String)
    created_at = Column(
        DateTime,
        default=datetime.now(UTC),
    )
    updated_at = Column(
        DateTime,
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
    )
    deleted_at = Column(DateTime, nullable=True)
