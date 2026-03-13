---
name: generate-map
description: |
  Generate or regenerate Magic Tower game maps with valid layout and playability.
  Use this skill whenever the user wants to create new maps, regenerate existing maps,
  or fix map design issues. Triggers on phrases like "generate floor X", "regenerate maps",
  "create new floor", "fix floor X map", "redesign floor", "rebuild maps 1-5", etc.
---

# Map Generation Skill

Generate valid and playable maps for the Magic Tower RPG game.

## When to Use This Skill

- User requests to generate/regenerate specific floors (e.g., "regenerate floor 1-3")
- User asks to create a new map for specific floor (e.g., "create floor 5 map")
- User wants to fix map design issues
- User mentions "map generation" or "redesign map"

## Project Context

- **Map files**: `data/maps/floor_XX.json` (21 floors total)
- **Entity configs**: `data/entities/` (items.json, monsters.json, shops.json)
- **Map dimensions**: 25 (width) x 19 (height) tiles
- **Player enters from**: upstairs position (usually near top)

## Generation Process

### Step 1: Parse User Request

Determine which floors to generate:
- "前三层" or "floor 1-3" → Generate floor_01.json, floor_02.json, floor_03.json
- "第五层" or "floor 5" → Generate floor_05.json
- "所有地图" or "all floors" → Generate all 21 floors

### Step 2: Read Entity Configurations

Before generating, read these files:
1. `data/entities/items.json` - Available items (keys, potions, gems, equipment)
2. `data/entities/monsters.json` - Available monsters with stats
3. `data/entities/shops.json` - Available shop types

### Step 3: Generate Map JSON Structure

```json
{
  "level": <floor_number>,
  "name": "Floor <N> - <English Name>",
  "name_cn": "第<N>层 - <Chinese Name>",
  "width": 25,
  "height": 19,
  "player_start": [<x>, <y>],
  "tiles": [[<2D array of tile IDs>]],
  "entities": [<array of entity objects>]
}
```

### Tile Type IDs

| ID | Type | Description |
|----|------|-------------|
| 1 | FLOOR | Walkable ground |
| 2 | WALL | Impassable wall |
| 20 | STAIRS_DOWN | Stairs going down (to next floor) |
| 21 | STAIRS_UP | Stairs going up (from previous floor) |

**Important**: Doors are NOT placed as tile values. They are placed as entities with type "door".

### Entity Format

```json
{"type": "monster", "id": "<monster_id>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "item", "id": "<item_id>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "door", "id": "<color>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "shop", "id": "<shop_id>", "x": <0-24>, "y": <0-18>, "data": {}}
```

## Validity Rules (MUST Follow)

**CRITICAL - Collision Zero Rule:**
Entities must reside on FLOOR tiles (tiles[y][x] == 1), NOT on wall tiles (2) or other unreachable tiles.
- When placing an entity at (x, y), you MUST verify tiles[y][x] == 1 BEFORE adding to entities array
- Example: To place item at x=7, y=5, check tiles[5][7] first - if it's 2 (WALL), choose different coordinates
- Strictly one entity per tile (no overlapping entities)

Graph Connectivity: Use Flood-fill from player_start. Every FLOOR tile and ENTITY must be reachable. No isolated "islands."

Stair Logic:

F1: STAIRS_DOWN only (Bottom). F21: STAIRS_UP only (Top). F2-20: Both.

Stairs must be walkable (not blocked by walls or invalid entity clusters).

Vacuum Abhorrence: Every enclosed room (behind a door) MUST contain at least one item, monster, or NPC. No empty "trap" rooms.

## Door Design Rules (CRITICAL)

**The Cut-Vertex Test (MANDATORY):**
A door must be a mandatory bridge. If the door is treated as a WALL, the area behind it MUST be unreachable.
- NO diagonal bypasses (check 4-connected neighbors)
- NO side corridors that go around the door
- Test: Replace door tile with WALL in your mind, then flood-fill from player_start - the area behind should NOT be reachable

