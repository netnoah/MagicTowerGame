"""Tests for connectivity tracking."""
import pytest
from tools.map_generator.connectivity import (
    ConnectivityTracker,
    flood_fill,
    get_all_regions,
)


class TestFloodFill:
    def test_flood_fill_simple(self):
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        result = flood_fill(tiles, 2, 2)
        assert len(result) == 9
        assert (2, 2) in result

    def test_flood_fill_with_blocked(self):
        # Wall column at x=2 creates two separate regions
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        result = flood_fill(tiles, 1, 1)
        assert len(result) == 3  # Left side only: (1,1), (1,2), (1,3)
        assert (3, 2) not in result  # Right side not reachable


class TestGetAllRegions:
    def test_single_region(self):
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 1, 1, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        regions = get_all_regions(tiles)
        assert len(regions) == 1

    def test_multiple_regions(self):
        tiles = [
            [2, 2, 2, 2, 2, 2, 2],
            [2, 1, 1, 2, 1, 1, 2],
            [2, 1, 1, 2, 1, 1, 2],
            [2, 2, 2, 2, 2, 2, 2],
        ]
        regions = get_all_regions(tiles)
        assert len(regions) == 2


class TestConnectivityTracker:
    def test_initialization(self):
        tiles = [
            [2, 2, 2],
            [2, 1, 2],
            [2, 2, 2],
        ]
        tracker = ConnectivityTracker(tiles, start=(1, 1))
        assert tracker.start == (1, 1)
        assert len(tracker.reachable) == 1

    def test_add_door_connection(self):
        # Wall column at x=2 separates left and right
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        tracker = ConnectivityTracker(tiles, start=(1, 2))
        assert len(tracker.reachable) == 3  # Left side only
        tracker.add_door((2, 2))  # Open door at wall position
        assert len(tracker.reachable) == 7  # 3 left + 1 door + 3 right

    def test_is_reachable(self):
        tiles = [
            [2, 2, 2, 2, 2],
            [2, 1, 2, 1, 2],
            [2, 1, 2, 1, 2],
            [2, 2, 2, 2, 2],
        ]
        tracker = ConnectivityTracker(tiles, start=(1, 1))
        assert tracker.is_reachable((1, 2))
        assert not tracker.is_reachable((3, 1))
