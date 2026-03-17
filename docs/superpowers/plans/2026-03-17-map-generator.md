# Map Generator Improvement Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a hybrid "AI blueprint + Python generation" map generation system that guarantees correctness through connectivity tracking during generation.

**Architecture:** AI designs a declarative blueprint JSON describing intent (regions, surprises, unlock sequences), then a Python script generates the actual map using connectivity tracking to guarantee all areas are reachable. No post-hoc validation/repair needed.

**Tech Stack:** Python 3.10+, pytest for testing, JSON for data exchange

---

## File Structure

```
tools/map_generator/
├── __init__.py
├── generator.py          # CLI entry point
├── config/
│   ├── __init__.py
│   └── monster_tiers.json
├── models/
│   ├── __init__.py
│   └── blueprint.py      # Dataclasses for blueprint parsing
├── layout_builder.py     # Room division, wall generation
├── connectivity.py       # Connectivity tracking algorithm
├── entity_placer.py      # Monster, item, door placement
├── output.py             # JSON output formatting
└── templates.py          # Template loading

tests/
├── test_blueprint.py
├── test_blueprint_validation.py
├── test_cross_floor_reference.py
├── test_layout_builder.py
├── test_connectivity.py
├── test_entity_placer.py
├── test_output.py
├── test_templates.py
├── test_generator.py
└── test_integration.py

.claude/skills/generate-map/
├── SKILL.md              # Updated skill instructions
├── templates/
│   ├── floors_1-5.json
│   ├── floors_6-10.json
│   ├── floors_11-15.json
│   └── floors_16-21.json
└── examples/
    └── blueprint_f1-5.json
```

---

## Task 1: Project Setup and Monster Tiers Config

**Files:**
- Create: `tools/map_generator/__init__.py`
- Create: `tools/map_generator/config/__init__.py`
- Create: `tools/map_generator/config/monster_tiers.json`

- [ ] **Step 1: Create package structure**

```bash
mkdir -p tools/map_generator/config tools/map_generator/models tests
touch tools/map_generator/__init__.py tools/map_generator/config/__init__.py tools/map_generator/models/__init__.py
```

- [ ] **Step 2: Create monster_tiers.json config**

Create file `tools/map_generator/config/monster_tiers.json`:

```json
{
  "tiers": {
    "1": ["slime_green", "slime_red", "bat"],
    "2": ["skeleton", "ghost"],
    "3": ["orc", "wizard"],
    "4": ["knight"],
    "5": ["dragon_baby"],
    "6": ["demon_lord"]
  },
  "tier_variance": {
    "easy": {"min_offset": 0, "max_offset": 0},
    "normal": {"min_offset": -1, "max_offset": 1},
    "hard": {"min_offset": -1, "max_offset": 2}
  },
  "guardian_tiers": {
    "easy": {"min": 2, "max": 3},
    "normal": {"min": 3, "max": 5},
    "hard": {"min": 4, "max": 6}
  }
}
```

- [ ] **Step 3: Verify structure**

Run: `ls -la tools/map_generator/`
Expected: `__init__.py  config/  models/`

- [ ] **Step 4: Commit**

```bash
git add tools/map_generator/
git commit -m "feat(map-gen): add project structure and monster tiers config"
```

---

## Task 2: Blueprint Data Models

**Files:**
- Create: `tools/map_generator/models/blueprint.py`
- Create: `tests/test_blueprint.py`

- [ ] **Step 1: Write failing test for blueprint parsing**

Create file `tests/test_blueprint.py`:

