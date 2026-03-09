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

### Phase 1: 基础框架 ✅ 进行中

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 1.1 | ✅ 完成 | `systems/resource_loader.py` | 资源加载器，支持自动加载+旋转 |
| 1.2 | ✅ 完成 | `systems/animation.py` | 动画播放系统 |
| 1.3 | ⏳ 待做 | `main.py` | 游戏入口和主循环 |
| 1.4 | ⏳ 待做 | `engine/game.py` | 游戏引擎核心 |
| 1.5 | ⏳ 待做 | `engine/display.py` | 显示管理 |
| 1.6 | ⏳ 待做 | `engine/input.py` | 输入处理 |
| 1.7 | ⏳ 待做 | `config.py` | 全局配置 |

### Phase 2: 地图系统

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 2.1 | ⏳ 待做 | `systems/tile.py` | 瓦片类型和渲染 |
| 2.2 | ⏳ 待做 | `systems/floor_manager.py` | 楼层管理 |
| 2.3 | ⏳ 待做 | `systems/collision.py` | 碰撞检测 |
| 2.4 | ⏳ 待做 | `data/maps/floor_01.json` | 第一层地图数据 |

### Phase 3: 战斗系统

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 3.1 | ⏳ 待做 | `entities/player.py` | 玩家实体 |
| 3.2 | ⏳ 待做 | `entities/monster.py` | 怪物实体 |
| 3.3 | ⏳ 待做 | `systems/combat.py` | 战斗逻辑 |
| 3.4 | ⏳ 待做 | `data/entities/monsters.json` | 怪物数据 |

### Phase 4: 物品和商店

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 4.1 | ⏳ 待做 | `systems/item.py` | 物品系统 |
| 4.2 | ⏳ 待做 | `systems/inventory.py` | 背包系统 |
| 4.3 | ⏳ 待做 | `systems/shop.py` | 商店系统 |
| 4.4 | ⏳ 待做 | `ui/shop_ui.py` | 商店界面 |

### Phase 5: 界面和完善

| 步骤 | 状态 | 文件 | 说明 |
|-----|------|------|------|
| 5.1 | ⏳ 待做 | `ui/hud.py` | 游戏HUD |
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

## 更新日志

### 2026-03-09
- 创建项目规划文档
- 完成资源加载器 (`systems/resource_loader.py`)
- 完成动画系统 (`systems/animation.py`)
- 确定资源规范和命名约定
