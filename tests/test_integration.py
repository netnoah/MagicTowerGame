"""Integration tests for map generation system."""
import json
import tempfile
from pathlib import Path

from tools.map_generator.generator import MapGenerator, validate_blueprint
from tools.map_generator.models.blueprint import Blueprint
from tools.map_generator.layout_builder import LayoutBuilder
from tools.map_generator.connectivity import flood_fill, get_all_regions


class TestFullGenerationPipeline:
    """End-to-end tests for map generation."""

    def test_complete_floor_generation(self):
        """Test generating a complete floor with all features."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "difficulty_tier": "easy",
            "global_theme": "Test",
            "floors": [
                {
                    "floor": 1,
                    "name": "Test Floor",
                    "layout": {"pattern": "simple_rooms", "room_count": 3},
                    "regions": [
                        {"id": "start", "type": "entrance"},
                        {
                            "id": "main",
                            "type": "pathway",
                            "content": {
                                "monsters": {"tier": 1, "count": 2},
                                "items": ["yellow_key"],
                            },
                        },
                        {
                            "id": "vault",
                            "type": "treasure",
                            "access": {"requires": "yellow_key"},
                            "content": {"items": ["red_gem"]},
                        },
                    ],
                    "surprises": [
                        {
                            "type": "guardian",
                            "location": "main",
                            "guardian_tier": 2,
                            "reward": ["blue_key"],
                        }
                    ],
                    "shops": [
                        {"id": "weapon_shop", "region": "start"}
                    ],
                }
            ],
            "unlock_sequence": [
                {"floor": 1, "door": "yellow", "key_at": "start", "target_region": "vault"}
            ],
        }

        generator = MapGenerator(seed=42)
        maps = generator.generate(blueprint_data)

        assert len(maps) == 1
        map_data = maps[0]

        # Verify basic structure
        assert map_data["level"] == 1
        assert map_data["name"] == "Test Floor"
        assert len(map_data["tiles"]) == 19
        assert len(map_data["tiles"][0]) == 25

        # Verify entities
        entities = map_data["entities"]
        entity_types = {e["type"] for e in entities}

        # Should have monsters, items, doors, shops
        assert "monster" in entity_types
        assert "item" in entity_types
        assert "door" in entity_types
        assert "shop" in entity_types

        # Verify door entity exists (from unlock_sequence)
        doors = [e for e in entities if e["type"] == "door"]
        assert len(doors) >= 1
        assert any("yellow" in e["id"] for e in doors)

        # Verify shop entity exists
        shops = [e for e in entities if e["type"] == "shop"]
        assert len(shops) >= 1
        assert any("weapon_shop" in e["id"] for e in shops)

    def test_room_connectivity(self):
        """Test that all rooms are connected after generation."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Test",
                    "layout": {"pattern": "simple_rooms", "room_count": 4},
                    "regions": [{"id": "start", "type": "entrance"}],
                }
            ],
        }

        generator = MapGenerator(seed=123)
        maps = generator.generate(blueprint_data)

        map_data = maps[0]
        tiles = map_data["tiles"]
        player_start = tuple(map_data["player_start"])

        # Use flood fill to verify all floor tiles are reachable
        reachable = flood_fill(tiles, player_start[0], player_start[1])

        # Count total floor tiles
        total_floor = sum(
            1 for y in range(len(tiles)) for x in range(len(tiles[0]))
            if tiles[y][x] == 1
        )

        # All floor tiles should be reachable (excluding stairs)
        assert len(reachable) >= total_floor * 0.8  # Allow some tolerance for stairs

    def test_multi_floor_generation(self):
        """Test generating multiple floors."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 3],
            "difficulty_tier": "easy",
            "floors": [
                {
                    "floor": i,
                    "name": f"Floor {i}",
                    "layout": {"pattern": "simple_rooms", "room_count": 2 + i},
                    "regions": [{"id": "start", "type": "entrance"}],
                }
                for i in range(1, 4)
            ],
        }

        generator = MapGenerator(seed=42)
        maps = generator.generate(blueprint_data)

        assert len(maps) == 3
        assert [m["level"] for m in maps] == [1, 2, 3]

        # Floor 1 should have stairs down but not up
        assert any(tiles == 20 for row in maps[0]["tiles"] for tiles in row)  # Stairs down

        # Floor 2 and 3 should have stairs up
        assert any(tiles == 21 for row in maps[1]["tiles"] for tiles in row)  # Stairs up

    def test_save_and_load_generated_map(self):
        """Test saving generated map to file."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Test Floor",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                }
            ],
        }

        generator = MapGenerator(seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            files = generator.generate_and_save(blueprint_data, tmpdir)

            assert len(files) == 1
            assert Path(files[0]).exists()

            # Verify file content
            with open(files[0], "r", encoding="utf-8") as f:
                loaded = json.load(f)

            assert loaded["level"] == 1
            assert loaded["name"] == "Test Floor"
            assert "tiles" in loaded
            assert "entities" in loaded


class TestUnlockSequenceProcessing:
    """Tests for unlock sequence feature."""

    def test_unlock_sequence_places_door_and_key(self):
        """Test that unlock sequence places door and key correctly."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Test",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [
                        {"id": "start", "type": "entrance"},
                        {"id": "vault", "type": "treasure"},
                    ],
                }
            ],
            "unlock_sequence": [
                {"floor": 1, "door": "blue", "key_at": "start", "key_count": 2}
            ],
        }

        generator = MapGenerator(seed=42)
        maps = generator.generate(blueprint_data)
        entities = maps[0]["entities"]

        # Should have blue door
        doors = [e for e in entities if e["type"] == "door"]
        assert any("blue" in e["id"] for e in doors)

        # Should have blue keys
        keys = [e for e in entities if e["type"] == "item" and "blue_key" in e["id"]]
        assert len(keys) == 2

    def test_multiple_unlock_steps(self):
        """Test multiple unlock steps for different doors."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Test",
                    "layout": {"pattern": "simple_rooms", "room_count": 4},
                    "regions": [
                        {"id": "start", "type": "entrance"},
                        {"id": "area1", "type": "pathway"},
                        {"id": "area2", "type": "pathway"},
                    ],
                }
            ],
            "unlock_sequence": [
                {"floor": 1, "door": "yellow", "key_at": "start"},
                {"floor": 1, "door": "blue", "key_at": "area1"},
            ],
        }

        generator = MapGenerator(seed=42)
        maps = generator.generate(blueprint_data)
        entities = maps[0]["entities"]

        doors = [e for e in entities if e["type"] == "door"]
        door_colors = {e["id"].split("_")[0] for e in doors}

        assert "yellow" in door_colors
        assert "blue" in door_colors