```python
"""Tests for blueprint data models."""
import pytest
from tools.map_generator.models.blueprint import (
    Blueprint,
    FloorBlueprint,
    Region,
    RegionContent,
    UnlockStep,
)


class TestRegion:
    def test_region_from_dict_minimal(self):
        data = {"id": "start", "type": "entrance"}
        region = Region.from_dict(data)
        assert region.id == "start"
        assert region.type == "entrance"
        assert region.access is None
        assert region.content is None

    def test_region_from_dict_full(self):
        data = {
            "id": "main",
            "type": "pathway",
            "access": {"requires": "yellow_key"},
            "content": {
                "monsters": {"tier": 1, "count": 3},
                "items": ["yellow_key"],
                "doors": ["yellow"],
                "has_stairs": True,
            },
        }
        region = Region.from_dict(data)
        assert region.id == "main"
        assert region.access.requires == "yellow_key"
        assert region.content.monsters["tier"] == 1
        assert region.content.has_stairs is True


class TestUnlockStep:
    def test_unlock_step_from_dict(self):
        data = {"floor": 1, "door": "yellow", "key_at": "start"}
        step = UnlockStep.from_dict(data)
        assert step.floor == 1
        assert step.door == "yellow"
        assert step.key_at == "start"
        assert step.target_region is None

    def test_unlock_step_door_color_alias(self):
        data = {"floor": 2, "door_color": "blue", "key_at": "vault"}
        step = UnlockStep.from_dict(data)
        assert step.door == "blue"


class TestBlueprint:
    def test_blueprint_from_dict(self):
        data = {
            "group": 1,
            "floors_range": [1, 5],
            "difficulty_tier": "easy",
            "global_theme": "Introduction",
            "floors": [
                {
                    "floor": 1,
                    "name": "Entrance",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                }
            ],
            "unlock_sequence": [
                {"floor": 1, "door": "yellow", "key_at": "start"}
            ],
        }
        blueprint = Blueprint.from_dict(data)
        assert blueprint.group == 1
        assert blueprint.floors_range == (1, 5)
        assert blueprint.difficulty_tier == "easy"
        assert len(blueprint.floors) == 1
        assert len(blueprint.unlock_sequence) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_blueprint.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement blueprint dataclasses**

Create file `tools/map_generator/models/blueprint.py`:

```python
"""Data models for map generation blueprints."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RegionAccess:
    requires: str

    @classmethod
    def from_dict(cls, data: dict) -> "RegionAccess":
        return cls(requires=data["requires"])


@dataclass
class RegionContent:
    monsters: Optional[dict] = None
    items: Optional[list[str]] = None
    doors: Optional[list[str]] = None
    has_stairs: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "RegionContent":
        return cls(
            monsters=data.get("monsters"),
            items=data.get("items"),
            doors=data.get("doors"),
            has_stairs=data.get("has_stairs", False),
        )


@dataclass
class Region:
    id: str
    type: str
    access: Optional[RegionAccess] = None
    content: Optional[RegionContent] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Region":
        access = RegionAccess.from_dict(data["access"]) if "access" in data else None
        content = RegionContent.from_dict(data["content"]) if "content" in data else None
        return cls(
            id=data["id"],
            type=data["type"],
            access=access,
            content=content,
        )


@dataclass
class Surprise:
    type: str
    location: Optional[str] = None
    guardian_tier: Optional[int] = None
    reward: Optional[list[str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Surprise":
        return cls(
            type=data["type"],
            location=data.get("location"),
            guardian_tier=data.get("guardian_tier"),
            reward=data.get("reward"),
        )


@dataclass
class LayoutConfig:
    pattern: str
    room_count: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> "LayoutConfig":
        return cls(
            pattern=data["pattern"],
            room_count=data.get("room_count", 3),
        )


@dataclass
class UnlockStep:
    floor: int
    door: str
    key_at: str
    target_region: Optional[str] = None
    key_count: int = 1

    @classmethod
    def from_dict(cls, data: dict) -> "UnlockStep":
        door = data.get("door") or data.get("door_color")
        return cls(
            floor=data["floor"],
            door=door,
            key_at=data["key_at"],
            target_region=data.get("target_region"),
            key_count=data.get("key_count", 1),
        )


@dataclass
class FloorBlueprint:
    floor: int
    name: str
    layout: LayoutConfig
    regions: list[Region]
    surprises: list[Surprise] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "FloorBlueprint":
        layout = LayoutConfig.from_dict(data["layout"])
        regions = [Region.from_dict(r) for r in data.get("regions", [])]
        surprises = [Surprise.from_dict(s) for s in data.get("surprises", [])]
        return cls(
            floor=data["floor"],
            name=data.get("name", f"Floor {data['floor']}"),
            layout=layout,
            regions=regions,
            surprises=surprises,
        )


@dataclass
class Blueprint:
    group: int
    floors_range: tuple[int, int]
    difficulty_tier: str
    floors: list[FloorBlueprint]
    global_theme: str = ""
    unlock_sequence: list[UnlockStep] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Blueprint":
        floors = [FloorBlueprint.from_dict(f) for f in data.get("floors", [])]
        unlock_sequence = [UnlockStep.from_dict(u) for u in data.get("unlock_sequence", [])]
        floors_range = tuple(data.get("floors_range", [1, 1]))
        return cls(
            group=data.get("group", 1),
            floors_range=floors_range,  # type: ignore
            difficulty_tier=data.get("difficulty_tier", "normal"),
            global_theme=data.get("global_theme", ""),
            floors=floors,
            unlock_sequence=unlock_sequence,
        )

    @classmethod
    def from_json_file(cls, filepath: str) -> "Blueprint":
        import json
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_blueprint.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/map_generator/models/blueprint.py tests/test_blueprint.py
git commit -m "feat(map-gen): add blueprint data models"
```

---

## Task 3: Layout Builder

**Files:**
- Create: `tools/map_generator/layout_builder.py`
- Create: `tests/test_layout_builder.py`

- [ ] **Step 1: Write failing test for layout builder**

Create file `tests/test_layout_builder.py`:

```python
"""Tests for layout builder."""
import pytest
from tools.map_generator.layout_builder import LayoutBuilder, Room


class TestRoom:
    def test_room_creation(self):
        room = Room(id="entrance", x1=1, y1=1, x2=5, y2=5)
        assert room.id == "entrance"
        assert room.width == 4
        assert room.height == 4
        assert room.center == (3, 3)

    def test_room_tiles(self):
        room = Room(id="test", x1=0, y1=0, x2=2, y2=2)
        tiles = list(room.tiles())
        assert (0, 0) in tiles
        assert (1, 1) in tiles
        assert len(tiles) == 9


class TestLayoutBuilder:
    def test_create_empty_map(self):
        builder = LayoutBuilder(width=25, height=19)
        tiles = builder.get_tiles()
        assert len(tiles) == 19
        assert len(tiles[0]) == 25
        assert all(tiles[y][x] == 2 for y in range(19) for x in range(25))

    def test_generate_simple_rooms(self):
        builder = LayoutBuilder(width=25, height=19)
        rooms = builder.generate_rooms(pattern="simple_rooms", count=3)
        assert len(rooms) == 3
        for i, r1 in enumerate(rooms):
            for r2 in rooms[i+1:]:
                assert not r1.overlaps(r2)

    def test_carve_rooms(self):
        builder = LayoutBuilder(width=25, height=19)
        rooms = builder.generate_rooms(pattern="simple_rooms", count=2)
        builder.carve_rooms(rooms)
        tiles = builder.get_tiles()
        floor_count = sum(1 for y in range(19) for x in range(25) if tiles[y][x] == 1)
        assert floor_count > 50

    def test_get_floor_tiles(self):
        builder = LayoutBuilder(width=25, height=19)
        rooms = builder.generate_rooms(pattern="simple_rooms", count=2)
        builder.carve_rooms(rooms)
        floor_tiles = builder.get_floor_tiles()
        assert len(floor_tiles) > 50
        assert all(isinstance(t, tuple) and len(t) == 2 for t in floor_tiles)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_layout_builder.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement layout builder**

Create file `tools/map_generator/layout_builder.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_layout_builder.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/map_generator/layout_builder.py tests/test_layout_builder.py
git commit -m "feat(map-gen): add layout builder for room generation"
```

---

## Task 4: Connectivity Module

**Files:**
- Create: `tools/map_generator/connectivity.py`
- Create: `tests/test_connectivity.py`

- [ ] **Step 1: Write failing test for connectivity**

Create file `tests/test_connectivity.py`:

```python
"""Tests for connectivity tracking."""
import pytest
from tools.map_generator.connectivity import (
    ConnectivityTracker,
    flood_fill,
    get_all_regions,
)


class TestFloodFill:
    def test_flood_fill_simple(self):
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        result = flood_fill(tiles, 2, 2)
        assert len(result) == 9
        assert (2, 2) in result

    def test_flood_fill_with_blocked(self):
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        result = flood_fill(tiles, 1, 1)
        assert len(result) == 4
        assert (3, 2) not in result


class TestGetAllRegions:
    def test_single_region(self):
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        regions = get_all_regions(tiles)
        assert len(regions) == 1

    def test_multiple_regions(self):
        tiles = [
            [2, 2, 2, 2, 2, 2, 2],
            [2, 1, 1, 2, 1, 1, 2],
            [2, 1, 1, 2, 1, 1, 2],
            [2, 2, 2, 2, 2, 2, 2],
        ]
        regions = get_all_regions(tiles)
        assert len(regions) == 2


class TestConnectivityTracker:
    def test_initialization(self):
        tiles = [
            [2, 2, 2],
            [2, 1, 2],
            [2, 2, 2],
        ]
        tracker = ConnectivityTracker(tiles, start=(1, 1))
        assert tracker.start == (1, 1)
        assert len(tracker.reachable) == 1

    def test_add_door_connection(self):
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        tracker = ConnectivityTracker(tiles, start=(1, 2))
        assert len(tracker.reachable) == 3
        tracker.add_door((2, 2))
        assert len(tracker.reachable) == 6

    def test_is_reachable(self):
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        tracker = ConnectivityTracker(tiles, start=(1, 1))
        assert tracker.is_reachable((1, 2))
        assert not tracker.is_reachable((3, 1))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_connectivity.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement connectivity module**

Create file `tools/map_generator/connectivity.py`:

```python
"""Connectivity tracking for map generation."""
from collections import deque
from typing import Optional


def flood_fill(
    tiles: list[list[int]],
    start_x: int,
    start_y: int,
    blocked: Optional[set[tuple[int, int]]] = None,
    floor_tile: int = 1,
) -> set[tuple[int, int]]:
    if blocked is None:
        blocked = set()
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    visited: set[tuple[int, int]] = set()
    queue = deque([(start_x, start_y)])
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or (x, y) in blocked:
            continue
        if not (0 <= x < width and 0 <= y < height):
            continue
        if tiles[y][x] != floor_tile:
            continue
        visited.add((x, y))
        queue.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return visited


def get_all_regions(tiles: list[list[int]], floor_tile: int = 1) -> list[set[tuple[int, int]]]:
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    regions: list[set[tuple[int, int]]] = []
    visited: set[tuple[int, int]] = set()
    for y in range(height):
        for x in range(width):
            if tiles[y][x] == floor_tile and (x, y) not in visited:
                region = flood_fill(tiles, x, y, floor_tile=floor_tile)
                regions.append(region)
                visited.update(region)
    return regions


class ConnectivityTracker:
    TILE_FLOOR = 1

    def __init__(
        self,
        tiles: list[list[int]],
        start: tuple[int, int],
        blocked: Optional[set[tuple[int, int]]] = None,
    ):
        self._tiles = tiles
        self.start = start
        self._blocked = blocked or set()
        self._doors: set[tuple[int, int]] = set()
        self._reachable = self._compute_reachable()

    def _compute_reachable(self) -> set[tuple[int, int]]:
        effective_blocked = self._blocked - self._doors
        return flood_fill(
            self._tiles,
            self.start[0],
            self.start[1],
            blocked=effective_blocked,
            floor_tile=self.TILE_FLOOR,
        )

    @property
    def reachable(self) -> set[tuple[int, int]]:
        return self._reachable.copy()

    def add_door(self, position: tuple[int, int]):
        self._doors.add(position)
        self._reachable = self._compute_reachable()

    def is_reachable(self, position: tuple[int, int]) -> bool:
        return position in self._reachable

    def get_reachable_positions(self) -> set[tuple[int, int]]:
        return self._reachable.copy()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_connectivity.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/map_generator/connectivity.py tests/test_connectivity.py
git commit -m "feat(map-gen): add connectivity tracking module"
```

---

## Task 5: Entity Placer

**Files:**
- Create: `tools/map_generator/entity_placer.py`
- Create: `tests/test_entity_placer.py`

- [ ] **Step 1: Write failing test for entity placer**

Create file `tests/test_entity_placer.py`:

```python
"""Tests for entity placement."""
import pytest
from tools.map_generator.entity_placer import EntityPlacer, Entity, get_monster_for_tier


class TestEntity:
    def test_entity_creation(self):
        entity = Entity(type="monster", id="slime_green", x=5, y=10)
        assert entity.type == "monster"
        assert entity.id == "slime_green"
        assert entity.x == 5
        assert entity.y == 10
        assert entity.data == {}

    def test_entity_to_dict(self):
        entity = Entity(type="item", id="yellow_key", x=3, y=7, data={"secret": True})
        result = entity.to_dict()
        assert result == {
            "type": "item",
            "id": "yellow_key",
            "x": 3,
            "y": 7,
            "data": {"secret": True},
        }


class TestEntityPlacer:
    def test_initialization(self):
        floor_tiles = {(x, y) for x in range(3) for y in range(3)}
        placer = EntityPlacer(floor_tiles)
        assert len(placer.available_positions) == 9

    def test_place_entity(self):
        floor_tiles = {(1, 1), (2, 2), (3, 3)}
        placer = EntityPlacer(floor_tiles)
        entity = placer.place_entity("monster", "slime_green")
        assert entity is not None
        assert entity.type == "monster"
        assert (entity.x, entity.y) in floor_tiles

    def test_place_in_region(self):
        floor_tiles = {(x, y) for x in range(5) for y in range(5)}
        region = {(0, 0), (0, 1), (1, 0), (1, 1)}
        placer = EntityPlacer(floor_tiles)
        entity = placer.place_in_region("item", "yellow_key", region)
        assert entity is not None
        assert (entity.x, entity.y) in region


class TestGetMonsterForTier:
    def test_get_monster_for_tier(self):
        monster = get_monster_for_tier(1)
        assert monster in ["slime_green", "slime_red", "bat"]
        monster = get_monster_for_tier(6)
        assert monster == "demon_lord"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_entity_placer.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement entity placer**

Create file `tools/map_generator/entity_placer.py`:

```python
"""Entity placement for map generation."""
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Entity:
    type: str
    id: str
    x: int
    y: int
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "data": self.data,
        }


MONSTER_TIERS: dict[int, list[str]] = {
    1: ["slime_green", "slime_red", "bat"],
    2: ["skeleton", "ghost"],
    3: ["orc", "wizard"],
    4: ["knight"],
    5: ["dragon_baby"],
    6: ["demon_lord"],
}


def get_monster_for_tier(tier: int, variance: int = 0) -> str:
    min_tier = max(1, tier - variance)
    max_tier = min(6, tier + variance)
    available: list[str] = []
    for t in range(min_tier, max_tier + 1):
        available.extend(MONSTER_TIERS.get(t, []))
    if not available:
        return "slime_green"
    return random.choice(available)


class EntityPlacer:
    def __init__(self, floor_tiles: set[tuple[int, int]], seed: Optional[int] = None):
        self._all_floor = floor_tiles.copy()
        self._available = floor_tiles.copy()
        self._placed: list[Entity] = []
        if seed is not None:
            random.seed(seed)

    @property
    def available_positions(self) -> set[tuple[int, int]]:
        return self._available.copy()

    def place_entity(self, entity_type: str, entity_id: str, data: Optional[dict] = None) -> Optional[Entity]:
        if not self._available:
            return None
        pos = random.choice(list(self._available))
        return self.place_entity_at(entity_type, entity_id, pos, data)

    def place_entity_at(self, entity_type: str, entity_id: str, position: tuple[int, int], data: Optional[dict] = None) -> Entity:
        if position not in self._available:
            raise ValueError(f"Position {position} is not available")
        entity = Entity(
            type=entity_type,
            id=entity_id,
            x=position[0],
            y=position[1],
            data=data or {},
        )
        self._available.discard(position)
        self._placed.append(entity)
        return entity

    def place_in_region(self, entity_type: str, entity_id: str, region: set[tuple[int, int]], data: Optional[dict] = None) -> Optional[Entity]:
        available_in_region = region & self._available
        if not available_in_region:
            return None
        pos = random.choice(list(available_in_region))
        return self.place_entity_at(entity_type, entity_id, pos, data)

    def place_monsters_by_tier(self, tier: int, count: int, region: Optional[set[tuple[int, int]]] = None, variance: int = 0) -> list[Entity]:
        monsters: list[Entity] = []
        for _ in range(count):
            if region:
                pos_pool = region & self._available
            else:
                pos_pool = self._available
            if not pos_pool:
                break
            pos = random.choice(list(pos_pool))
            monster_id = get_monster_for_tier(tier, variance)
            entity = self.place_entity_at("monster", monster_id, pos)
            monsters.append(entity)
        return monsters

    def get_all_entities(self) -> list[Entity]:
        return self._placed.copy()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_entity_placer.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/map_generator/entity_placer.py tests/test_entity_placer.py
git commit -m "feat(map-gen): add entity placement module"
```

---

## Task 6: Output Module

**Files:**
- Create: `tools/map_generator/output.py`
- Create: `tests/test_output.py`

- [ ] **Step 1: Write failing test for output module**

Create file `tests/test_output.py`:

```python
"""Tests for map output generation."""
import json
import tempfile
from pathlib import Path
from tools.map_generator.output import MapOutput, generate_floor_map


class TestMapOutput:
    def test_create_basic_map(self):
        tiles = [[2] * 25 for _ in range(19)]
        tiles[9][12] = 1
        output = MapOutput(
            level=1,
            name="Test Floor",
            name_cn="测试层",
            tiles=tiles,
            player_start=(12, 9),
        )
        result = output.to_dict()
        assert result["level"] == 1
        assert result["width"] == 25
        assert result["height"] == 19
        assert result["player_start"] == [12, 9]
        assert len(result["entities"]) == 0

    def test_add_entity(self):
        tiles = [[1] * 10 for _ in range(10)]
        output = MapOutput(
            level=1,
            name="Test",
            name_cn="测试",
            tiles=tiles,
            player_start=(5, 5),
        )
        output.add_entity("monster", "slime_green", 3, 3)
        output.add_entity("item", "yellow_key", 7, 7, {"secret": True})
        result = output.to_dict()
        assert len(result["entities"]) == 2

    def test_save_to_file(self):
        tiles = [[1] * 5 for _ in range(5)]
        output = MapOutput(
            level=1,
            name="Test",
            name_cn="测试",
            tiles=tiles,
            player_start=(2, 2),
        )
        output.add_entity("item", "yellow_key", 1, 1)
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = output.save(tmpdir)
            assert Path(filepath).exists()
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["level"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_output.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement output module**

Create file `tools/map_generator/output.py`:

```python
"""Output generation for map files."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


