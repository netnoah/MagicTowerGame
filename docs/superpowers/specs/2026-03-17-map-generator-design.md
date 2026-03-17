# 地图生成系统改进设计

> 日期：2026-03-17
> 状态：待审批

## 概述

改进现有的地图生成Skill，实现"AI设计蓝图 + Python脚本生成"的混合方案，一步完成高质量地图生成。

## 目标

1. **提高生成效率** - 自动化脚本替代手动JSON编写
2. **保证地图质量** - 生成时保证正确性，无需事后修复
3. **保留AI设计感** - 策略性布局、难度节奏、惊喜元素

## 核心设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 工作流程 | AI先设计蓝图，脚本后生成（一步完成） | 兼顾设计感和自动化 |
| 蓝图格式 | 结构化参数，描述意图而非坐标 | AI表达方便，脚本解析清晰 |
| 难度曲线 | 总体线性，每层有波动 | 支持回头机制，增加策略深度 |
| 验证策略 | 可达性追踪法 | 生成时保证正确，无死循环 |
| 生成方式 | 按5层一组生成 | 便于整体设计，又不至于太复杂 |
| 蓝图辅助 | 模板+自由组合 | 有参考但不限制创意 |

## 文件结构

```
.claude/skills/generate-map/
├── SKILL.md              # 改进的Skill指令
├── templates/
│   ├── floors_1-5.json   # 入门区模板
│   ├── floors_6-10.json  # 探索区模板
│   ├── floors_11-15.json # 挑战区模板
│   └── floors_16-21.json # 终极区模板
└── examples/             # 完整蓝图示例

tools/map_generator/
├── generator.py          # 主入口
├── layout_builder.py     # 房间划分、墙体生成
├── connectivity.py       # 可达性追踪算法
├── entity_placer.py      # 怪物、道具、门放置
├── surprise_mechanics.py # 守门人、机关等惊喜元素
├── templates.py          # 模板加载
└── output.py             # JSON输出
```

## 数据流

```
用户请求 "生成F1-5地图"
    ↓
Skill: AI参考模板，设计蓝图JSON
    ↓
Skill: 保存蓝图到临时文件
    ↓
Skill: 运行 python generator.py --blueprint temp.json
    ↓
Python脚本: 读取蓝图 → 生成地图 → 输出到 data/maps/
    ↓
Skill: 报告完成
```

## 蓝图格式

```json
{
  "group": 1,
  "floors_range": [1, 5],
  "difficulty_tier": "easy",
  "global_theme": "入塔初探",
  "floors": [
    {
      "floor": 1,
      "name": "入口大厅",
      "layout": {
        "pattern": "simple_rooms",
        "room_count": 3
      },
      "regions": [
        {
          "id": "start",
          "type": "entrance",
          "content": {
            "monsters": {"tier": 1, "count": 2},
            "items": ["yellow_key"]
          }
        },
        {
          "id": "main",
          "type": "pathway",
          "access": {"requires": "yellow_key"},
          "content": {
            "monsters": {"tier": 1, "count": 3},
            "doors": ["yellow"],
            "has_stairs": true
          }
        }
      ],
      "surprises": [
        {
          "type": "guardian",
          "location": "side_room",
          "guardian_tier": 3,
          "reward": ["sword_2"]
        }
      ]
    }
  ],
  "unlock_sequence": [
    {"floor": 1, "door": "yellow", "key_at": "start"},
    {"floor": 3, "door": "blue", "key_at": "floor_2_main"}
  ]
}
```

### 核心字段说明

- `regions`: 区域划分和内容，用描述性位置（entrance, pathway, side_room）而非坐标
- `surprises`: 惊喜元素配置
- `unlock_sequence`: 跨层钥匙-门顺序，保证可达性

## 核心算法：可达性追踪法

### 生成流程

