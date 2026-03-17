---
name: generate-map
description: |
  Generate or regenerate Magic Tower game maps with valid layout and playability.
  Use this skill whenever the user wants to create new maps, regenerate existing maps,
  or fix map design issues. Triggers on phrases like "generate floor X", "regenerate maps",
  "create new floor", "fix floor X map", "redesign floor", "rebuild maps 1-5", etc.
---

# Map Generation Skill (Hybrid AI + Python)

Generate valid and playable maps for Magic Tower RPG game using a hybrid approach:
1. **AI designs the blueprint** (declarative intent)
2. **Python generates the map** (guaranteed correctness)

## When to Use This Skill

- User requests to generate/regenerate specific floors (e.g., "regenerate floor 1-3")
- User asks to create a new map for specific floor (e.g., "create floor 5 map")
- User wants to fix map design issues
- User mentions "map generation" or "redesign map"

## Project Context

- **Map files**: `data/maps/floor_XX.json` (21 floors total)
- **Entity configs**: `data/entities/` (items.json, monsters.json, shops.json)
- **Map dimensions**: 25 (width) x 19 (height) tiles
- **Generator tool**: `tools/map_generator/generator.py`

## Hybrid Workflow

### Step 1: Determine Floor Group

Identify which floor group to generate:

| Group | Floors | Difficulty | Template |
|-------|--------|------------|----------|
| 1 | F1-5 | Easy | `floors_1-5.json` |
| 2 | F6-10 | Normal | `floors_6-10.json` |
| 3 | F11-15 | Hard | `floors_11-15.json` |
| 4 | F16-21 | Expert | `floors_16-21.json` |

### Step 2: Design Blueprint (AI Task)

Create a blueprint JSON file describing the map intent:

```json
{
  "group": 1,
  "floors_range": [1, 5],
  "difficulty_tier": "easy",
  "global_theme": "Introduction to the Tower",
  "floors": [
    {
      "floor": 1,
      "name": "Tower Entrance",
      "layout": {"pattern": "simple_rooms", "room_count": 3},
      "regions": [
        {"id": "start", "type": "entrance"},
        {"id": "main", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 3}}},
        {"id": "vault", "type": "treasure", "access": {"requires": "yellow_key"}, "content": {"items": ["red_gem"]}}
      ],
      "surprises": []
    }
  ],
  "unlock_sequence": [
    {"floor": 1, "door": "yellow", "key_at": "start", "target_region": "vault"}
  ]
}
```

**Blueprint Elements:**
- `regions`: Define areas with purpose (entrance, pathway, treasure, boss)
- `access`: Lock regions behind keys/requirements
- `content`: Specify monsters (tier, count) and items
- `unlock_sequence`: Define the order players unlock doors

### Step 3: Run Python Generator

Execute the generator CLI:

```bash
python -m tools.map_generator.generator \
  --blueprint .temp/blueprint_f1-5.json \
  --output data/maps \
  --seed 42 \
  --verbose
```

### Step 4: Verify Output

The generator guarantees:
- All regions are reachable (connectivity tracking)
- Entities placed on valid floor tiles
- Door-key balance maintained
- Stairs correctly placed

## Blueprint Reference

### Region Types

| Type | Purpose | Content |
|------|---------|---------|
| `entrance` | Player spawn point | None |
| `pathway` | Standard exploration | Monsters, items |
| `treasure` | Reward areas | Items, gems |
| `boss` | Guardian encounters | High-tier monster + loot |
| `secret` | Hidden areas | Rare items |

### Layout Patterns

| Pattern | Description | Room Count |
|---------|-------------|------------|
| `simple_rooms` | Non-overlapping rectangles | 2-5 |
| `cross` | Central hub + 4 branches | 5 |
| `linear` | Horizontal progression | 2-4 |

### Monster Tiers

| Tier | Monsters |
|------|----------|
| 1 | slime_green, slime_red, bat |
| 2 | skeleton, ghost |
| 3 | orc, wizard |
| 4 | knight |
| 5 | dragon_baby |
| 6 | demon_lord |

## Tile Type IDs

| ID | Type | Description |
|----|------|-------------|
| 1 | FLOOR | Walkable ground |
| 2 | WALL | Impassable wall |
| 20 | STAIRS_DOWN | Stairs going down |
| 21 | STAIRS_UP | Stairs going up |

## Entity Format

```json
{"type": "monster", "id": "<monster_id>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "item", "id": "<item_id>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "door", "id": "<color>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "shop", "id": "<shop_id>", "x": <0-24>, "y": <0-18>, "data": {}}
```

## Example Usage

### Generate Floors 1-5

```bash
# 1. Design blueprint (AI creates this)
cat > .temp/blueprint_f1-5.json << 'EOF'
{
  "group": 1,
  "floors_range": [1, 5],
  "difficulty_tier": "easy",
  "global_theme": "Introduction",
  "floors": [
    {
      "floor": 1,
      "name": "Entrance Hall",
      "layout": {"pattern": "simple_rooms", "room_count": 3},
      "regions": [
        {"id": "start", "type": "entrance"},
        {"id": "main", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 3}, "items": ["yellow_key"]}}
      ],
      "surprises": []
    }
  ],
  "unlock_sequence": []
}
EOF

# 2. Run generator
python -m tools.map_generator.generator -b .temp/blueprint_f1-5.json -o data/maps -v

# 3. Verify
ls -la data/maps/floor_01.json
```

## Playability Guidelines

- **Difficulty Scaling**: Use appropriate monster tiers for floor group
- **Economy**: Keys >= doors (slight surplus allows exploration)
- **Risk/Reward**: High-tier monsters guard valuable items
- **Connectivity**: All areas must be reachable after unlocking doors