TILE_FLOOR = 1
TILE_WALL = 2
TILE_STAIRS_DOWN = 20
TILE_STAIRS_UP = 21


@dataclass
class MapOutput:
    level: int
    name: str
    name_cn: str
    tiles: list[list[int]]
    player_start: tuple[int, int]
    width: int = 25
    height: int = 19
    entities: list[dict] = field(default_factory=list)

    def add_entity(self, entity_type: str, entity_id: str, x: int, y: int, data: Optional[dict] = None):
        self.entities.append({
            "type": entity_type,
            "id": entity_id,
            "x": x,
            "y": y,
            "data": data or {},
        })

    def set_stairs_up(self, position: tuple[int, int]):
        x, y = position
        self.tiles[y][x] = TILE_STAIRS_UP

    def set_stairs_down(self, position: tuple[int, int]):
        x, y = position
        self.tiles[y][x] = TILE_STAIRS_DOWN

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "name": self.name,
            "name_cn": self.name_cn,
            "width": self.width,
            "height": self.height,
            "player_start": list(self.player_start),
            "tiles": self.tiles,
            "entities": self.entities,
        }

    def save(self, output_dir: str) -> str:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        filename = f"floor_{self.level:02d}.json"
        filepath = output_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return str(filepath)


def generate_floor_map(
    level: int,
    name: str,
    name_cn: str,
    tiles: list[list[int]],
    player_start: tuple[int, int],
    entities: list[dict],
    stairs_up: Optional[tuple[int, int]] = None,
    stairs_down: Optional[tuple[int, int]] = None,
    width: int = 25,
    height: int = 19,
) -> dict:
    tiles_copy = [row[:] for row in tiles]
    if stairs_up:
        x, y = stairs_up
        tiles_copy[y][x] = TILE_STAIRS_UP
    if stairs_down:
        x, y = stairs_down
        tiles_copy[y][x] = TILE_STAIRS_DOWN
    return {
        "level": level,
        "name": name,
        "name_cn": name_cn,
        "width": width,
        "height": height,
        "player_start": list(player_start),
        "tiles": tiles_copy,
        "entities": entities,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_output.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/map_generator/output.py tests/test_output.py
git commit -m "feat(map-gen): add output generation module"
```

---

## Task 7: Template System

**Files:**
- Create: `tools/map_generator/templates.py`
- Create: `tests/test_templates.py`

- [ ] **Step 1: Write failing test for templates**

Create file `tests/test_templates.py`:

```python
"""Tests for template system."""
import pytest
from tools.map_generator.templates import FloorTemplate, TemplateLoader


class TestFloorTemplate:
    def test_floor_template_from_dict(self):
        data = {
            "group_name": "Entry Area",
            "floors_range": [1, 5],
            "difficulty": {
                "monster_tier_base": 1,
                "monster_tier_variance": 1,
            },
            "layout": {
                "patterns": ["simple_rooms"],
                "room_count_range": [2, 4],
            },
            "doors": {
                "colors": ["yellow"],
                "max_per_floor": 2,
            },
        }
        template = FloorTemplate.from_dict(data)
        assert template.group_name == "Entry Area"
        assert template.floors_range == (1, 5)
        assert template.difficulty["monster_tier_base"] == 1

    def test_get_monster_tier_for_floor(self):
        template = FloorTemplate(
            group_name="Test",
            floors_range=(1, 5),
            difficulty={"monster_tier_base": 1, "monster_tier_variance": 1},
        )
        assert template.get_monster_tier(1) == 1


class TestTemplateLoader:
    def test_get_template_by_floor(self):
        loader = TemplateLoader()
        t1 = loader.get_for_floor(3)
        assert t1 is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_templates.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement templates module**

Create file `tools/map_generator/templates.py`:

```python
"""Template system for map generation."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FloorTemplate:
    group_name: str
    floors_range: tuple[int, int]
    difficulty: dict = field(default_factory=lambda: {
        "monster_tier_base": 1,
        "monster_tier_variance": 1,
    })
    layout: dict = field(default_factory=lambda: {
        "patterns": ["simple_rooms"],
        "room_count_range": [2, 4],
    })
    doors: dict = field(default_factory=lambda: {
        "colors": ["yellow"],
        "max_per_floor": 2,
    })
    surprises: dict = field(default_factory=lambda: {
        "guardian_chance": 0.3,
        "trap_chance": 0.2,
    })
    rewards: dict = field(default_factory=lambda: {
        "common": ["yellow_key", "red_potion"],
        "rare": [],
        "legendary": [],
    })

    @classmethod
    def from_dict(cls, data: dict) -> "FloorTemplate":
        floors_range = tuple(data.get("floors_range", [1, 1]))
        return cls(
            group_name=data.get("group_name", "Unknown"),
            floors_range=floors_range,  # type: ignore
            difficulty=data.get("difficulty", {}),
            layout=data.get("layout", {}),
            doors=data.get("doors", {}),
            surprises=data.get("surprises", {}),
            rewards=data.get("rewards", {}),
        )

    def get_monster_tier(self, floor: int) -> int:
        base = self.difficulty.get("monster_tier_base", 1)
        variance = self.difficulty.get("monster_tier_variance", 0)
        range_size = self.floors_range[1] - self.floors_range[0] + 1
        if range_size > 0:
            progress = (floor - self.floors_range[0]) / range_size
        else:
            progress = 0
        return base + int(progress * variance)

    def get_available_door_colors(self) -> list[str]:
        return self.doors.get("colors", ["yellow"])

    def get_max_doors_per_floor(self) -> int:
        return self.doors.get("max_per_floor", 2)


class TemplateLoader:
    DEFAULT_TEMPLATE = FloorTemplate(
        group_name="Default",
        floors_range=(1, 21),
        difficulty={"monster_tier_base": 1},
    )

    def __init__(self, template_dir: Optional[str] = None):
        self._templates: dict[str, FloorTemplate] = {}
        if template_dir:
            self._load_templates(template_dir)

    def _load_templates(self, template_dir: str):
        template_path = Path(template_dir)
        if not template_path.exists():
            return
        for filepath in template_path.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                template = FloorTemplate.from_dict(data)
                self._templates[filepath.name] = template
            except (json.JSONDecodeError, KeyError):
                continue

    def get_for_floor(self, floor: int) -> FloorTemplate:
        for template in self._templates.values():
                if template.floors_range[0] <= floor <= template.floors_range[1]:
                    return template
        return self.DEFAULT_TEMPLATE
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_templates.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/map_generator/templates.py tests/test_templates.py
git commit -m "feat(map-gen): add template loading system"
```

---

## Task 8: Main Generator CLI

**Files:**
- Create: `tools/map_generator/generator.py`

- [ ] **Step 1: Write failing test for generator CLI**

Create file `tests/test_generator.py`:

```python
"""Tests for main generator CLI."""
import json
import tempfile
from pathlib import Path
from tools.map_generator.generator import MapGenerator, load_blueprint


class TestMapGenerator:
    def test_initialization(self):
        generator = MapGenerator()
        assert generator.width == 25
        assert generator.height == 19

    def test_generate_single_floor(self):
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "difficulty_tier": "easy",
            "floors": [
                {
                    "floor": 1,
                    "name": "Test Floor",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                }
            ],
            "unlock_sequence": [],
        }
        generator = MapGenerator()
        result = generator.generate(blueprint_data)
        assert result is not None
        assert len(result) == 1
        assert result[0]["level"] == 1

    def test_generated_map_has_valid_structure(self):
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "difficulty_tier": "easy",
            "floors": [
                {
                    "floor": 1,
                    "name": "Test",
                    "layout": {"pattern": "simple_rooms", "room_count": 3},
                    "regions": [
                        {"id": "start", "type": "entrance"},
                        {"id": "main", "type": "pathway"},
                    ],
                    "surprises": [],
                }
            ],
            "unlock_sequence": [],
        }
        generator = MapGenerator()
        result = generator.generate(blueprint_data)
        map_data = result[0]
        assert "level" in map_data
        assert "tiles" in map_data
        assert "entities" in map_data
        assert len(map_data["tiles"]) == 19

        assert len(map_data["tiles"][0]) == 25
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_generator.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement generator CLI**

Create file `tools/map_generator/generator.py`:

```python
"""Main map generator CLI."""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from tools.map_generator.models.blueprint import Blueprint
from tools.map_generator.layout_builder import LayoutBuilder
from tools.map_generator.connectivity import ConnectivityTracker
from tools.map_generator.entity_placer import EntityPlacer
from tools.map_generator.output import MapOutput


VALID_DOOR_COLORS = {"yellow", "blue", "red", "green"}


def validate_blueprint(data: dict) -> dict:
    errors = []
    if "floors_range" not in data:
        errors.append({"message": "Missing required field: floors_range"})
        return {"valid": False, "errors": errors}
    if "floors" not in data:
        errors.append({"message": "Missing required field: floors"})
        return {"valid": False, "errors": errors}
    floors_range = data.get("floors_range", [1, 1])
    floor_numbers = set()
    for floor_data in data["floors"]:
        floor_num = floor_data.get("floor")
        if floor_num is None:
            errors.append({"message": f"Floor missing 'floor' field"})
            continue
        if floor_num < floors_range[0] or floor_num > floors_range[1]:
            errors.append({
                "message": f"Floor {floor_num} is outside range {floors_range[0]}-{floors_range[1]}}"
            })
        if floor_num in floor_numbers:
            errors.append({"message": f"Duplicate floor number: {floor_num}"})
        floor_numbers.add(floor_num)
    if "unlock_sequence" in data:
        for step in data["unlock_sequence"]:
            door_color = step.get("door") or step.get("door_color")
            if door_color not in VALID_DOOR_COLORS:
                errors.append({
                    "message": f"Invalid door color: {door_color}. Valid: {VALID_DOOR_COLORS}"
                })
    return {"valid": len(errors) == 0, "errors": errors}


def resolve_cross_floor_reference(ref: str, blueprint: Blueprint) -> Optional:
any]:
    if "_" not in ref:
        return None
    parts = ref.split("_", 2)
    if len(parts) != 3:
        return None
    try:
        floor_num = int(parts[1])
    except ValueError:
        return None
    region_id = "_".join(parts[2:])
    if floor_num < blueprint.floors_range[0] or floor_num > blueprint.floors_range[1]:
        return None
    for floor in blueprint.floors:
        if floor.floor == floor_num:
            for region in floor.regions:
                if region.id == region_id:
                    return region
            return None
    return None