```
Step 1: 解析蓝图
    ↓
Step 2: 生成基础布局（墙体、房间划分）
    ↓
Step 3: 可达性追踪放置（核心）
    ├── 3.1 从起点开始，标记可达区域
    ├── 3.2 按 unlock_sequence 顺序：
    │       ├── 在当前可达区域放置钥匙
    │       ├── 放置对应颜色的门
    │       └── 更新可达区域（门后区域变为可达）
    └── 3.3 直到所有门和钥匙放置完成
    ↓
Step 4: 放置实体（怪物、道具）
    ├── 4.1 按 difficulty_tier 放置主怪物群
    ├── 4.2 按 surprises 配置放置惊喜元素
    └── 4.3 放置楼梯、商店等
    ↓
Step 5: 输出地图JSON
```

### 可达性追踪伪代码

```python
def build_unlock_sequence(blueprint):
    reachable = {start_region}

    for step in blueprint.unlock_sequence:
        # 钥匙必须放在当前可达区域
        key_region = find_region_in_reachable(step.key_at, reachable)
        place_key(step.door_color, key_region)

        # 放门，连接新区域
        door_pos = find_wall_between(reachable, step.target_region)
        place_door(step.door_color, door_pos)

        # 扩展可达区域
        reachable.add(step.target_region)

    return reachable  # 最终所有区域都可达
```

### 正确性保证

- ✅ 所有区域连通
- ✅ 钥匙在门之前可获取
- ✅ 不会出现死锁或无法到达的区域
- ✅ 无需"生成-检测-修复"循环

## 惊喜元素设计

按优先级实现：

### 1. 守门人机制（最高优先级）

在侧房间放置一个跨层强怪，挡住稀有奖励。玩家可以绕路，也可以选择挑战。

```json
{"type": "guardian", "tier": 3, "reward": ["sword_2"]}
```

### 2. 机关陷阱

拿取道具后触发效果（如刷出怪物）。

```json
{"type": "trap", "trigger": "gem_red", "effect": "spawn_skeletons"}
```

### 3. 楼层彩蛋

特殊形状的地图布局（十字形、螺旋形、心形、骷髅形）。

```json
{"type": "pattern", "name": "cross"}
```

### 4. 商人惊喜

在非预期位置放置商店。

```json
{"type": "surprise_shop"}
```

### 5. 隐藏房间

需要特殊条件才能进入的秘密区域。

```json
{"type": "hidden_room", "access": "secret"}
```

## 模板系统

### 模板结构

```json
{
  "group_name": "入门区",
  "floors_range": [1, 5],
  "difficulty": {
    "monster_tier_base": 1,
    "monster_tier_variance": 1,
    "guardian_tier_max": 3
  },
  "layout": {
    "patterns": ["simple_rooms", "cross", "linear"],
    "room_count_range": [2, 4]
  },
  "doors": {
    "colors": ["yellow"],
    "max_per_floor": 2
  },
  "surprises": {
    "guardian_chance": 0.4,
    "trap_chance": 0.2,
    "pattern_chance": 0.3
  },
  "rewards": {
    "common": ["yellow_key", "potion_red", "gem_red"],
    "rare": ["sword_1", "shield_1"],
    "legendary": []
  }
}
```

### 难度递增对比

| 属性 | F1-5 | F6-10 | F11-15 | F16-21 |
|------|------|-------|---------|---------|
| 怪物基础等级 | 1 | 2 | 3 | 4 |
| 守门人最高等级 | 3 | 5 | 7 | 10 |
| 门颜色 | 黄 | 黄+蓝 | 黄+蓝+红 | 全色 |
| 守门人概率 | 40% | 50% | 60% | 70% |
| 机关概率 | 20% | 30% | 40% | 50% |

## 难度曲线设计

### 总体原则

- **总体线性递增**：每层难度稳步上升
- **每层内部波动**：允许低层出现高层怪物
- **回头机制**：玩家需要回来打之前打不过的怪

### 蓝图表达

```json
"monsters": {
  "main": {"tier": 1, "count": 4},
  "challenge": {"tier": 3, "count": 1}
}
```

