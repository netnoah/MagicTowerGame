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