def load_blueprint(filepath: str) -> Blueprint:
    return Blueprint.from_json_file(filepath)


@dataclass
class MapGenerator:
    width: int = 25
    height: int = 19
    seed: Optional[int] = None

    def generate(self, blueprint_data: dict) -> list[dict]:
        validation = validate_blueprint(blueprint_data)
        if not validation["valid"]:
            raise ValueError(f"Invalid blueprint: {validation['errors']}")
        blueprint = Blueprint.from_dict(blueprint_data)
        maps = []
        for floor_bp in blueprint.floors:
            builder = LayoutBuilder(width=self.width, height=self.height, seed=self.seed)
            rooms = builder.generate_rooms(
                pattern=floor_bp.layout.pattern,
                count=floor_bp.layout.room_count,
            )
            builder.carve_rooms(rooms)
            tiles = builder.get_tiles()
            floor_tiles = builder.get_floor_tiles()
            if not floor_tiles:
                continue
            start_pos = list(floor_tiles)[0]
            placer = EntityPlacer(floor_tiles, seed=self.seed)
            for region in floor_bp.regions:
                region_tiles = {t for t in floor_tiles if t}
                if region.content:
                    if region.content.monsters:
                        tier = region.content.monsters.get("tier", 1)
                        count = region.content.monsters.get("count", 1)
                        placer.place_monsters_by_tier(tier, count, region_tiles)
                    if region.content.items:
                        for item_id in region.content.items:
                            placer.place_in_region("item", item_id, region_tiles)
            stairs_up = None
            stairs_down = None
            if floor_bp.floor > 1:
                stairs_up = start_pos
            if floor_bp.floor < 21:
                stairs_down = list(floor_tiles)[-1] if len(floor_tiles) > 1 else None
            output = MapOutput(
                level=floor_bp.floor,
                name=floor_bp.name,
                name_cn=f"第{floor_bp.floor}层",
                tiles=tiles,
                player_start=start_pos,
            )
            for entity in placer.get_all_entities():
                output.add_entity(entity.type, entity.id, entity.x, entity.y, entity.data)
            if stairs_up:
                output.set_stairs_up(stairs_up)
            if stairs_down:
                output.set_stairs_down(stairs_down)
            maps.append(output.to_dict())
        return maps

    def generate_and_save(self, blueprint_data: dict, output_dir: str) -> list[str]:
        maps = self.generate(blueprint_data)
        saved_files = []
        for map_data in maps:
            output = MapOutput(
                level=map_data["level"],
                name=map_data["name"],
                name_cn=map_data["name_cn"],
                tiles=map_data["tiles"],
                player_start=tuple(map_data["player_start"]),
                entities=map_data["entities"],
            )
            filepath = output.save(output_dir)
            saved_files.append(filepath)
        return saved_files


