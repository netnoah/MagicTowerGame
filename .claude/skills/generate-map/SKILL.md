---
name: generate-map
description: |
  Generate or regenerate Magic Tower game maps with valid layout and playability.
  Use this skill whenever the user wants to create new maps, regenerate existing maps,
  or fix map design issues. Triggers on phrases like "generate floor X", "regenerate maps",
  "create new floor", "fix floor X map", "redesign floor", "rebuild maps 1-5", etc.
---

# Map Generation Skill

Generate valid and playable maps for Magic Tower RPG game.

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

### Step 0: Read User Request

Determine which floors to generate:
- "前三层" or "floor 1-3" → Generate floor_01.json, floor_02.json, floor_03.json
- "第五层" or "floor 5" → Generate floor_05.json
- "所有地图" or "all floors" → Generate all 21 floors

### Step 1: Read Entity Configurations

Before generating, read these files:
1. `data/entities/items.json` - Available items (keys, potions, gems, equipment)
2. `data/entities/monsters.json` - Available monsters with stats
3. `data/entities/shops.json` - Available shop types

### Step 2: Plan Map Blocking (墙体规划)

创建墙体布局，把地图分成多个不连通的区域：

**核心思想：** 先规划"阻隔"，后规划"连接"

1. **基础布局**：使用对称布局创建房间结构
   - 外围全部是墙(2)
   - 内部用墙分隔成多个房间/区域
   - 早期楼层(F1-7)：简单对称布局
   - 中期楼层(F8-17)：更复杂的迷宫
   - 后期楼层(F18-21)：复杂的多分支结构

2. **区域识别**：使用flood-fill识别所有不连通区域
   ```python
   def get_regions(tiles):
       """返回所有不连通的区域列表，每个区域是一组坐标"""
       regions = []
       visited = set()
       for y in range(height):
           for x in range(width):
               if tiles[y][x] == 1 and (x,y) not in visited:
                   # 新发现一个区域，用flood-fill找到所有可达位置
                   region = flood_fill(tiles, x, y)
                   regions.append(region)
                   visited.update(region)
       return regions
   ```

3. **区域数量目标**：
   - F1-3: 3-5个区域
   - F4-7: 4-6个区域
   - F8-12: 5-8个区域
   - F13-21: 6-10个区域

### Step 3: Initial Region Incentives (区域激励)

**目的：** 在每个不连通区域放置至少一个"有吸引力"的东西，给玩家探索的动力。

对每个区域：
1. **选择区域类型**（决定放什么）：
   - 包含player_start的区域：放楼梯（F1放STAIRS_UP，F20-21放STAIRS_DOWN和STAIRS_UP，F21放STAIRS_DOWN）
   - 其他区域：选择放钥匙、宝石、装备、商店
   - 随机分布，确保多样性

2. **放置到区域内的FLOOR位置**：
   ```python
   for region in regions:
       if player_start in region:
           # 这是起始区域，放置楼梯
           place_stairs_in_region(region)
       else:
           # 其他区域，放置有价值的物品
           place_incentive_in_region(region)
   ```

3. **放置规则**：
   - 物品必须放在 tiles[y][x] == 1 的位置
   - 每个tile最多一个实体
   - 钥匙：根据楼层难度选择颜色（早期黄钥匙为主）
   - 宝石/装备：根据区域大小决定数量

### Step 4: Door Connection Logic (门连接逻辑) - **核心步骤!**

**目的：** 通过门连接所有不连通区域，每个门必须连接两个之前不连通的区域。

**算法：**

```
while len(regions) > 1:
    # 1. 找到一个可以连接两个区域的墙位置
    best_door_pos = None
    best_connection = None
    max_regions_joined = 0

    for y in range(height):
        for x in range(width):
            if tiles[y][x] == 2:  # 这是一个墙
                # 测试：如果把这个墙改成FLOOR+放门，会连接多少个区域
                tiles[y][x] = 1  # 临时改成FLOOR
                regions_after = get_regions(tiles)  # 重新计算区域
                tiles[y][x] = 2  # 改回墙

                # 计算减少的区域数量
                regions_joined = len(regions) - len(regions_after)

                if regions_joined > max_regions_joined:
                    max_regions_joined = regions_joined
                    best_door_pos = (x, y)
                    best_connection = regions_after

    if best_door_pos is None:
        # 找不到有效的门位置，生成失败
        raise Exception("无法连接所有区域")

    # 2. 放置门
    x, y = best_door_pos
    tiles[y][x] = 1  # 先改成FLOOR
    entities.append({
        "type": "door",
        "id": choose_door_color(floor_level),
        "x": x,
        "y": y,
        "data": {}
    })

    # 3. 更新区域列表
    regions = best_connection
```

**门的选择逻辑：**
- 优先选择能连接最多区域的墙位置
- 这样可以用最少的门连接所有区域
- 避免放置"无意义"的门

**钥匙颜色选择：**
- F1-5: 主要是黄色门
- F6-10: 黄色+蓝色门
- F11-15: 黄+蓝+红色门
- F16-21: 所有颜色

### Step 5: Supplemental Placement (补充放置)

在确保连通后，添加更多内容：