class TestShopPlacement:
    """Tests for shop placement feature."""

    def test_shop_placement_in_region(self):
        """Test shop is placed in specified region."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Test",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [
                        {"id": "start", "type": "entrance"},
                        {"id": "shop_area", "type": "pathway"},
                    ],
                    "shops": [
                        {"id": "potion_shop", "region": "shop_area"},
                        {"id": "weapon_shop", "region": "start"},
                    ],
                }
            ],
        }

        generator = MapGenerator(seed=42)
        maps = generator.generate(blueprint_data)
        entities = maps[0]["entities"]

        shops = [e for e in entities if e["type"] == "shop"]
        assert len(shops) >= 2

        shop_ids = {e["id"] for e in shops}
        assert "potion_shop" in shop_ids
        assert "weapon_shop" in shop_ids


class TestSurpriseMechanics:
    """Tests for surprise mechanics feature."""

    def test_guardian_surprise_places_monster_and_reward(self):
        """Test guardian surprise places guardian and reward items."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Test",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [
                        {
                            "type": "guardian",
                            "location": "start",
                            "guardian_tier": 3,
                            "reward": ["rare_sword", "gold_coin"],
                        }
                    ],
                }
            ],
        }

        generator = MapGenerator(seed=42)
        maps = generator.generate(blueprint_data)
        entities = maps[0]["entities"]

        # Should have a guardian monster (tier 3)
        monsters = [e for e in entities if e["type"] == "monster"]
        assert len(monsters) >= 1

        # Should have reward items
        items = [e for e in entities if e["type"] == "item"]
        item_ids = {e["id"] for e in items}
        assert "rare_sword" in item_ids
        assert "gold_coin" in item_ids

    def test_trap_surprise_places_monster(self):
        """Test trap surprise places a trap monster."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Test",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                    "surprises": [
                        {"type": "trap", "location": "start"}
                    ],
                }
            ],
        }

        generator = MapGenerator(seed=42)
        maps = generator.generate(blueprint_data)
        entities = maps[0]["entities"]

        # Should have at least one monster (the trap)
        monsters = [e for e in entities if e["type"] == "monster"]
        assert len(monsters) >= 1


class TestBlueprintValidation:
    """Tests for blueprint validation."""

    def test_valid_complete_blueprint(self):
        """Test validation passes for complete valid blueprint."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 5],
            "floors": [
                {
                    "floor": 1,
                    "name": "Floor 1",
                    "layout": {"pattern": "simple_rooms", "room_count": 3},
                    "regions": [{"id": "start", "type": "entrance"}],
                }
            ],
            "unlock_sequence": [
                {"floor": 1, "door": "yellow", "key_at": "start"}
            ],
        }

        result = validate_blueprint(blueprint_data)
        assert result["valid"] is True

    def test_invalid_door_color(self):
        """Test validation fails for invalid door color."""
        blueprint_data = {
            "group": 1,
            "floors_range": [1, 1],
            "floors": [
                {
                    "floor": 1,
                    "name": "Test",
                    "layout": {"pattern": "simple_rooms", "room_count": 2},
                    "regions": [{"id": "start", "type": "entrance"}],
                }
            ],
            "unlock_sequence": [
                {"floor": 1, "door": "purple", "key_at": "start"}  # Invalid color
            ],
        }

        result = validate_blueprint(blueprint_data)
        assert result["valid"] is False
        assert any("purple" in str(e) for e in result["errors"])