## 使用方式

用户只需一句话：

```
"生成F1-5地图"
"重新生成第3层"
"生成全部21层地图"
```

Skill自动完成：设计蓝图 → 保存 → 运行脚本 → 输出地图

## 输出地图格式

生成的地图JSON必须符合现有 `data/maps/floor_*.json` 格式：

```json
{
  "level": 1,
  "name": "Floor 1 - Entrance Hall",
  "name_cn": "第1层 - 入口大厅",
  "width": 25,
  "height": 19,
  "player_start": [12, 17],
  "tiles": [
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 21, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    "... (19 rows total)"
  ],
  "entities": [
    {"type": "monster", "id": "slime_green", "x": 7, "y": 14, "data": {}},
    {"type": "item", "id": "yellow_key", "x": 12, "y": 17, "data": {}},
    {"type": "door", "id": "yellow", "x": 12, "y": 12, "data": {}},
    {"type": "shop", "id": "general_store", "x": 22, "y": 14, "data": {}}
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| level | int | 楼层编号 (1-21) |
| name | string | 英文名称 |
| name_cn | string | 中文名称 |
| width | int | 固定25 |
| height | int | 固定19 |
| player_start | [x, y] | 玩家起始坐标 |
| tiles | int[][] | 19x25的二维数组，tile ID |
| entities | object[] | 实体列表 |

### Tile ID 映射

| ID | 类型 | 说明 |
|----|------|------|
| 1 | FLOOR | 可行走地面 |
| 2 | WALL | 墙壁 |
| 20 | STAIRS_DOWN | 下行楼梯 |
| 21 | STAIRS_UP | 上行楼梯 |

## 区域解析算法

蓝图中的抽象区域ID到具体坐标的映射规则：

### 区域类型定义

| 类型 | 说明 | 放置规则 |
|------|------|----------|
| entrance | 玩家入口区域 | 固定在地图底部中央附近 |
| pathway | 主要通道 | 连接各区域的走廊 |
| side_room | 侧房间 | 从主通道分支的小房间 |
| vault | 宝库 | 需要钥匙才能进入的奖励区 |
| challenge | 挑战区 | 有强怪守卫的区域 |

### 解析流程

```python
def resolve_regions(layout, regions):
    # 1. 根据layout.pattern生成基础房间结构
    rooms = generate_rooms(layout.pattern, layout.room_count)

    # 2. 为每个region分配房间
    assigned = {}
    for region in regions:
        if region.type == "entrance":
            assigned[region.id] = rooms[0]  # 第一个房间
        elif region.type == "side_room":
            assigned[region.id] = find_smallest_room(rooms)
        else:
            assigned[region.id] = find_unassigned_room(rooms)

    # 3. 返回房间坐标范围
    return assigned  # {region_id: {"x": (x1, x2), "y": (y1, y2)}}
```

### 跨层引用解析

`"key_at": "floor_2_main"` 格式：
- `floor_N`：引用第N层
- `main`：该层的区域ID

```python
def resolve_cross_floor_reference(ref, all_blueprints):
    floor_num = int(ref.split("_")[1])
    region_id = ref.split("_", 2)[2]  # "floor_2_main" -> "main"
    return all_blueprints[floor_num].regions[region_id]
