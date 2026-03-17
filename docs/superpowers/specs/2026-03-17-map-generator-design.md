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

## 实现优先级

1. **Phase 1**: 核心生成器
   - generator.py 主入口
   - layout_builder.py 布局生成
   - connectivity.py 可达性追踪
   - output.py JSON输出

2. **Phase 2**: 实体系统
   - entity_placer.py 怪物/道具放置
   - templates.py 模板加载

3. **Phase 3**: 惊喜元素
   - surprise_mechanics.py 守门人/机关

4. **Phase 4**: Skill改进
   - 更新 SKILL.md
   - 创建模板文件
   - 添加蓝图示例
