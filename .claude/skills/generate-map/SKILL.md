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
- **Floor templates**: `.claude/skills/generate-map/templates/` (floors_1-5.json, etc.)
- **Blueprint output**: `.temp/blueprint_*.json` (temporary working directory)

## Supported Features

The generator automatically handles:

| Feature | Description |
|---------|-------------|
| Room layout | Generates connected rooms with passages |
| Monster placement | Places monsters by tier in regions |
| Item placement | Distributes items across regions |
| Door placement | Places doors based on `unlock_sequence` |
| Key placement | Places keys in accessible regions |
| Shop placement | Places shops in specified regions |
| Surprise mechanics | Places guardians with rewards, traps |
| Stairs | Auto-places stairs up/down between floors |
| Connectivity | Ensures all rooms are connected |

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

Create a blueprint JSON file describing the map intent.

## CRITICAL REQUIREMENTS

### Requirement 1: 7-9 Regions Per Floor

Each floor MUST have 7-9 regions to create meaningful exploration while ensuring generator can place all doors.

**Region distribution pattern:**
- 1 entrance region (player spawn)
- 3-4 pathway regions (main exploration areas with monsters)
- 2-3 treasure regions (locked areas with rewards)
- 1 challenge region (optional difficult area with high rewards)

**IMPORTANT:** Do NOT exceed 9 regions or 8 doors per floor, as the generator cannot place more doors than available passage points.

### Requirement 2: Door-Region Balance

**Generator Limitation:** LayoutBuilder typically generates 5-8 passage points per floor.

**Safe limits:**
- **Optimal**: 6-7 regions with 5-6 doors
- **Maximum**: 9 regions with 7-8 doors (risky - may not all place)
- **Avoid**: >9 regions or >8 doors (generator cannot place all)

**Door placement rules:**
- Every pathway region after entrance requires a door
- Every treasure region requires a door (locked by key)
- Challenge regions require a door
- The unlock_sequence MUST have one entry per door
- **CRITICAL:** Keep unlock_sequence entries ≤ available passage points (typically 5-8)

**Example for 7 regions:**
- 1 door from entrance to pathway_1
- 1 door from entrance to pathway_2
- 1 door from pathway_2 to pathway_3
- 1 door from pathway_2 to treasure_1
- 1 door from pathway_3 to treasure_2
- 1 door from treasure_1 to challenge_room
- (Total: 6 doors - generator can handle this)

### Requirement 3: Surprise Elements Required

Every floor MUST include at least 2 surprise elements. Surprise types:

| Type | Description | Example |
|------|-------------|---------|
| `guardian` | Strong monster guarding valuable loot | Guardian tier 3 protecting a sword upgrade |
| `trap` | Hidden dangerous monster | Tier 2-3 monster that appears unexpectedly |
| `surprise_shop` | Unexpected merchant in remote area | Shop in a treasure room |

**Surprise distribution per floor:**
- Floors 1-5: At least 1 guardian + 1 trap
- Floors 6-10: At least 2 guardians + 1 trap
- Floors 11-15: At least 2 guardians + 2 traps
- Floors 16-21: At least 3 guardians + 2 traps

### Requirement 4: Key-Door Reachability (CRITICAL - Prevents Deadlocks)

**The Golden Rule:** Every key MUST be obtainable BEFORE the player needs it to open a door.

**Why this matters:** If a player spawns in an area that requires 2 keys to exit, but only has 1 key available in that area, they are deadlocked and cannot progress.

### Requirement 5: Key Economy Balance (CRITICAL - Maintains Strategy)

**Balance Rule:** Keys should be **just enough** to progress, not abundant. This maintains strategic decision-making.

**Target ratios:**
- **Minimum**: Keys ≥ Doors (prevent deadlock)
- **Optimal**: Keys = Doors + 1~2 (slight surplus for exploration)
- **Maximum**: Keys ≤ Doors × 1.3 (avoid trivializing puzzles)

**Example for 8 doors:**
- ✓ Good: 9-10 keys total (1.1-1.25 ratio)
- ✗ Bad: 17 keys for 5 doors (3.4 ratio - no strategy)
- ✗ Bad: 4 keys for 8 doors (0.5 ratio - deadlock)

