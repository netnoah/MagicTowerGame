"""Data models for map generation blueprints."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RegionAccess:
    requires: str

    @classmethod
    def from_dict(cls, data: dict) -> "RegionAccess":
        return cls(requires=data["requires"])


@dataclass
class RegionContent:
    monsters: Optional[dict] = None
    items: Optional[list[str]] = None
    doors: Optional[list[str]] = None
    has_stairs: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "RegionContent":
        return cls(
            monsters=data.get("monsters"),
            items=data.get("items"),
            doors=data.get("doors"),
            has_stairs=data.get("has_stairs", False),
        )


@dataclass
class Region:
    id: str
    type: str
    access: Optional[RegionAccess] = None
    content: Optional[RegionContent] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Region":
        access = RegionAccess.from_dict(data["access"]) if "access" in data else None
        content = RegionContent.from_dict(data["content"]) if "content" in data else None
        return cls(
            id=data["id"],
            type=data["type"],
            access=access,
            content=content,
        )


@dataclass
class Surprise:
    type: str
    location: Optional[str] = None
    guardian_tier: Optional[int] = None
    reward: Optional[list[str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Surprise":
        return cls(
            type=data["type"],
            location=data.get("location"),
            guardian_tier=data.get("guardian_tier"),
            reward=data.get("reward"),
        )


@dataclass
class LayoutConfig:
    pattern: str
    room_count: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> "LayoutConfig":
        return cls(
            pattern=data["pattern"],
            room_count=data.get("room_count", 3),
        )


@dataclass
class UnlockStep:
    floor: int
    door: str
    key_at: str
    target_region: Optional[str] = None
    key_count: int = 1

    @classmethod
    def from_dict(cls, data: dict) -> "UnlockStep":
        door = data.get("door") or data.get("door_color")
        return cls(
            floor=data["floor"],
            door=door,
            key_at=data["key_at"],
            target_region=data.get("target_region"),
            key_count=data.get("key_count", 1),
        )


@dataclass
class ShopConfig:
    id: str
    region: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ShopConfig":
        return cls(
            id=data["id"],
            region=data.get("region"),
        )


@dataclass
class FloorBlueprint:
    floor: int
    name: str
    layout: LayoutConfig
    regions: list[Region]
    surprises: list[Surprise] = field(default_factory=list)
    shops: list[ShopConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "FloorBlueprint":
        layout = LayoutConfig.from_dict(data["layout"])
        regions = [Region.from_dict(r) for r in data.get("regions", [])]
        surprises = [Surprise.from_dict(s) for s in data.get("surprises", [])]
        shops = [ShopConfig.from_dict(s) for s in data.get("shops", [])]
        return cls(
            floor=data["floor"],
            name=data.get("name", f"Floor {data['floor']}"),
            layout=layout,
            regions=regions,
            surprises=surprises,
            shops=shops,
        )


@dataclass
class Blueprint:
    group: int
    floors_range: tuple[int, int]
    difficulty_tier: str
    floors: list[FloorBlueprint]
    global_theme: str = ""
    unlock_sequence: list[UnlockStep] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Blueprint":
        floors = [FloorBlueprint.from_dict(f) for f in data.get("floors", [])]
        unlock_sequence = [UnlockStep.from_dict(u) for u in data.get("unlock_sequence", [])]
        floors_range = tuple(data.get("floors_range", [1, 1]))
        return cls(
            group=data.get("group", 1),
            floors_range=floors_range,  # type: ignore
            difficulty_tier=data.get("difficulty_tier", "normal"),
            global_theme=data.get("global_theme", ""),
            floors=floors,
            unlock_sequence=unlock_sequence,
        )

    @classmethod
    def from_json_file(cls, filepath: str) -> "Blueprint":
        import json
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
