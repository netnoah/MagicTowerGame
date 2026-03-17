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
        for floor_bp in blueprint.floors:
            builder = LayoutBuilder(width=self.width, height=self.height, seed=self.seed)
            rooms = builder.generate_rooms(
                pattern=floor_bp.layout.pattern,
                count=floor_bp.layout.room_count,
            )
            builder.carve_rooms(rooms)
            tiles = builder.get_tiles()
            floor_tiles = builder.get_floor_tiles()
            if not floor_tiles:
                continue
            start_pos = list(floor_tiles)[0]
            placer = EntityPlacer(floor_tiles, seed=self.seed)
            for region in floor_bp.regions:
                region_tiles = {t for t in floor_tiles if t}
                if region.content:
                    if region.content.monsters:
                        tier = region.content.monsters.get("tier", 1)
                        count = region.content.monsters.get("count", 1)
                        placer.place_monsters_by_tier(tier, count, region_tiles)
                    if region.content.items:
                        for item_id in region.content.items:
                            placer.place_in_region("item", item_id, region_tiles)
            stairs_up = None
            stairs_down = None
            if floor_bp.floor > 1:
                stairs_up = start_pos
            if floor_bp.floor < 21:
                stairs_down = list(floor_tiles)[-1] if len(floor_tiles) > 1 else None
            output = MapOutput(
                level=floor_bp.floor,
                name=floor_bp.name,
                name_cn=f"第{floor_bp.floor}层",
                tiles=tiles,
                player_start=start_pos,
            )
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
