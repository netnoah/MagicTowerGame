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
