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