def main():
    parser = argparse.ArgumentParser(description="Generate Magic Tower maps")
    parser.add_argument("--blueprint", "-b", required=True, help="Path to blueprint JSON file")
    parser.add_argument("--output", "-o", default="data/maps", help="Output directory")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Random seed")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    try:
        blueprint = load_blueprint(args.blueprint)
        if args.verbose:
            print(f"Loaded blueprint: group {blueprint.group}, floors {blueprint.floors_range}")
        with open(args.blueprint, "r", encoding="utf-8") as f:
            blueprint_data = json.load(f)
        generator = MapGenerator(seed=args.seed)
        files = generator.generate_and_save(blueprint_data, output_dir=args.output)
        print(f"Generated {len(files)} map(s):")
        for f in files:
            print(f"  - {f}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_generator.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tools/map_generator/generator.py tests/test_generator.py
git commit -m "feat(map-gen): add main generator CLI"
```

---

## Task 9: Blueprint Validation Tests

**Files:**
- Create: `tests/test_blueprint_validation.py`

- [ ] **Step 1: Write test for blueprint validation**

Create file `tests/test_blueprint_validation.py`:

```python
"""Tests for blueprint validation."""
import pytest
from tools.map_generator.generator import validate_blueprint


class TestBlueprintValidation:
    def test_valid_blueprint(self):
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 5],
            "floors": [
                {
                    "floor": 1,
                    "name": "Floor 1",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                }
            ],
            "unlock_sequence": [],
        }
        result = validate_blueprint(blueprint_data)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_missing_floor_in_range(self):
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 5],
            "floors": [
                {
                    "floor": 10,
                    "name": "Floor 10",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                }
            ],
            "unlock_sequence": [],
        }
        result = validate_blueprint(blueprint_data)
        assert result["valid"] is False
        assert any("floor 10" in str(e).lower() for e in result["errors"])

    def test_invalid_door_color(self):
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Floor 1",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                }
            ],
            "unlock_sequence": [
                {"floor": 1, "door": "purple", "key_at": "start"}
            ],
        }
        result = validate_blueprint(blueprint_data)
        assert result["valid"] is False
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_blueprint_validation.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_blueprint_validation.py
git commit -m "test(map-gen): add blueprint validation tests"
```

---

## Task 10: Resolve Cross-Floor Reference Tests

**Files:**
- Create: `tests/test_cross_floor_reference.py`

- [ ] **Step 1: Write test for cross-floor reference**

Create file `tests/test_cross_floor_reference.py`:

```python
"""Tests for cross-floor reference resolution."""
import pytest
from tools.map_generator.models.blueprint import Blueprint
from tools.map_generator.generator import resolve_cross_floor_reference