**Key placement strategy:**
1. **Exact placement**: Each unlock_sequence entry places exactly 1 key
2. **No bonus keys**: Don't add extra keys beyond unlock_sequence requirements
3. **Challenge-reward**: Some keys require defeating monsters to reach

**Implementation:**
```json
// CORRECT: 8 doors, 8 keys (1:1 ratio)
{
  "unlock_sequence": [
    {"door": "yellow", "key_at": "entrance", "target_region": "hall_1"},
    // ... 7 more entries
  ]
  // Total keys: 8 (exactly one per door)
}

// WRONG: Too many keys
{
  "regions": [
    {"id": "entrance", "content": {"items": ["yellow_key", "yellow_key", "yellow_key"]}},
    // Excess keys remove strategy
  ]
}
```

#### Linear Unlock Sequence Pattern

Design unlock_sequence following a **linear progression** where each door's key is placed in an already-accessible region:

```
entrance (no door needed)
  ↓ [yellow door 1]
corridor_1 (has yellow_key_1)
  ↓ [yellow door 2]
corridor_2 (has blue_key)
  ↓ [blue door]
treasure_room
```

**Correct Example:**
```json
{
  "regions": [
    {"id": "entrance", "type": "entrance"},
    {"id": "corridor_1", "type": "pathway"},
    {"id": "corridor_2", "type": "pathway"}
  ],
  "unlock_sequence": [
    {
      "floor": 1,
      "door": "yellow",
      "key_at": "entrance",          // ✓ Key in starting area
      "target_region": "corridor_1"
    },
    {
      "floor": 1,
      "door": "yellow",
      "key_at": "corridor_1",        // ✓ Key in area unlocked by first door
      "target_region": "corridor_2"
    }
  ]
}
```

**INCORRECT Example (Deadlock):**
```json
{
  "regions": [
    {"id": "entrance", "type": "entrance"},  // Player spawns here
    {"id": "corridor_1", "type": "pathway"},
    {"id": "corridor_2", "type": "pathway"}
  ],
  "unlock_sequence": [
    {
      "floor": 1,
      "door": "yellow",
      "key_at": "corridor_1",        // ✗ Key BEHIND the door it opens!
      "target_region": "corridor_1"  // ✗ DEADLOCK: player can't reach key
    }
  ]
}
```

#### Validation Rules

When designing unlock_sequence, verify:

1. **First door rule:** The first door in the sequence MUST have its key in the `entrance` region
2. **Chain rule:** Each subsequent door's key MUST be in a region accessible by all previous doors
3. **No circular dependencies:** Never place a key behind the door it opens

#### Reachability Verification Algorithm

Before finalizing blueprint, mentally trace player progression:

```python
reachable_regions = {entrance}
available_keys = {}

for step in unlock_sequence:
    # Check: is key_at region reachable?
    if step.key_at not in reachable_regions:
        ERROR: "Deadlock detected - key not reachable"

    # Player obtains key
    available_keys[step.door_color] += 1

    # Player uses key to open door
    if available_keys[step.door_color] <= 0:
        ERROR: "Not enough keys"

    # New region becomes accessible
    reachable_regions.add(step.target_region)
```

#### Entrance Region Rules

