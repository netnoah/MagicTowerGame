"""Main map generator CLI."""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass

from tools.map_generator.models.blueprint import Blueprint
from tools.map_generator.layout_builder import LayoutBuilder
from tools.map_generator.connectivity import ConnectivityTracker
from tools.map_generator.entity_placer import EntityPlacer
from tools.map_generator.output import MapOutput


VALID_DOOR_COLORS = {"yellow", "blue", "red", "green"}


def validate_blueprint(data: dict) -> dict:
    errors = []
    if "floors_range" not in data:
        errors.append({"message": "Missing required field: floors_range"})
        return {"valid": False, "errors": errors}
    if "floors" not in data:
        errors.append({"message": "Missing required field: floors"})
        return {"valid": False, "errors": errors}
    floors_range = data.get("floors_range", [1, 1])
    floor_numbers = set()
    for floor_data in data.get("floors", []):
        floor_num = floor_data.get("floor")
        if floor_num is None:
            errors.append({"message": "Floor missing 'floor' field"})
            continue
        if floor_num < floors_range[0] or floor_num > floors_range[1]:
            errors.append({
                "message": f"Floor {floor_num} is outside range {floors_range[0]}-{floors_range[1]}"
            })
        if floor_num in floor_numbers:
            errors.append({"message": f"Duplicate floor number: {floor_num}"})
        floor_numbers.add(floor_num)
    if "unlock_sequence" in data:
        for step in data["unlock_sequence"]:
            door_color = step.get("door") or step.get("door_color")
            if door_color and door_color not in VALID_DOOR_COLORS:
                errors.append({
                    "message": f"Invalid door color: {door_color}. Valid: {VALID_DOOR_COLORS}"
                })
    return {"valid": len(errors) == 0, "errors": errors}


def resolve_cross_floor_reference(ref: str, blueprint: Blueprint) -> Optional[Any]:
    if "_" not in ref:
        return None
    parts = ref.split("_", 2)
    if len(parts) != 3:
        return None
    try:
        floor_num = int(parts[1])
    except ValueError:
        return None
    region_id = "_".join(parts[2:])
    if floor_num < blueprint.floors_range[0] or floor_num > blueprint.floors_range[1]:
        return None
    for floor in blueprint.floors:
        if floor.floor == floor_num:
            for region in floor.regions:
                if region.id == region_id:
                    return region
            return None
    return None


def load_blueprint(filepath: str) -> Blueprint:
    return Blueprint.from_json_file(filepath)


def get_region_tiles(
    region_id: str,
    rooms: list,
    floor_tiles: set[tuple[int, int]],
    all_regions: list
) -> set[tuple[int, int]]:
    """Get floor tiles that belong to a specific region."""
    # If region matches a room id, use that room's tiles
    for room in rooms:
        if room.id == region_id:
            return {t for t in floor_tiles if room.contains(t[0], t[1])}

    # Otherwise, try to distribute tiles among regions based on room count
    if not all_regions:
        return floor_tiles

    # Find the region index and assign proportional tiles
    for i, region in enumerate(all_regions):
        if region.id == region_id:
            # Simple distribution: divide floor tiles among regions
            tiles_list = list(floor_tiles)
            region_count = len(all_regions)
            tiles_per_region = len(tiles_list) // region_count
            start_idx = i * tiles_per_region
            end_idx = start_idx + tiles_per_region if i < region_count - 1 else len(tiles_list)
            return set(tiles_list[start_idx:end_idx])

    return floor_tiles