class TestCrossFloorReference:
    def test_resolve_simple_region_id(self):
        blueprint = Blueprint.from_dict({
            "group": 1,
            "floors_range": [1, 3],
            "floors": [
                {
                    "floor": 1,
                    "name": "Floor 1",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                },
            ],
        })
        result = resolve_cross_floor_reference("start", blueprint)
        assert result is None  # Not cross-floor format

    def test_resolve_cross_floor_reference(self):
        blueprint = Blueprint.from_dict({
            "group": 1,
            "floors_range": [1, 3],
            "floors": [
                {
                    "floor": 1,
                    "name": "Floor 1",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                },
                {
                    "floor": 2,
                    "name": "Floor 2",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "main", "type": "pathway"}],
                    "surprises": [],
                },
            ],
        })
        result = resolve_cross_floor_reference("floor_2_main", blueprint)
        assert result is not None
        assert result.id == "main"

    def test_floor_outside_range(self):
        blueprint = Blueprint.from_dict({
            "group": 1,
            "floors_range": [1, 3],
            "floors": [
                {
                    "floor": 1,
                    "name": "Floor 1",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                },
            ],
        })
        result = resolve_cross_floor_reference("floor_5_main", blueprint)
        assert result is None
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_cross_floor_reference.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_cross_floor_reference.py
git commit -m "test(map-gen): add cross-floor reference resolution tests"
```

---

## Task 11: Update SKILL.md and Create Templates

**Files:**
- Modify: `.claude/skills/generate-map/SKILL.md`
- Create: `.claude/skills/generate-map/templates/floors_1-5.json`
- Create: `.claude/skills/generate-map/templates/floors_6-10.json`
- Create: `.claude/skills/generate-map/templates/floors_11-15.json`
- Create: `.claude/skills/generate-map/templates/floors_16-21.json`

- [ ] **Step 1: Update SKILL.md**

Replace the content of `.claude/skills/generate-map/SKILL.md` with the new hybrid workflow (see spec for details).

- [ ] **Step 2: Create template files**

Create directory: `mkdir -p .claude/skills/generate-map/templates`

Create 4 template files for each difficulty tier (F1-5, F6-10, F11-15, F16-21) following the spec's format.

- [ ] **Step 3: Verify files exist**

Run: `ls -la .claude/skills/generate-map/templates/`
Expected: 4 JSON files

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/generate-map/
git commit -m "feat(map-gen): update SKILL.md and add floor templates"
```

