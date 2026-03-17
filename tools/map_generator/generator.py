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
            builder = LayoutBuilder(width=self.width, height=self.height, seed=self.seed)
            rooms = builder.generate_rooms(
                pattern=floor_bp.layout.pattern,
                count=floor_bp.layout.room_count,
            )
            builder.carve_rooms(rooms)

            # Connect rooms with passages
            builder.connect_rooms(rooms)

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

            # Track which regions have been processed for key placement
            accessible_regions: set[str] = set()

            # Process unlock_sequence for this floor
            floor_unlock_steps = [
                step for step in blueprint.unlock_sequence
                if step.floor == floor_bp.floor
            ]

            # First pass: place content in regions without access requirements
            for region in floor_bp.regions:
                region_tiles = get_region_tiles(
                    region.id, rooms, floor_tiles, floor_bp.regions
                )

                # Mark entrance as accessible
                if region.type == "entrance":
                    accessible_regions.add(region.id)

                # Skip regions with access requirements for now
                if region.access and region.access.requires:
                    continue

                accessible_regions.add(region.id)

                if region.content:
                    if region.content.monsters:
                        tier = region.content.monsters.get("tier", 1)
                        count = region.content.monsters.get("count", 1)
                        placer.place_monsters_by_tier(tier, count, region_tiles)
                    if region.content.items:
                        for item_id in region.content.items:
                            placer.place_in_region("item", item_id, region_tiles)

            # Process unlock sequence: place doors and keys
            for step in floor_unlock_steps:
                # Find passage points to place door
                door_placed = False

                # Try to place door at a passage between rooms
                for i, room1 in enumerate(rooms):
                    for room2 in rooms[i+1:]:
                        passages = builder.get_passages_between_rooms(room1, room2)
                        for passage in passages:
                            if passage not in door_positions and passage in floor_tiles:
                                # Place door entity
                                placer.place_entity_at("door", f"{step.door}_door", passage)
                                door_positions.add(passage)
                                door_placed = True
                                break
                        if door_placed:
                            break
                    if door_placed:
                        break

                # If no passage found, place door at a random floor tile near room boundary
                if not door_placed and rooms:
                    for room in rooms[1:]:  # Skip first room (usually entrance)
                        boundary = builder.get_boundary_tiles(room)
                        available = boundary & floor_tiles & placer.available_positions
                        if available:
                            pos = list(available)[0]
                            placer.place_entity_at("door", f"{step.door}_door", pos)
                            door_positions.add(pos)
                            break

                # Place key in the key_at region
                key_region = step.key_at
                key_tiles = get_region_tiles(key_region, rooms, floor_tiles, floor_bp.regions)

                # Generate key item id from door color
                key_id = f"{step.door}_key"
                for _ in range(step.key_count):
                    placer.place_in_region("item", key_id, key_tiles)

            # Second pass: place content in regions with access requirements
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
