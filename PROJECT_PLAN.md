# 魔塔游戏 (Magic Tower Game) - 项目规划

> 创建日期: 2026-03-09
> 技术栈: Python + Pygame
> 开发者: AI + User

---

## 项目概述

经典魔塔RPG游戏复刻，玩家需要在21层塔楼中探索、战斗、收集钥匙和道具，最终击败魔王。

### 核心特性
- 多层楼塔地图 (21+ 层)
- 回合制战斗系统
- 钥匙开门机制 (红/蓝/黄)
- 商店系统 (购买装备、升级属性)
- 物品和道具系统
- 存档/读档功能

---

## 技术选型

| 组件 | 选择 | 理由 |
|-----|------|-----|
| 游戏框架 | Pygame | 成熟稳定，2D游戏首选 |
| 地图格式 | JSON | 易读易编辑 |
| 存档格式 | JSON | 便于调试 |
| 图片格式 | PNG | 支持透明通道 |
| 音频格式 | OGG/WAV | Pygame原生支持 |

---

## 目录结构

```
MagicTowerGame/
│
├── main.py                      # 游戏入口
├── config.py                    # 全局配置
├── requirements.txt             # 依赖
│
├── engine/                      # 核心引擎
│   ├── game.py                  # 游戏主循环
│   ├── display.py               # 渲染系统
│   ├── input.py                 # 输入处理
│   ├── audio.py                 # 音频系统
│   └── state_machine.py         # 状态机
│
├── entities/                    # 游戏实体
│   ├── player.py                # 玩家
│   ├── monster.py               # 怪物
│   ├── npc.py                   # NPC
│   └── entity.py                # 实体基类
│
├── systems/                     # 游戏系统
│   ├── resource_loader.py       # 资源加载器 ✅
│   ├── animation.py             # 动画系统 ✅
│   ├── combat.py                # 战斗系统
│   ├── floor_manager.py         # 楼层管理
│   ├── collision.py             # 碰撞检测
│   ├── item.py                  # 物品系统
│   ├── inventory.py             # 背包系统
│   ├── shop.py                  # 商店系统
│   └── tile.py                  # 瓦片系统
│
├── ui/                          # 用户界面
│   ├── hud.py                   # 游戏HUD
│   ├── menu.py                  # 菜单
│   ├── dialog.py                # 对话框
│   └── shop_ui.py               # 商店界面
│
├── data/                        # 数据文件
│   ├── maps/                    # 地图JSON
│   ├── entities/                # 实体定义
│   └── saves/                   # 存档
│
└── assets/                      # 游戏资源
    ├── sprites/                 # 图片资源
    │   ├── playerA/             # 玩家A动画
    │   │   ├── walk_0.png
    │   │   ├── walk_1.png
    │   │   └── ...
    │   ├── monsters/            # 怪物动画
    │   ├── tiles/               # 地图瓦片
    │   └── items/               # 物品图标
    ├── audio/                   # 音频
    └── fonts/                   # 字体
```

---

## 资源规范

### 图片资源命名

动画帧文件命名格式: `<动画名>_<帧号>.png`

```
assets/sprites/playerA/
├── walk_0.png      # 行走动画第0帧
├── walk_1.png
├── ...
├── attack_0.png    # 攻击动画第0帧
├── attack_1.png
└── ...
```

### 方向生成

原始图片默认为 **向右 (RIGHT)**，系统自动旋转生成其他方向：
- RIGHT = 原图 (0°)
- UP = 旋转 90°
- LEFT = 旋转 180°
- DOWN = 旋转 270°

### 图片要求

| 项目 | 规格 |
|-----|------|
| 格式 | PNG (透明背景) |
| 尺寸 | 32x32 或 64x64 (统一) |
| 原图方向 | 面向右边 |

---

## 开发进度

### Phase 1: 基础框架 ✅ 完成

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 1.1 | ✅ 完成 | `systems/resource_loader.py` | 资源加载器，支持自动加载+旋转+sprite加载 |
| 1.2 | ✅ 完成 | `systems/animation.py` | 动画播放系统 |
| 1.3 | ✅ 完成 | `main.py` | 游戏入口和主循环 |
| 1.4 | ✅ 完成 | `engine/game.py` | 游戏引擎核心 |
| 1.5 | ✅ 完成 | `engine/display.py` | 显示管理 |
| 1.6 | ✅ 完成 | `engine/input.py` | 输入处理 |
| 1.7 | ✅ 完成 | `config.py` | 全局配置 |

### Phase 2: 地图系统 ✅ 完成

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 2.1 | ✅ 完成 | `systems/tile.py` | 瓦片类型和渲染 |
| 2.2 | ✅ 完成 | `systems/floor_manager.py` | 楼层管理 |
| 2.3 | ✅ 完成 | `systems/collision.py` | 碰撞检测 |
| 2.4 | ✅ 完成 | `data/maps/floor_*.json` | 地图数据 (4层已完成) |

### Phase 3: 战斗系统 ✅ 完成

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 3.1 | ✅ 完成 | `entities/player.py` | 玩家实体 |
| 3.2 | ✅ 完成 | `entities/monster.py` | 怪物实体 |
| 3.3 | ✅ 完成 | `systems/combat.py` | 战斗逻辑 |
| 3.4 | ✅ 完成 | `data/entities/monsters.json` | 怪物数据 |

