from pydantic import BaseModel
from .exercise import Exercise
from .media import Media


class AsyncMessage(BaseModel):
    exercise: Exercise
    media: Media