The `entrance` region MUST:
- Be the player spawn point (no doors blocking access)
- Contain keys for the first set of doors
- NOT have any `access.requires` field (it's always accessible)

**Example:**
```json
{
  "regions": [
    {
      "id": "entrance",
      "type": "entrance"
      // NO access.requires - always accessible
    },
    {
      "id": "main_hall",
      "type": "pathway",
      "access": {"requires": "yellow_key"}  // Requires key
    }
  ],
  "unlock_sequence": [
    {
      "floor": 1,
      "door": "yellow",
      "key_at": "entrance",  // Key in spawn area
      "target_region": "main_hall"
    }
  ]
}
```

## Blueprint Format

**IMPORTANT:** The unlock_sequence MUST follow linear progression - each door's key must be obtainable in an already-accessible region.

```json
{
  "group": 1,
  "floors_range": [1, 1],
  "difficulty_tier": "easy",
  "global_theme": "Introduction to the Tower",
  "floors": [
    {
      "floor": 1,
      "name": "Tower Entrance",
      "layout": {"pattern": "simple_rooms", "room_count": 9},
      "regions": [
        {"id": "entrance", "type": "entrance", "content": {"items": ["yellow_key"]}},
        {"id": "hall_1", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 2}}},
        {"id": "hall_2", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 2}, "items": ["yellow_key"]}},
        {"id": "hall_3", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 3}}},
        {"id": "hall_4", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 2}, "items": ["blue_key"]}},
        {"id": "side_room", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 2}}},
        {"id": "vault_1", "type": "treasure", "access": {"requires": "yellow_key"}, "content": {"items": ["red_gem", "red_potion"]}},
        {"id": "vault_2", "type": "treasure", "access": {"requires": "blue_key"}, "content": {"items": ["sword_1", "blue_gem"]}},
        {"id": "challenge", "type": "boss", "access": {"requires": "yellow_key"}, "content": {"items": ["shield_1"]}}
      ],
      "surprises": [
        {"type": "guardian", "location": "vault_1", "guardian_tier": 2, "reward": ["red_key"]},
        {"type": "trap", "location": "hall_3"}
      ],
      "shops": [
        {"id": "potion_shop", "region": "entrance"}
      ]
    }
  ],
  "unlock_sequence": [
    {"floor": 1, "door": "yellow", "key_at": "entrance", "target_region": "hall_1"},
    {"floor": 1, "door": "yellow", "key_at": "entrance", "target_region": "hall_2"},
    {"floor": 1, "door": "yellow", "key_at": "hall_2", "target_region": "hall_3"},
    {"floor": 1, "door": "yellow", "key_at": "hall_2", "target_region": "hall_4"},
    {"floor": 1, "door": "yellow", "key_at": "hall_2", "target_region": "side_room"},
    {"floor": 1, "door": "yellow", "key_at": "hall_2", "target_region": "vault_1"},
    {"floor": 1, "door": "yellow", "key_at": "hall_2", "target_region": "challenge"},
    {"floor": 1, "door": "blue", "key_at": "hall_4", "target_region": "vault_2"}
  ]
}
```

### Blueprint Elements:

- `regions`: Minimum 9 regions with distinct purposes
- `access`: Lock regions behind specific keys
- `content`: Specify monsters (tier, count) and items for each region
- `unlock_sequence`: MUST have one entry per door (typically 8+ entries for 9 regions)
- `surprises`: MUST include at least 2 surprise elements
- `shops`: Optional, place shop NPCs in accessible regions

### Step 3: Run Python Generator

Execute the generator CLI:

```bash
python -m tools.map_generator.generator \
  --blueprint .temp/blueprint_f1-5.json \
  --output data/maps \
  --seed 42 \
  --verbose
```

**Note:** Each floor uses a unique seed derived from the base seed + floor number, ensuring variety even when generating multiple floors with the same base seed.

### Step 4: Verify Output

The generator produces complete maps with:
- Connected room layout with passages
- Monsters and items placed in regions
- Doors placed at passage points (from unlock_sequence)
- Keys placed in accessible regions
- Shops positioned in specified regions
- Surprise encounters with guardians/traps and rewards
- Stairs for multi-floor navigation

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

| Pattern | Description | Room Count | Variety |
|---------|-------------|------------|---------|
| `simple_rooms` | Non-overlapping rectangles with varied sizes | 2-5 | High - random positions and sizes |
| `cross` | Central hub + 4 directional arms | 5 | Medium - randomized center and arm lengths |
| `linear` | Horizontal progression rooms | 2-4 | Medium - varied heights and widths |
| `l_shape` | L-shaped layout with corner room | 4-5 | High - randomized arm lengths |
| `spiral` | Spiral arrangement around center | 3-6 | High - randomized spiral pattern |

### Monster Tiers

| Tier | Monsters |
|------|----------|
| 1 | slime_green, slime_red, bat |
| 2 | skeleton, ghost |
| 3 | orc, wizard |
| 4 | knight |
| 5 | dragon_baby |
| 6 | demon_lord |

### Unlock Sequence

Define door-key relationships - ONE ENTRY PER DOOR:

```json
{
  "floor": 1,
  "door": "yellow",
  "key_at": "entrance",
  "target_region": "hall_1",
  "key_count": 1
}
```

Valid door colors: `yellow`, `blue`, `red`, `green`

### Surprise Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `guardian` | Monster guarding loot | `guardian_tier`, `reward[]`, `location` |
| `trap` | Hidden dangerous monster | `location` |

### Shop Configuration

```json
{"id": "weapon_shop", "region": "entrance"}
```

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

## Complete Example: Floor 1 Blueprint

This example demonstrates all requirements: 9 regions, 8 doors (linear unlock), 2 surprises.

**Critical:** Notice how each unlock step places the key in an already-accessible region.

**Key-Door Balance:** 8 doors require exactly 8 keys (1:1 ratio), creating strategic choices.

```json
{
  "group": 1,
  "floors_range": [1, 1],
  "difficulty_tier": "easy",
  "global_theme": "Tower Entrance - First Steps",
  "floors": [
    {
      "floor": 1,
      "name": "Entrance Hall",
      "layout": {"pattern": "simple_rooms", "room_count": 9},
      "regions": [
        {"id": "entrance", "type": "entrance", "content": {"items": ["yellow_key"]}},
        {"id": "corridor_1", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 2}}},
        {"id": "corridor_2", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 2}, "items": ["yellow_key"]}},
        {"id": "corridor_3", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 3}}},
        {"id": "corridor_4", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 2}, "items": ["blue_key"]}},
        {"id": "side_chamber", "type": "pathway", "content": {"monsters": {"tier": 1, "count": 2}}},
        {"id": "treasury", "type": "treasure", "access": {"requires": "yellow_key"}, "content": {"items": ["red_gem", "red_potion"]}},
        {"id": "armory", "type": "treasure", "access": {"requires": "blue_key"}, "content": {"items": ["sword_1", "blue_gem"]}},
        {"id": "guardian_room", "type": "boss", "access": {"requires": "yellow_key"}, "content": {"items": ["shield_1", "red_key"]}}
      ],
      "surprises": [
        {"type": "guardian", "location": "guardian_room", "guardian_tier": 2, "reward": ["red_key"]},
        {"type": "trap", "location": "corridor_3"}
      ],
      "shops": [
        {"id": "potion_shop", "region": "entrance"}
      ]
    }
  ],
  "unlock_sequence": [
    {"floor": 1, "door": "yellow", "key_at": "entrance", "target_region": "corridor_1"},
    {"floor": 1, "door": "yellow", "key_at": "entrance", "target_region": "corridor_2"},
    {"floor": 1, "door": "yellow", "key_at": "corridor_2", "target_region": "corridor_3"},
    {"floor": 1, "door": "yellow", "key_at": "corridor_2", "target_region": "corridor_4"},
    {"floor": 1, "door": "yellow", "key_at": "corridor_2", "target_region": "side_chamber"},
    {"floor": 1, "door": "yellow", "key_at": "corridor_2", "target_region": "treasury"},
    {"floor": 1, "door": "blue", "key_at": "corridor_4", "target_region": "armory"},
    {"floor": 1, "door": "yellow", "key_at": "treasury", "target_region": "guardian_room"}
  ]
}
```

**Key-Door Balance Analysis:**
- **Total Doors**: 8
- **Total Keys**: 8 (1:1 ratio)
  - entrance: 1 yellow_key
  - corridor_2: 1 yellow_key
  - corridor_4: 1 blue_key
  - treasury: 1 yellow_key (from surprise reward)
- **Strategic Choices**: Player must decide which doors to open first with limited keys

**Reachability Trace:**
1. Player spawns in `entrance` → finds 1 yellow_key
2. **Choice**: Open `corridor_1` OR `corridor_2`? (only 1 key available!)
3. Opens `corridor_2` (better choice - has more keys) → finds 1 yellow_key
4. **Strategy**: Now has keys for multiple paths - must prioritize
5. Opens doors strategically based on reward priorities
```

## Playability Guidelines

- **Region Count**: Minimum 9 regions per floor for meaningful exploration
- **Door Coverage**: Every region transition must have a door
- **Surprise Elements**: Include guardians and traps for engagement
- **Difficulty Scaling**: Use appropriate monster tiers for floor group
- **Economy**: Keys >= doors (slight surplus allows exploration)
- **Risk/Reward**: High-tier monsters guard valuable items
- **Connectivity**: All areas must be reachable after unlocking doors
- **Progression**: Use unlock_sequence to create meaningful exploration flow