### Phase 4: 物品和商店 ✅ 进行中

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 4.1 | ✅ 完成 | `systems/items.py` | 物品系统 (含sprite渲染) |
| 4.2 | ⏳ 待做 | `systems/inventory.py` | 背包系统 |
| 4.3 | ⏳ 待做 | `systems/shop.py` | 商店系统 |
| 4.4 | ⏳ 待做 | `ui/shop_ui.py` | 商店界面 |

### Phase 5: 界面和完善 ✅ 进行中

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 5.1 | ✅ 完成 | `ui/hud.py` | 游戏HUD |
| 5.2 | ⏳ 待做 | `ui/menu.py` | 菜单系统 |
| 5.3 | ⏳ 待做 | `data/save_manager.py` | 存档系统 |
| 5.4 | ⏳ 待做 | `engine/audio.py` | 音频系统 |

---

## 核心数据结构

### 玩家属性

```python
@dataclass
class PlayerStats:
    level: int = 1
    hp: int = 1000
    max_hp: int = 1000
    attack: int = 10
    defense: int = 10

    gold: int = 0
    experience: int = 0

    yellow_keys: int = 0
    blue_keys: int = 0
    red_keys: int = 0

    current_floor: int = 1
    position: Tuple[int, int] = (0, 0)
```

### 战斗公式

```python
def calculate_damage(attacker_attack, defender_defense):
    return max(1, attacker_attack - defender_defense)

def battle_rounds(player, monster):
    player_damage = calculate_damage(player.attack, monster.defense)
    monster_damage = calculate_damage(monster.attack, player.defense)

    rounds = math.ceil(monster.hp / player_damage)
    total_damage = rounds * monster_damage

    return rounds, total_damage
```

### 瓦片类型

```python
class TileType(Enum):
    FLOOR = 0
    WALL = 1
    YELLOW_DOOR = 10
    BLUE_DOOR = 11
    RED_DOOR = 12
    STAIRS_UP = 20
    STAIRS_DOWN = 21
    SHOP = 30
    NPC = 31
```

---

## 下一步行动

1. **创建游戏主循环** (`main.py`, `engine/game.py`)
2. **实现基础渲染** (`engine/display.py`)
3. **添加输入处理** (`engine/input.py`)
4. **创建玩家实体** (`entities/player.py`)
5. **实现地图系统** (`systems/tile.py`, `systems/floor_manager.py`)

---

## 注意事项

- 所有代码遵循 **不可变原则** (创建新对象，不修改原对象)
- 测试覆盖率目标 **80%+**
- 文件大小控制在 **800行以内**
- 函数大小控制在 **50行以内**

---

## 门与钥匙设计规则

### 门类型

| 类型 | 瓦片值 | 钥匙类型 | 稀有度 |
|-----|-------|---------|--------|
| 黄门 | 10 | yellow_key | 常见 |
| 蓝门 | 11 | blue_key | 较少 |
| 红门 | 12 | red_key | 稀有 |
| 绿门 | 13 | green_key | 非常稀有 |

### 设计原则

1. **数量匹配**: 每种颜色的门数量 ≤ 对应钥匙数量（确保游戏可通关）
2. **稀有度递减**: 黄门 > 蓝门 > 红门 > 绿门（数量从多到少）
3. **有意义放置**: 门必须放在通道位置，只有开门才能通过，没有绕行路线
4. **无封闭区域**: 所有区域必须可达，不能设计完全封闭的区域

### 门数量规划（21层）

| 楼层范围 | 黄门 | 蓝门 | 红门 | 绿门 |
|---------|-----|-----|-----|-----|
| 1-5层 | 8-12 | 2-4 | 0-1 | 0 |
| 6-10层 | 6-10 | 4-6 | 2-3 | 0-1 |
| 11-15层 | 4-8 | 3-5 | 3-4 | 1-2 |
| 16-21层 | 2-6 | 2-4 | 4-6 | 2-3 |
| **总计** | ~40 | ~20 | ~12 | ~5 |

### 钥匙分布规划

钥匙总数应略多于门数（留有富余）：
- 黄钥匙: 45-50 把
- 蓝钥匙: 22-25 把
- 红钥匙: 15-18 把
- 绿钥匙: 6-8 把

### 放置规则

1. **通道门**: 放在走廊或通道中间，阻断通行
2. **房间门**: 放在房间入口处，控制进入
3. **宝库门**: 放在重要物品房间前，用高级门保护
4. **分支选择**: 在分支路口放门，增加策略性

### 禁止的设计

- ❌ 封闭区域（四面都是墙或门，没有入口）
- ❌ 门后有门（连续门没有地面空间）
- ❌ 门旁边有可绕行的路径
- ❌ 门数量超过钥匙数量

---

## 更新日志

### 2026-03-11
- 完善物品sprite渲染系统
- 添加盾牌装备数据 (shield_1~5)
- 优化资源加载器（物品/怪物保持原始大小）
- 添加门与钥匙设计规则
- 修复重复渲染bug

### 2026-03-09
- 创建项目规划文档
- 完成资源加载器 (`systems/resource_loader.py`)
- 完成动画系统 (`systems/animation.py`)
- 确定资源规范和命名约定