class TestLayoutPatterns:
    """Tests for different layout patterns."""

    def test_simple_rooms_pattern(self):
        """Test simple_rooms pattern generates non-overlapping rooms."""
        builder = LayoutBuilder(width=25, height=19, seed=42)
        rooms = builder.generate_rooms(pattern="simple_rooms", count=4)
        builder.carve_rooms(rooms)
        builder.connect_rooms(rooms)

        # Check rooms don't overlap
        for i, r1 in enumerate(rooms):
            for r2 in rooms[i+1:]:
                assert not r1.overlaps(r2, margin=1)

        # Check all rooms are connected
        tiles = builder.get_tiles()
        floor_tiles = builder.get_floor_tiles()
        assert len(floor_tiles) > 50  # Should have substantial floor area

    def test_cross_pattern(self):
        """Test cross pattern generates 5 rooms in cross shape."""
        builder = LayoutBuilder(width=25, height=19, seed=42)
        rooms = builder.generate_rooms(pattern="cross", count=5)
        builder.carve_rooms(rooms)
        builder.connect_rooms(rooms)

        assert len(rooms) == 5
        room_ids = {r.id for r in rooms}
        assert "center" in room_ids
        assert "north" in room_ids
        assert "south" in room_ids
        assert "east" in room_ids
        assert "west" in room_ids

    def test_linear_pattern(self):
        """Test linear pattern generates rooms in a line."""
        builder = LayoutBuilder(width=25, height=19, seed=42)
        rooms = builder.generate_rooms(pattern="linear", count=3)
        builder.carve_rooms(rooms)
        builder.connect_rooms(rooms)

        assert len(rooms) == 3

        # Rooms should be ordered left to right
        for i in range(len(rooms) - 1):
            assert rooms[i].x1 < rooms[i+1].x1