**The Chokepoint Template (MANDATORY):**
Door must be flanked by walls: [Wall, Door, Wall] or its vertical equivalent.
- Horizontal door: tiles[y][x-1] == 2 AND tiles[y][x+1] == 2
- Vertical door: tiles[y-1][x] == 2 AND tiles[y+1][x] == 2
- NO gaps on either side of the door

**The Toll Rule:**
A door must guard a "Net-Positive" reward (Value ≥ Key cost).

**Key Sequence:**
Verify that the required key is reachable within the current flood-fill area before the door.

## Playability Rules
• Difficulty Scaling:
• Low (F1-7): Slimes, bats, skeletons. Focus on basic resource management.
• Mid (F8-17): Ghosts, orcs, wizards, knights. Focus on armor/attack trade-offs.
• High (F18-21): Dragons, Demon Lord. Focus on final power-ups.
• Economic Strategy:
• Key Scarcity: Total keys < Total doors (force player to choose paths).
• Risk/Reward: High-stat monsters must guard high-value gems or equipment.
• Layout Aesthetics:
• Use Symmetry for early floors to reduce cognitive load.
• Vary corridor widths ( to  tiles). Use -tile corridors for "gauntlets."

## MANDATORY Validation (BLOCKING - Must Pass Before Writing)

YOU MUST validate using Python code BEFORE writing any map file. If ANY check fails, FIX the map immediately.

### Validation Script Template (COPY AND RUN THIS):

```python
import json

with open('data/maps/floor_XX.json', encoding='utf-8') as f:
    data = json.load(f)

# CHECK 1: Entity-Floor Collision
for e in data['entities']:
    x, y = e['x'], e['y']
    tile = data['tiles'][y][x]
    if tile != 1:  # Must be FLOOR (1)
        print(f"ERROR: {e['type']} {e['id']} at ({x},{y}) is on tile={tile}, not FLOOR")

# CHECK 2: Door Isolation (Cut-Vertex Test)
# For each door, verify that treating it as WALL makes the area behind unreachable
# TODO: Implement flood-fill test

# CHECK 3: Stair Logic
# Floor 1: only STAIRS_DOWN(20); Floor 21: only STAIRS_UP(21); Others: both
```

### Required Checks:

1. **Entity-Floor Collision (CRITICAL)**: EVERY entity's (x,y) must have tiles[y][x] == 1
   - Run the Python script above
   - If ANY entity is on tile != 1, FIX before proceeding

2. **Door Isolation (CRITICAL)**: Each door must truly block access to area behind
   - Door must have walls on BOTH sides: tiles[y][x-1] == 2 AND tiles[y][x+1] == 2 (horizontal)
   - OR tiles[y-1][x] == 2 AND tiles[y+1][x] == 2 (vertical)
   - NO bypass paths around the door (test with flood-fill treating door as wall)

3. **Connectivity**: Flood-fill from player_start reaches all floor tiles

4. **Stair Validity**: Correct stairs for floor number

5. **Key Balance**: Count keys vs doors, ensure critical path solvable

## Example Generation Flow (MANDATORY SEQUENCE)

```
1. Read request: "regenerate floor 1-3"
2. Read entity configs from data/entities/
3. For each floor (1, 2, 3):
   a. Create tile layout (walls, floors, rooms)
   b. Place stairs (floor 1: only down; floors 2-3: both)
   c. Place doors following door rules
   d. Place keys ONLY on tiles[y][x] == 1 (FLOOR)
   e. Place monsters ONLY on tiles[y][x] == 1 (FLOOR)
   f. Place items ONLY on tiles[y][x] == 1 (FLOOR)
   g. Optionally place shops ONLY on tiles[y][x] == 1 (FLOOR)
   h. **MANDATORY: Run Python validation script (see above)**
   i. If validation FAILS, FIX the map and RE-RUN validation
   j. Do NOT proceed to next floor until current floor PASSES ALL CHECKS
4. Only write JSON files AFTER ALL floors pass validation
5. Report validation results to user
```

## Output Format

After generation, report:

```
Generated maps: floor_01.json, floor_02.json, floor_03.json
```