def find_passage_to_region(
    builder: LayoutBuilder,
    rooms: list,
    target_region_id: str,
    reachable_tiles: set[tuple[int, int]],
    floor_tiles: set[tuple[int, int]],
    all_regions: list,
    passage_map: dict[tuple[int, int], tuple[str, str]],
    region_to_rooms: dict[str, list],
) -> Optional[tuple[int, int]]:
    """Find a passage position that blocks access to the target region.

    Uses the passage_map to find passages that connect rooms in different regions.
    """
    import random

    if not target_region_id:
        return None

    # Get rooms in target region
    target_rooms = region_to_rooms.get(target_region_id, [])
    if not target_rooms:
        # Fallback: use tile-based approach
        target_tiles = get_region_tiles(target_region_id, rooms, floor_tiles, all_regions)
        for x, y in floor_tiles:
            adjacent_to_reachable = False
            adjacent_to_target = False
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in reachable_tiles:
                    adjacent_to_reachable = True
                if (nx, ny) in target_tiles:
                    adjacent_to_target = True
            if adjacent_to_reachable and adjacent_to_target:
                return (x, y)
        return None

    target_room_ids = {r.id for r in target_rooms}

    # Find passages that connect a room in accessible region to a room in target region
    candidate_passages = []
    for passage_pos, (room1_id, room2_id) in passage_map.items():
        if room1_id in target_room_ids or room2_id in target_room_ids:
            # This passage connects to target region
            candidate_passages.append(passage_pos)

    if candidate_passages:
        return random.choice(candidate_passages)

    # Fallback: find any passage adjacent to target region tiles
    target_tiles = get_region_tiles(target_region_id, rooms, floor_tiles, all_regions)
    for passage_pos in passage_map.keys():
        x, y = passage_pos
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) in target_tiles:
                return passage_pos

    return None


def map_regions_to_rooms(
    regions: list,
    rooms: list,
    floor_tiles: set[tuple[int, int]]
) -> dict[str, list]:
    """Map each region to the room(s) it occupies based on tile overlap."""
    region_to_rooms = {}

    for region in regions:
        region_tiles = get_region_tiles(region.id, rooms, floor_tiles, regions)
        associated_rooms = []

        for room in rooms:
            room_tiles = {t for t in floor_tiles if room.contains(t[0], t[1])}
            # If region has significant overlap with room
            overlap = len(region_tiles & room_tiles)
            if overlap > 0:
                associated_rooms.append(room)

        region_to_rooms[region.id] = associated_rooms

    return region_to_rooms