1. **怪物放置**：
   - 根据区域大小和楼层难度决定数量
   - 低难度：每个区域1-2个怪物
   - 中难度：每个区域2-4个怪物
   - 高难度：每个区域3-6个怪物

2. **补充物品**：
   - 药水：均匀分布
   - 额外的钥匙/宝石：根据门的需求平衡

### Step 6: Final Validation (最终验证)

运行Python验证脚本确保一切正确：

```python
import json
from collections import deque

def flood_fill(tiles, start_x, start_y, blocked_positions=set()):
    """Returns set of reachable positions from start"""
    height, width = len(tiles), len(tiles[0])
    visited = set()
    queue = deque([(start_x, start_y)])

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or (x, y) in blocked_positions:
            continue
        if 0 <= x < width and 0 <= y < height and tiles[y][x] != 2:
            visited.add((x, y))
            queue.extend([(x+1,y), (x-1,y), (x,y+1), (x,y-1)])
    return visited

def get_regions(tiles):
    """Returns all disconnected regions"""
    height, width = len(tiles), len(tiles[0])
    regions = []
    visited = set()

    for y in range(height):
        for x in range(width):
            if tiles[y][x] == 1 and (x, y) not in visited:
                region = flood_fill(tiles, x, y)
                regions.append(region)
                visited.update(region)
    return regions

# 读取地图
with open('data/maps/floor_XX.json', encoding='utf-8') as f:
    data = json.load(f)

# CHECK 1: Entity-Floor Collision
print("CHECK 1: Entity-Floor Collision")
all_pass = True
for e in data['entities']:
    x, y = e['x'], e['y']
    if tiles[y][x] != 1:
        print(f"FAIL: {e['type']} {e['id']} at ({x},{y}) is not on FLOOR")
        all_pass = False

# CHECK 2: All Regions Connected (after doors opened)
print("\nCHECK 2: All Regions Connected (doors open)")
door_positions = {(e['x'], e['y']) for e in data['entities'] if e['type'] == 'door'}
blocked_without_doors = {(e['x'], e['y']) for e in data['entities']}
reachable = flood_fill(data['tiles'], data['player_start'][0], data['player_start'][1], blocked_without_doors)
floor_tiles = set((x, y) for y in range(len(data['tiles'])) for x in range(len(data['tiles'][0])) if data['tiles'][y][x] == 1)

if reachable == floor_tiles:
    print("PASS: All floor tiles are reachable when doors are open")
else:
    print(f"FAIL: {len(floor_tiles - reachable)} floor tiles are unreachable")

# CHECK 3: Stair Validity
print("\nCHECK 3: Stair Validity")
stairs_down = stairs_up = False
for y in range(len(data['tiles'])):
    for x in range(len(data['tiles'][0])):
        if data['tiles'][y][x] == 20:
            stairs_down = True
        if data['tiles'][y][x] == 21:
            stairs_up = True

level = data['level']
if level == 1:
    if stairs_down:
        print("FAIL: Floor 1 should NOT have stairs_down")
elif level == 21:
    if stairs_up:
        print("FAIL: Floor 21 should NOT have stairs_up")
else:
    if stairs_down and stairs_up:
        print("PASS: Floor has both stairs")
    else:
        print("FAIL: Floor must have both STAIRS_DOWN and STAIRS_UP")

# CHECK 4: Key-Door Balance
print("\nCHECK 4: Key-Door Balance")
door_counts = {"yellow": 0, "blue": 0, "red": 0, "green": 0}
key_counts = {"yellow": 0, "blue": 0, "red": 0, "green": 0}

for e in data['entities']:
    if e['type'] == 'door':
        door_counts[e['id']] += 1
    elif e['type'] == 'item' and e['id'].endswith('_key'):
        color = e['id'].split('_')[0]
        key_counts[color] += 1

for color in door_counts:
    if key_counts[color] < door_counts[color]:
        print(f"FAIL: {color} keys ({key_counts[color]}) < {color} doors ({door_counts[color]})")
        all_pass = False
    else:
        print(f"INFO: {color} keys ({key_counts[color]}) >= {color} doors ({door_counts[color]})")

print(f"\n=== SUMMARY ===")
if all_pass:
    print("ALL CHECKS PASSED - Map is valid!")
else:
    print("SOME CHECKS FAILED")
```

## Tile Type IDs

| ID | Type | Description |
|----|------|-------------|
| 1 | FLOOR | Walkable ground |
| 2 | WALL | Impassable wall |
| 20 | STAIRS_DOWN | Stairs going down (to next floor) |
| 21 | STAIRS_UP | Stairs going up (from previous floor) |

## Entity Format

```json
{"type": "monster", "id": "<monster_id>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "item", "id": "<item_id>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "door", "id": "<color>", "x": <0-24>, "y": <0-18>, "data": {}}
{"type": "shop", "id": "<shop_id>", "x": <0-24>, "y": <0-18>, "data": {}}
```

## Playability Guidelines

- **Difficulty Scaling**: 根据楼层选择怪物类型
- **Economy**: 钥匙总数应接近或略少于门总数（迫使玩家做选择）
- **Risk/Reward**: 高属性怪物应守护高价值物品

## Output Format

After generation, report:
```
Generated maps: floor_01.json, floor_02.json, floor_03.json
All validation checks passed.
```
