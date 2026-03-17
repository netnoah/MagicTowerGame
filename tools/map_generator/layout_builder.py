"""Layout builder for generating map room structures."""
from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class Room:
    id: str
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def tiles(self):
        for y in range(self.y1, self.y2 + 1):
            for x in range(self.x1, self.x2 + 1):
                yield (x, y)

    def overlaps(self, other: "Room", margin: int = 1) -> bool:
        return not (
            self.x2 + margin < other.x1
            or other.x2 + margin < self.x1
            or self.y2 + margin < other.y1
            or other.y2 + margin < self.y1
        )

    def contains(self, x: int, y: int) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


class LayoutBuilder:
    TILE_FLOOR = 1
    TILE_WALL = 2

    def __init__(self, width: int = 25, height: int = 19, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self._tiles: list[list[int]] = []
        self._rooms: list[Room] = []
        if seed is not None:
            random.seed(seed)
        self._initialize_tiles()

    def _initialize_tiles(self):
        self._tiles = [
            [self.TILE_WALL for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def get_tiles(self) -> list[list[int]]:
        return [row[:] for row in self._tiles]

    def get_rooms(self) -> list[Room]:
        return self._rooms[:]

    def generate_rooms(self, pattern: str, count: int) -> list[Room]:
        if pattern == "simple_rooms":
            return self._generate_simple_rooms(count)
        elif pattern == "cross":
            return self._generate_cross_rooms()
        elif pattern == "linear":
            return self._generate_linear_rooms(count)
        else:
            return self._generate_simple_rooms(count)

    def _generate_simple_rooms(self, count: int) -> list[Room]:
        rooms = []
        max_attempts = 100
        for i in range(count):
            for _ in range(max_attempts):
                room_width = random.randint(5, 9)
                room_height = random.randint(4, 7)
                x1 = random.randint(1, self.width - room_width - 2)
                y1 = random.randint(1, self.height - room_height - 2)
                x2 = x1 + room_width
                y2 = y1 + room_height
                room = Room(id=f"room_{i}", x1=x1, y1=y1, x2=x2, y2=y2)
                if not any(room.overlaps(r, margin=2) for r in rooms):
                    rooms.append(room)
                    break
        self._rooms = rooms
        return rooms

    def _generate_cross_rooms(self) -> list[Room]:
        center_x, center_y = self.width // 2, self.height // 2
        rooms = [
            Room(id="center", x1=center_x-4, y1=center_y-3, x2=center_x+4, y2=center_y+3),
            Room(id="north", x1=center_x-2, y1=1, x2=center_x+2, y2=center_y-4),
            Room(id="south", x1=center_x-2, y1=center_y+4, x2=center_x+2, y2=self.height-2),
            Room(id="west", x1=1, y1=center_y-2, x2=center_x-5, y2=center_y+2),
            Room(id="east", x1=center_x+5, y1=center_y-2, x2=self.width-2, y2=center_y+2),
        ]
        self._rooms = rooms
        return rooms

    def _generate_linear_rooms(self, count: int) -> list[Room]:
        rooms = []
        usable_width = self.width - 4
        room_width = usable_width // count - 2
        for i in range(count):
            x1 = 2 + i * (room_width + 2)
            y1 = 4
            x2 = x1 + room_width
            y2 = self.height - 5
            rooms.append(Room(id=f"room_{i}", x1=x1, y1=y1, x2=x2, y2=y2))
        self._rooms = rooms
        return rooms

    def carve_rooms(self, rooms: list[Room]):
        for room in rooms:
            for x, y in room.tiles():
                if 0 <= x < self.width and 0 <= y < self.height:
                    self._tiles[y][x] = self.TILE_FLOOR

    def get_floor_tiles(self) -> set[tuple[int, int]]:
        return {
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self._tiles[y][x] == self.TILE_FLOOR
        }

    def get_room_at(self, x: int, y: int) -> Optional[Room]:
        for room in self._rooms:
            if room.contains(x, y):
                return room
        return None
