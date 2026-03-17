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
        assert any("floor 10" in str(e).lower() or "10" in str(e) for e in result["errors"])

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

    def test_duplicate_floor_number(self):
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
                },
                {
                    "floor": 1,
                    "name": "Floor 1 Duplicate",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [],
                }
            ],
            "unlock_sequence": [],
        }
        result = validate_blueprint(blueprint_data)
        assert result["valid"] is False
        assert any("duplicate" in str(e).lower() for e in result["errors"])
