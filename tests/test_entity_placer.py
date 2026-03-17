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