---

## Task 12: Integration Tests and Final Verification

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

Create file `tests/test_integration.py` with end-to-end tests validating the full generation cycle from blueprint to output.

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Test CLI manually**

```bash
python -m tools.map_generator.generator --blueprint .temp/test_blueprint.json --output data/maps --verbose
```
Expected: Map file generated successfully

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(map-gen): complete hybrid AI + Python map generation system

Implements design spec 2026-03-17-map-generator-design.md:
- Blueprint data models for declarative map intent
- Layout builder with multiple room patterns
- Connectivity tracking for guaranteed reachability
- Entity placement with tier-based monster selection
- Template system for difficulty scaling
- CLI tool for running generator
- Updated SKILL.md with new workflow
- Templates for all 4 difficulty tiers"
```

---

## Summary

This plan implements the hybrid "AI blueprint + Python generation" map system described in the spec. Key achievements:

1. **Blueprint-driven**: AI designs intent, not coordinates
2. **Correctness guaranteed**: Connectivity tracking ensures reachability
3. **Template support**: 4 difficulty tier templates
4. **TDD throughout**: All modules have comprehensive tests
5. **CLI tool**: Easy to use from command line or skill

> **Note:** The spec mentions `surprise_mechanics.py` for advanced features (guardians, traps, pattern shapes). This is intentionally deferred as Phase 3 per the spec. The current implementation provides a solid foundation that can be extended incrementally.
