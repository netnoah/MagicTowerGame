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
