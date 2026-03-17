"""Connectivity tracking for map generation."""
from collections import deque
from typing import Optional


def flood_fill(
    tiles: list[list[int]],
    start_x: int,
    start_y: int,
    blocked: Optional[set[tuple[int, int]]] = None,
    floor_tile: int = 1,
    passable: Optional[set[tuple[int, int]]] = None,
) -> set[tuple[int, int]]:
    if blocked is None:
        blocked = set()
    if passable is None:
        passable = set()
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    visited: set[tuple[int, int]] = set()
    queue = deque([(start_x, start_y)])
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or (x, y) in blocked:
            continue
        if not (0 <= x < width and 0 <= y < height):
            continue
        if tiles[y][x] != floor_tile and (x, y) not in passable:
            continue
        visited.add((x, y))
        queue.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return visited


def get_all_regions(tiles: list[list[int]], floor_tile: int = 1) -> list[set[tuple[int, int]]]:
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    regions: list[set[tuple[int, int]]] = []
    visited: set[tuple[int, int]] = set()
    for y in range(height):
        for x in range(width):
            if tiles[y][x] == floor_tile and (x, y) not in visited:
                region = flood_fill(tiles, x, y, floor_tile=floor_tile)
                regions.append(region)
                visited.update(region)
    return regions


class ConnectivityTracker:
    TILE_FLOOR = 1

    def __init__(
        self,
        tiles: list[list[int]],
        start: tuple[int, int],
        blocked: Optional[set[tuple[int, int]]] = None,
    ):
        self._tiles = tiles
        self.start = start
        self._blocked = blocked or set()
        self._doors: set[tuple[int, int]] = set()
        self._reachable = self._compute_reachable()

    def _compute_reachable(self) -> set[tuple[int, int]]:
        effective_blocked = self._blocked - self._doors
        return flood_fill(
            self._tiles,
            self.start[0],
            self.start[1],
            blocked=effective_blocked,
            floor_tile=self.TILE_FLOOR,
            passable=self._doors,
        )

    @property
    def reachable(self) -> set[tuple[int, int]]:
        return self._reachable.copy()

    def add_door(self, position: tuple[int, int]):
        self._doors.add(position)
        self._reachable = self._compute_reachable()

    def is_reachable(self, position: tuple[int, int]) -> bool:
        return position in self._reachable

    def get_reachable_positions(self) -> set[tuple[int, int]]:
        return self._reachable.copy()