```

## unlock_sequence 完整Schema

```json
{
  "floor": 1,           // 门所在楼层
  "door": "yellow",     // 门颜色：yellow/blue/red/green
  "door_color": "yellow", // 别名字段，与door等价
  "key_at": "start",    // 钥匙位置：区域ID或跨层引用
  "target_region": "main", // 门后连接的区域（可选，默认自动推断）
  "key_count": 1        // 需要的钥匙数量（可选，默认1）
}
```

### 同层示例

```json
{"floor": 1, "door": "yellow", "key_at": "start", "target_region": "main"}
```

### 跨层示例

```json
{"floor": 3, "door": "blue", "key_at": "floor_2_vault", "target_region": "challenge"}
```

## 怪物等级映射

### Tier 到 Monster ID 映射表

| Tier | 怪物列表 |
|------|----------|
| 1 | slime_green, slime_red, bat |
| 2 | skeleton, ghost |
| 3 | orc, wizard |
| 4 | knight |
| 5 | dragon_baby |
| 6+ | demon_lord (Boss) |

### 配置文件位置

映射定义在 `tools/map_generator/config/monster_tiers.json`：

```json
{
  "tiers": {
    "1": ["slime_green", "slime_red", "bat"],
    "2": ["skeleton", "ghost"],
    "3": ["orc", "wizard"],
    "4": ["knight"],
    "5": ["dragon_baby"],
    "6": ["demon_lord"]
  },
  "tier_variance": {
    "1": {"min": 1, "max": 1},
    "2": {"min": 1, "max": 2},
    "3": {"min": 2, "max": 3}
  }
}
```

### variance 应用规则

```python
def get_monsters_for_tier(tier, variance):
    # tier=2, variance=1 -> 可能选tier 1-3的怪物
    min_tier = max(1, tier - variance)
    max_tier = min(6, tier + variance)
    available = []
    for t in range(min_tier, max_tier + 1):
        available.extend(MONSTER_TIERS[str(t)])
    return random.choice(available)
```

## 与现有Skill的集成

### 迁移策略

1. **保留现有SKILL.md** 作为设计指南
2. **新增Python脚本** 处理实际生成
3. **Skill工作流更新**：
   - 旧：AI直接生成地图JSON
   - 新：AI生成蓝图 → 调用Python脚本

### SKILL.md 改动

```markdown
## 生成流程

1. 根据用户请求选择对应模板
2. 设计蓝图JSON（参考examples/）
3. 保存蓝图到 .temp/blueprint.json
4. 运行 python tools/map_generator/generator.py --blueprint .temp/blueprint.json
5. 验证生成结果

## 验证检查

Python脚本内置验证，输出包含验证报告：
- [✓] 所有区域连通
- [✓] 钥匙-门平衡
- [✓] 楼梯正确
```

## 错误处理策略

### 错误类型与处理

| 错误 | 处理方式 | 用户提示 |
|------|----------|----------|
| 蓝图格式错误 | 立即退出，输出具体错误位置 | "蓝图JSON格式错误：第X行" |
| 区域引用不存在 | 立即退出，列出有效区域 | "未找到区域'xxx'，有效区域：entrance, main" |
| 模板文件缺失 | 使用默认配置 | "模板缺失，使用默认配置" |
| 输出文件存在 | 备份后覆盖 | "已备份旧文件到 .bak/" |
| 生成内部错误 | 输出调试信息 | "生成失败：xxx，请检查蓝图" |

### 错误输出格式

```json
{
  "success": false,
  "error": {
    "code": "REGION_NOT_FOUND",
    "message": "Region 'vault' not found in floor 1",
    "valid_regions": ["entrance", "main", "side_room"],
    "suggestion": "Check region IDs in blueprint"
  }
}
```

## 实现优先级

1. **Phase 1**: 核心生成器
   - generator.py 主入口
   - layout_builder.py 布局生成
   - connectivity.py 可达性追踪
   - output.py JSON输出
   - config/monster_tiers.json 怪物等级配置

2. **Phase 2**: 实体系统
   - entity_placer.py 怪物/道具放置
   - templates.py 模板加载

3. **Phase 3**: 惊喜元素（按优先级）
   - surprise_mechanics.py
     - 3.1 守门人机制
     - 3.2 机关陷阱
     - 3.3 楼层彩蛋
     - 3.4 商人惊喜
     - 3.5 隐藏房间

4. **Phase 4**: Skill改进
   - 更新 SKILL.md
   - 创建模板文件（4套）
   - 添加蓝图示例（每套至少1个）
