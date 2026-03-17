"""Template system for map generation."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FloorTemplate:
    group_name: str
    floors_range: tuple[int, int]
    difficulty: dict = field(default_factory=lambda: {
        "monster_tier_base": 1,
        "monster_tier_variance": 1,
    })
    layout: dict = field(default_factory=lambda: {
        "patterns": ["simple_rooms"],
        "room_count_range": [2, 4],
    })
    doors: dict = field(default_factory=lambda: {
        "colors": ["yellow"],
        "max_per_floor": 2,
    })
    surprises: dict = field(default_factory=lambda: {
        "guardian_chance": 0.3,
        "trap_chance": 0.2,
    })
    rewards: dict = field(default_factory=lambda: {
        "common": ["yellow_key", "red_potion"],
        "rare": [],
        "legendary": [],
    })

    @classmethod
    def from_dict(cls, data: dict) -> "FloorTemplate":
        floors_range = tuple(data.get("floors_range", [1, 1]))
        return cls(
            group_name=data.get("group_name", "Unknown"),
            floors_range=floors_range,  # type: ignore
            difficulty=data.get("difficulty", {}),
            layout=data.get("layout", {}),
            doors=data.get("doors", {}),
            surprises=data.get("surprises", {}),
            rewards=data.get("rewards", {}),
        )

    def get_monster_tier(self, floor: int) -> int:
        base = self.difficulty.get("monster_tier_base", 1)
        variance = self.difficulty.get("monster_tier_variance", 0)
        range_size = self.floors_range[1] - self.floors_range[0] + 1
        if range_size > 0:
            progress = (floor - self.floors_range[0]) / range_size
        else:
            progress = 0
        return base + int(progress * variance)

    def get_available_door_colors(self) -> list[str]:
        return self.doors.get("colors", ["yellow"])

    def get_max_doors_per_floor(self) -> int:
        return self.doors.get("max_per_floor", 2)


class TemplateLoader:
    DEFAULT_TEMPLATE = FloorTemplate(
        group_name="Default",
        floors_range=(1, 21),
        difficulty={"monster_tier_base": 1},
    )

    def __init__(self, template_dir: Optional[str] = None):
        self._templates: dict[str, FloorTemplate] = {}
        if template_dir:
            self._load_templates(template_dir)

    def _load_templates(self, template_dir: str):
        template_path = Path(template_dir)
        if not template_path.exists():
            return
        for filepath in template_path.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                template = FloorTemplate.from_dict(data)
                self._templates[filepath.name] = template
            except (json.JSONDecodeError, KeyError):
                continue

    def get_for_floor(self, floor: int) -> FloorTemplate:
        for template in self._templates.values():
            if template.floors_range[0] <= floor <= template.floors_range[1]:
                return template
        return self.DEFAULT_TEMPLATE
