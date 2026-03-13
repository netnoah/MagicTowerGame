# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Classic Magic Tower RPG game built with Python + Pygame. Players explore 21 floors, battle monsters, collect keys/items, and defeat the final boss.

## Development Commands

```bash
# Run the game
python main.py

# Run tests
pytest                                    # All tests
pytest test_items.py -v                   # Specific test file
pytest --cov=. --cov-report=term-missing  # With coverage

# Install dependencies
pip install -r requirements.txt
```

## Architecture

```
main.py                 # Entry point → creates Game instance
config.py               # Centralized frozen dataclasses for all config

engine/                 # Core game loop
├── game.py             # Main Game class, orchestrates all systems
├── display.py          # Window management and rendering
├── input.py            # Input handling with key bindings
└── state_machine.py    # Game state transitions (MENU/PLAYING/SHOP/PAUSED)

entities/               # Game objects
├── player.py           # Player stats, movement, animations
└── monster.py          # Monster entities with MonsterManager

systems/                # Game logic modules
├── floor_manager.py    # Map loading, tile collision, entity placement
├── tile.py             # TileType enum and tile rendering
├── combat.py           # Turn-based combat calculations
├── items.py            # Item effects, ItemManager for JSON loading
├── shop.py             # Shop data and transaction logic
├── resource_loader.py  # Sprite loading with auto-rotation for 4 directions
└── animation.py        # Animation playback system

ui/                     # Interface components
├── hud.py              # Left panel showing stats/keys/gold
├── menu.py             # Main menu, pause menu, game over
├── shop_ui.py          # Shop interface
└── base.py             # UI component primitives (Panel, Label, etc.)

data/
├── maps/floor_*.json   # 21 floor maps (tile layer + entities layer)
└── entities/           # items.json, monsters.json, shops.json
```

## Key Technical Details

- **Resolution**: 1120x608 (HUD 160px + Map 800px + margin 160px)
- **Tile size**: 32x32 pixels, Map: 25x19 tiles
- **Sprites**: Auto-rotated from RIGHT-facing source (0°, 90°, 180°, 270°)
- **Combat formula**: `damage = max(1, attacker_attack - defender_defense)`
- **State machine**: MENU → PLAYING ↔ SHOP/PAUSED → GAME_OVER/VICTORY

## Control Scheme

Avoid a-z letter keys (conflicts with Chinese IME):
- **Movement**: Arrow keys
- **Confirm/Interact**: Enter / Space
- **Pause**: ESC
- **Monster info panel**: Left Ctrl

## Coding Standards

- **Immutability**: Create new objects, never mutate existing ones (use frozen dataclasses)
- **Test coverage**: Target 80%+
- **File size**: Keep under 800 lines
- **Function size**: Keep under 50 lines

## Related Documentation

- Detailed planning: `PROJECT_PLAN.md`
- Task tracking: `TODO.md`
