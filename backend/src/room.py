from enum import Enum
from typing import List
from pydantic import BaseModel

from exercises import ExerciseType


class ClientType(str, Enum):
    MOBILE = "mobile"
    DESKTOP = "desktop"


class Room(BaseModel):
    id: str
    type: ExerciseType | None
    mobile_id: str
    desktop_id: List[str]


class Rooms:
    MAX_ROOM_SIZE = 2
    MAX_DESKTOP_CLIENT_SIZE = 2

    def __init__(self):
        self.rooms: dict[str, Room] = {}

    def __len__(self):
        return len(self.rooms)

    def add(self, room_id: str, sid: str, type: str):
        if type == "mobile":
            self.rooms[room_id] = Room(
                id=room_id, type=None, mobile_id=sid, desktop_id=[]
            )
        else:  # desktop
            self.rooms[room_id] = Room(
                id=room_id, type=None, mobile_id="", desktop_id=[sid]
            )

    def get(self, room_id: str) -> Room | None:
        return self.rooms.get(room_id)

    def get_desktop_clients(self, room_id: str) -> List[str]:
        room = self.rooms[room_id]
        return room.desktop_id

    def set_exercise(self, room_id: str, exercise: ExerciseType):
        room = self.rooms[room_id]
        room.exercise = exercise

    def join(self, room_id: str, sid: str, type: str):
        room = self.rooms[room_id]
        if type == "mobile":
            room.mobile_id = sid
        else:  # desktop
            if sid not in room.desktop_id:
                room.desktop_id.append(sid)

    def leave(self, room_id: str, sid: str):
        room = self.rooms[room_id]
        if room.mobile_id == sid:
            room.mobile_id = ""
        elif sid in room.desktop_id:
            room.desktop_id.remove(sid)

    def is_sid_in_room(self, room_id: str, type: str) -> bool:
        room = self.rooms[room_id]
        if type == "mobile":
            return bool(room.mobile_id)
        else:  # desktop
            return len(room.desktop_id) > 0

    def is_max_capacity_reached(self) -> bool:
        return len(self.rooms.keys()) >= self.MAX_DESKTOP_CLIENT_SIZE

    def is_room_full(self, room_id: str) -> bool:
        room = self.rooms[room_id]
        return (
            bool(room.mobile_id) and len(room.desktop_id) > self.MAX_DESKTOP_CLIENT_SIZE
        )

    def is_any_desktop_client_in_room(self, room_id: str) -> bool:
        room = self.rooms[room_id]
        return len(room.desktop_id) > 0

    def is_room_empty(self, room_id: str) -> bool:
        room = self.rooms[room_id]
        return not room.mobile_id and len(room.desktop_id) == 0

    def remove_room(self, room_id: str):
        del self.rooms[room_id]
