"""Tests for layout builder."""
import pytest
from tools.map_generator.layout_builder import LayoutBuilder, Room


class TestRoom:
    def test_room_creation(self):
        room = Room(id="entrance", x1=1, y1=1, x2=5, y2=5)
        assert room.id == "entrance"
        assert room.width == 4
        assert room.height == 4
        assert room.center == (3, 3)

    def test_room_tiles(self):
        room = Room(id="test", x1=0, y1=0, x2=2, y2=2)
        tiles = list(room.tiles())
        assert (0, 0) in tiles
        assert (1, 1) in tiles
        assert len(tiles) == 9


class TestLayoutBuilder:
    def test_create_empty_map(self):
        builder = LayoutBuilder(width=25, height=19)
        tiles = builder.get_tiles()
        assert len(tiles) == 19
        assert len(tiles[0]) == 25
        assert all(tiles[y][x] == 2 for y in range(19) for x in range(25))

    def test_generate_simple_rooms(self):
        builder = LayoutBuilder(width=25, height=19)
        rooms = builder.generate_rooms(pattern="simple_rooms", count=3)
        assert len(rooms) == 3
        for i, r1 in enumerate(rooms):
            for r2 in rooms[i+1:]:
                assert not r1.overlaps(r2)

    def test_carve_rooms(self):
        builder = LayoutBuilder(width=25, height=19)
        rooms = builder.generate_rooms(pattern="simple_rooms", count=2)
        builder.carve_rooms(rooms)
        tiles = builder.get_tiles()
        floor_count = sum(1 for y in range(19) for x in range(25) if tiles[y][x] == 1)
        assert floor_count > 50

    def test_get_floor_tiles(self):
        builder = LayoutBuilder(width=25, height=19)
        rooms = builder.generate_rooms(pattern="simple_rooms", count=2)
        builder.carve_rooms(rooms)
        floor_tiles = builder.get_floor_tiles()
        assert len(floor_tiles) > 50
        assert all(isinstance(t, tuple) and len(t) == 2 for t in floor_tiles)
