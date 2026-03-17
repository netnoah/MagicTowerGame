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
