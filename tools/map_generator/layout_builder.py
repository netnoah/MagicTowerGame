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
        elif pattern == "l_shape":
            return self._generate_l_shape_rooms()
        elif pattern == "spiral":
            return self._generate_spiral_rooms(count)
        else:
            return self._generate_simple_rooms(count)

    def _generate_l_shape_rooms(self) -> list[Room]:
        """Generate L-shaped layout with rooms along two arms."""
        # Randomly decide orientation
        corner_x = random.randint(4, 8)
        corner_y = self.height - random.randint(4, 7)

        rooms = []

        # Horizontal arm (bottom)
        h_arm_length = random.randint(2, 3)
        for i in range(h_arm_length):
            room_w = random.randint(4, 6)
            room_h = random.randint(3, 5)
            x1 = 1 + i * (room_w + 1)
            y1 = corner_y - room_h // 2
            rooms.append(Room(id=f"h_{i}", x1=x1, y1=y1, x2=x1 + room_w, y2=y1 + room_h))

        # Vertical arm (left side going up)
        v_arm_length = random.randint(2, 3)
        for i in range(v_arm_length):
            room_w = random.randint(3, 5)
            room_h = random.randint(4, 6)
            x1 = corner_x - room_w // 2
            y1 = corner_y - (i + 1) * (room_h + 1)
            rooms.append(Room(id=f"v_{i}", x1=x1, y1=y1, x2=x1 + room_w, y2=y1 + room_h))

        # Corner room (larger)
        corner_w = random.randint(5, 7)
        corner_h = random.randint(4, 6)
        rooms.append(Room(id="corner", x1=corner_x, y1=corner_y - corner_h, x2=corner_x + corner_w, y2=corner_y))

        # Add a side room for variety
        if random.random() < 0.5:
            side_w = random.randint(3, 5)
            side_h = random.randint(3, 4)
            side_x = self.width - side_w - 2
            side_y = random.randint(2, self.height - side_h - 2)
            rooms.append(Room(id="side", x1=side_x, y1=side_y, x2=side_x + side_w, y2=side_y + side_h))

        self._rooms = rooms
        return rooms

    def _generate_spiral_rooms(self, count: int) -> list[Room]:
        """Generate a spiral-like arrangement of rooms."""
        rooms = []
        center_x, center_y = self.width // 2, self.height // 2

        # Create rooms in a spiral pattern
        angle_offset = random.uniform(0, 3.14)
        import math

        for i in range(count):
            # Spiral outward
            angle = angle_offset + i * (2 * 3.14159 / count) + (i * 0.3)
            radius = 3 + i * 1.5

            cx = int(center_x + radius * math.cos(angle))
            cy = int(center_y + radius * math.sin(angle))

            # Clamp to bounds
            room_w = random.randint(4, 6)
            room_h = random.randint(3, 5)
            x1 = max(1, min(cx - room_w // 2, self.width - room_w - 1))
            y1 = max(1, min(cy - room_h // 2, self.height - room_h - 1))

            rooms.append(Room(id=f"spiral_{i}", x1=x1, y1=y1, x2=x1 + room_w, y2=y1 + room_h))

        self._rooms = rooms
        return rooms

    def _generate_simple_rooms(self, count: int) -> list[Room]:
        rooms = []
        max_attempts = 100

        # Vary room size ranges based on room index for more variety
        size_configs = [
            (6, 10, 5, 8),   # Large room
            (4, 7, 3, 5),    # Medium room
            (5, 8, 4, 6),    # Medium-large room
            (3, 6, 3, 5),    # Small room
        ]

        for i in range(count):
            # Select size config based on room index (with some randomness)
            config_idx = i % len(size_configs)
            min_w, max_w, min_h, max_h = size_configs[config_idx]

            # Add randomness to size selection
            if random.random() < 0.3:  # 30% chance to use different config
                config_idx = random.randint(0, len(size_configs) - 1)
                min_w, max_w, min_h, max_h = size_configs[config_idx]

            for _ in range(max_attempts):
                room_width = random.randint(min_w, max_w)
                room_height = random.randint(min_h, max_h)
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
        # Add randomness to center position
        center_x = self.width // 2 + random.randint(-2, 2)
        center_y = self.height // 2 + random.randint(-1, 1)

        # Add randomness to arm lengths
        arm_length_h = random.randint(3, 5)  # Horizontal arm half-length
        arm_length_v = random.randint(2, 4)  # Vertical arm half-length
        center_w = random.randint(3, 5)      # Center room half-width
        center_h = random.randint(2, 3)      # Center room half-height

        rooms = [
            Room(id="center", x1=center_x-center_w, y1=center_y-center_h, x2=center_x+center_w, y2=center_y+center_h),
            Room(id="north", x1=center_x-2, y1=1, x2=center_x+2, y2=center_y-center_h-1),
            Room(id="south", x1=center_x-2, y1=center_y+center_h+1, x2=center_x+2, y2=self.height-2),
            Room(id="west", x1=1, y1=center_y-2, x2=center_x-center_w-1, y2=center_y+2),
            Room(id="east", x1=center_x+center_w+1, y1=center_y-2, x2=self.width-2, y2=center_y+2),
        ]
        self._rooms = rooms
        return rooms

    def _generate_linear_rooms(self, count: int) -> list[Room]:
        rooms = []
        usable_width = self.width - 4
        base_room_width = usable_width // count - 2

        # Add variation to vertical positioning
        y_margin_top = random.randint(2, 5)
        y_margin_bottom = random.randint(2, 5)

        for i in range(count):
            # Vary room width slightly
            room_width = base_room_width + random.randint(-1, 1)
            room_width = max(3, room_width)  # Minimum width

            x1 = 2 + i * (base_room_width + 2)
            y1 = y_margin_top

            # Add some variation to room height
            height_variation = random.randint(-1, 1)
            y2 = self.height - y_margin_bottom + height_variation
            y2 = min(y2, self.height - 2)  # Keep within bounds

            rooms.append(Room(id=f"room_{i}", x1=x1, y1=y1, x2=x1 + room_width, y2=y2))
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

    def get_boundary_tiles(self, room: Room) -> set[tuple[int, int]]:
        """Get tiles at the boundary of a room that could be door positions."""
        boundary = set()
        for x, y in room.tiles():
            # Check adjacent tiles - if any is a wall, this is a boundary
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if self._tiles[ny][nx] == self.TILE_WALL:
                    boundary.add((x, y))
                    break
        return boundary
    def get_passages_between_rooms(self, room1: Room, room2: Room) -> list[tuple[int, int]]:
        """Find potential passage points (walls) between two adjacent rooms."""
        passages = []
        # Get boundaries of both rooms
        boundary1 = self.get_boundary_tiles(room1)
        boundary2 = self.get_boundary_tiles(room2)
        # Find tiles that are close to each other (within 2 tiles)
        for x1, y1 in boundary1:
            for x2, y2 in boundary2:
                if abs(x1 - x2) + abs(y1 - y2) <= 2:
                    # Check if there's a wall between them
                    mx, my = (x1 + x2) // 2, (y1 + y2) // 2
                    if (0 <= mx < self.width and 0 <= my < self.height):
                        if self._tiles[my][mx] == self.TILE_WALL:
                            passages.append((mx, my))
        return passages

    def connect_rooms(self, rooms: list[Room]) -> list[tuple[int, int]]:
        """Connect all rooms with passages. Returns list of passage positions."""
        if len(rooms) < 2:
            return []

        passages = []
        connected = {rooms[0].id}
        unconnected = {r.id: r for r in rooms[1:]}

        while unconnected:
            best_passage = None
            best_connected_room = None
            best_distance = float('inf')

            for connected_room in [r for r in rooms if r.id in connected]:
                for room_id, room in unconnected.items():
                    dist = abs(connected_room.center[0] - room.center[0]) + \
                           abs(connected_room.center[1] - room.center[1])
                    if dist < best_distance:
                        room_passages = self.get_passages_between_rooms(connected_room, room)
                        if room_passages:
                            best_distance = dist
                            best_passage = random.choice(room_passages) if room_passages else None
                            best_connected_room = room_id

            if best_passage and best_connected_room:
                px, py = best_passage
                self._tiles[py][px] = self.TILE_FLOOR
                passages.append(best_passage)
                connected.add(best_connected_room)
                del unconnected[best_connected_room]
            else:
                # Force connect to nearest unconnected room
                if unconnected:
                    room_id = next(iter(unconnected))
                    room = unconnected[room_id]
                    # Find closest connected room and create passage
                    for connected_room in [r for r in rooms if r.id in connected]:
                        c1 = connected_room.center
                        c2 = room.center
                        # Carve a direct path
                        x, y = c1
                        tx, ty = c2
                        while x != tx:
                            x += 1 if tx > x else -1
                            if 0 <= x < self.width and 0 <= y < self.height:
                                if self._tiles[y][x] == self.TILE_WALL:
                                    self._tiles[y][x] = self.TILE_FLOOR
                                    passages.append((x, y))
                        while y != ty:
                            y += 1 if ty > y else -1
                            if 0 <= x < self.width and 0 <= y < self.height:
                                if self._tiles[y][x] == self.TILE_WALL:
                                    self._tiles[y][x] = self.TILE_FLOOR
                                    passages.append((x, y))
                        connected.add(room_id)
                        del unconnected[room_id]
                        break

        return passages

    def connect_rooms_with_tracking(self, rooms: list[Room]) -> dict[tuple[int, int], tuple[str, str]]:
        """Connect all rooms with passages. Returns dict mapping passage position to (room1_id, room2_id)."""
        if len(rooms) < 2:
            return {}

        passage_map: dict[tuple[int, int], tuple[str, str]] = {}
        connected = {rooms[0].id: rooms[0]}
        unconnected = {r.id: r for r in rooms[1:]}

        while unconnected:
            best_passage = None
            best_connected_room = None
            best_unconnected_room = None
            best_distance = float('inf')

            for connected_room in connected.values():
                for room_id, room in unconnected.items():
                    dist = abs(connected_room.center[0] - room.center[0]) + \
                           abs(connected_room.center[1] - room.center[1])
                    if dist < best_distance:
                        room_passages = self.get_passages_between_rooms(connected_room, room)
                        if room_passages:
                            best_distance = dist
                            best_passage = random.choice(room_passages) if room_passages else None
                            best_connected_room = connected_room.id
                            best_unconnected_room = room_id

            if best_passage and best_unconnected_room:
                px, py = best_passage
                self._tiles[py][px] = self.TILE_FLOOR
                passage_map[best_passage] = (best_connected_room, best_unconnected_room)
                connected[best_unconnected_room] = unconnected[best_unconnected_room]
                del unconnected[best_unconnected_room]
            else:
                # Force connect to nearest unconnected room
                if unconnected:
                    room_id = next(iter(unconnected))
                    room = unconnected[room_id]
                    for connected_room in connected.values():
                        c1 = connected_room.center
                        c2 = room.center
                        x, y = c1
                        tx, ty = c2
                        while x != tx:
                            x += 1 if tx > x else -1
                            if 0 <= x < self.width and 0 <= y < self.height:
                                if self._tiles[y][x] == self.TILE_WALL:
                                    self._tiles[y][x] = self.TILE_FLOOR
                                    passage_map[(x, y)] = (connected_room.id, room_id)
                        while y != ty:
                            y += 1 if ty > y else -1
                            if 0 <= x < self.width and 0 <= y < self.height:
                                if self._tiles[y][x] == self.TILE_WALL:
                                    self._tiles[y][x] = self.TILE_FLOOR
                                    passage_map[(x, y)] = (connected_room.id, room_id)
                        connected[room_id] = room
                        del unconnected[room_id]
                        break

        return passage_map
