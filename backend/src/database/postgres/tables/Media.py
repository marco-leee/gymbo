from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime, UTC
from .base import Base


class MediaTable(Base):
    __tablename__ = "media"

    id = Column(String, primary_key=True)
    exercise_id = Column(String, nullable=False)
    step = Column(String)
    camera_view = Column(String)
    original_video_location = Column(String)
    processed_video_location = Column(String)
    pose_detection_model_name = Column(String)
    media_metadata = Column(name="metadata", type_=JSON)
    errors = Column(JSON)
    angles_of_interest_enum = Column(JSON)
    angles_of_interest = Column(JSON)
    landmark2d_results = Column(JSON)
    landmark3d_results = Column(JSON)
    completed_at = Column(DateTime, nullable=True)
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
