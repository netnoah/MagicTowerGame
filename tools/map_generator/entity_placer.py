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
