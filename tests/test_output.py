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