@dataclass
class MapGenerator:
    width: int = 25
    height: int = 19
    seed: Optional[int] = None

    def generate(self, blueprint_data: dict) -> list[dict]:
        validation = validate_blueprint(blueprint_data)
        if not validation["valid"]:
            raise ValueError(f"Invalid blueprint: {validation['errors']}")
        blueprint = Blueprint.from_dict(blueprint_data)
        maps = []

        # Build floor lookup for cross-floor references
        floor_lookup = {f.floor: f for f in blueprint.floors}

        for floor_bp in blueprint.floors:
            # Use per-floor seed for variety: combine base seed with floor number
            floor_seed = None
            if self.seed is not None:
                floor_seed = self.seed * 1000 + floor_bp.floor
            else:
                # Generate a seed based on floor number for reproducibility
                import time
                floor_seed = int(time.time() * 1000) % (10**9) + floor_bp.floor * 12345

            builder = LayoutBuilder(width=self.width, height=self.height, seed=floor_seed)
            rooms = builder.generate_rooms(
                pattern=floor_bp.layout.pattern,
                count=floor_bp.layout.room_count,
            )
            builder.carve_rooms(rooms)

            # Connect rooms with passages and track which rooms each passage connects
            passage_map = builder.connect_rooms_with_tracking(rooms)

            tiles = builder.get_tiles()
            floor_tiles = builder.get_floor_tiles()
            if not floor_tiles:
                continue

            # Determine start position (first room center or first floor tile)
            if rooms:
                start_pos = rooms[0].center
            else:
                start_pos = list(floor_tiles)[0]

            placer = EntityPlacer(floor_tiles, seed=self.seed)

            # Track door positions for connectivity
            door_positions: set[tuple[int, int]] = set()

            # Initialize connectivity tracker from start position
            # Doors are initially treated as blocked (not passable)
            tracker = ConnectivityTracker(tiles, start_pos, blocked=set())

            # Map regions to rooms for better door placement
            region_to_rooms = map_regions_to_rooms(floor_bp.regions, rooms, floor_tiles)

            # Track accessible regions (starts with entrance)
            accessible_region_ids: set[str] = set()
            for region in floor_bp.regions:
                if region.type == "entrance":
                    accessible_region_ids.add(region.id)
                    break

            # Process unlock_sequence for this floor
            floor_unlock_steps = [
                step for step in blueprint.unlock_sequence
                if step.floor == floor_bp.floor
            ]

            # STEP 1: Place doors FIRST (before other entities) to reserve passage positions
            for step in floor_unlock_steps:
                target_region = step.target_region if hasattr(step, 'target_region') and step.target_region else None

                door_pos = None
                if target_region:
                    # Use passage_map to find the right passage
                    door_pos = find_passage_to_region(
                        builder, rooms, target_region,
                        floor_tiles, floor_tiles, floor_bp.regions,  # Use all floor tiles for initial search
                        passage_map, region_to_rooms
                    )

                # Fallback: place door at any passage between rooms
                if not door_pos:
                    for passage_pos in passage_map.keys():
                        if passage_pos not in door_positions and passage_pos in floor_tiles:
                            door_pos = passage_pos
                            break

                # Final fallback: place at boundary of any room
                if not door_pos and rooms:
                    for room in rooms[1:]:
                        boundary = builder.get_boundary_tiles(room)
                        available = boundary & floor_tiles
                        if available:
                            door_pos = list(available)[0]
                            break

                if door_pos:
                    # Place door entity - use try/except to handle already occupied positions
                    # Note: entity_id should be just the color (e.g., "yellow") for game compatibility
                    try:
                        placer.place_entity_at("door", step.door, door_pos)
                        door_positions.add(door_pos)
                        tracker.add_door(door_pos)
                    except ValueError:
                        # Position already occupied, skip this door
                        pass

            # STEP 2: Now place content in regions without access requirements
            for region in floor_bp.regions:
                region_tiles = get_region_tiles(
                    region.id, rooms, floor_tiles, floor_bp.regions
                )

                # Skip regions with access requirements for now
                if region.access and region.access.requires:
                    continue

                accessible_region_ids.add(region.id)

                if region.content:
                    if region.content.monsters:
                        tier = region.content.monsters.get("tier", 1)
                        count = region.content.monsters.get("count", 1)
                        placer.place_monsters_by_tier(tier, count, region_tiles)
                    if region.content.items:
                        for item_id in region.content.items:
                            placer.place_in_region("item", item_id, region_tiles)

            # STEP 3: Place keys in accessible regions
            current_reachable = tracker.get_reachable_positions()
            for step in floor_unlock_steps:
                key_region = step.key_at
                key_tiles = get_region_tiles(key_region, rooms, floor_tiles, floor_bp.regions)

                # Ensure key is placed in reachable area
                reachable_key_tiles = key_tiles & current_reachable & placer.available_positions
                if not reachable_key_tiles:
                    reachable_key_tiles = current_reachable & placer.available_positions
                if not reachable_key_tiles:
                    reachable_key_tiles = placer.available_positions

                # Generate key item id from door color and place it
                key_id = f"{step.door}_key"
                for _ in range(step.key_count):
                    if reachable_key_tiles:
                        placer.place_in_region("item", key_id, reachable_key_tiles)

            # STEP 4: Place content in regions with access requirements
            for region in floor_bp.regions:
                if not region.access or not region.access.requires:
                    continue

                region_tiles = get_region_tiles(
                    region.id, rooms, floor_tiles, floor_bp.regions
                )

                if region.content:
                    if region.content.monsters:
                        tier = region.content.monsters.get("tier", 1)
                        count = region.content.monsters.get("count", 1)
                        placer.place_monsters_by_tier(tier, count, region_tiles)
                    if region.content.items:
                        for item_id in region.content.items:
                            placer.place_in_region("item", item_id, region_tiles)

            # Process shops
            for shop_config in floor_bp.shops:
                if shop_config.region:
                    shop_tiles = get_region_tiles(
                        shop_config.region, rooms, floor_tiles, floor_bp.regions
                    )
                else:
                    shop_tiles = floor_tiles
                placer.place_in_region("shop", shop_config.id, shop_tiles)

            # Process surprises
            for surprise in floor_bp.surprises:
                if surprise.location:
                    surprise_tiles = get_region_tiles(
                        surprise.location, rooms, floor_tiles, floor_bp.regions
                    )
                else:
                    surprise_tiles = floor_tiles

                if surprise.type == "guardian" and surprise.guardian_tier:
                    # Place guardian monster
                    from tools.map_generator.entity_placer import get_monster_for_tier
                    guardian_id = get_monster_for_tier(surprise.guardian_tier)
                    placer.place_in_region("monster", guardian_id, surprise_tiles)

                    # Place rewards
                    if surprise.reward:
                        for reward_id in surprise.reward:
                            placer.place_in_region("item", reward_id, surprise_tiles)

                elif surprise.type == "trap":
                    # Place a trap monster (use tier 2-3 for traps)
                    from tools.map_generator.entity_placer import get_monster_for_tier
                    import random
                    trap_tier = random.randint(2, 3)
                    trap_monster = get_monster_for_tier(trap_tier)
                    placer.place_in_region("monster", trap_monster, surprise_tiles)

            # Place stairs
            stairs_up = None
            stairs_down = None
            if floor_bp.floor > 1 and rooms:
                # Place stairs up in first room
                stairs_up = rooms[0].center
            if floor_bp.floor < 21 and len(rooms) > 1:
                # Place stairs down in last room
                stairs_down = rooms[-1].center

            # Create output
            output = MapOutput(
                level=floor_bp.floor,
                name=floor_bp.name,
                name_cn=f"第{floor_bp.floor}层",
                tiles=tiles,
                player_start=start_pos,
            )

            # Add all entities
            for entity in placer.get_all_entities():
                output.add_entity(entity.type, entity.id, entity.x, entity.y, entity.data)

            if stairs_up:
                output.set_stairs_up(stairs_up)
            if stairs_down:
                output.set_stairs_down(stairs_down)

            maps.append(output.to_dict())

        return maps

    def generate_and_save(self, blueprint_data: dict, output_dir: str) -> list[str]:
        maps = self.generate(blueprint_data)
        saved_files = []
        for map_data in maps:
            output = MapOutput(
                level=map_data["level"],
                name=map_data["name"],
                name_cn=map_data["name_cn"],
                tiles=map_data["tiles"],
                player_start=tuple(map_data["player_start"]),
                entities=map_data["entities"],
            )
            filepath = output.save(output_dir)
            saved_files.append(filepath)
        return saved_files


def main():
    parser = argparse.ArgumentParser(description="Generate Magic Tower maps")
    parser.add_argument("--blueprint", "-b", required=True, help="Path to blueprint JSON file")
    parser.add_argument("--output", "-o", default="data/maps", help="Output directory")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Random seed")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    try:
        blueprint = load_blueprint(args.blueprint)
        if args.verbose:
            print(f"Loaded blueprint: group {blueprint.group}, floors {blueprint.floors_range}")
        with open(args.blueprint, "r", encoding="utf-8") as f:
            blueprint_data = json.load(f)
        generator = MapGenerator(seed=args.seed)
        files = generator.generate_and_save(blueprint_data, output_dir=args.output)
        print(f"Generated {len(files)} map(s):")
        for f in files:
            print(f"  - {f}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
