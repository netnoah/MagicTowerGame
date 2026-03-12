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
| 4.1a | ✅ 完成 | `systems/floor_manager.py` | 地图物品加载和渲染 |
| 4.1b | ✅ 完成 | `data/maps/floor_*.json` | 地图设计 (3层已完成) |
| 4.1c | ✅ 完成 | `assets/sprites/items/` | 物品资源 (钥匙/药水/宝石/武器/防具) |
| 4.1d | ✅ 完成 | `engine/game.py` | 宝石系统 (红宝石+攻击, 蓝宝石+防御) |
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

### 核心设计原则（必须遵守）

1. **门必须堵住唯一通道**:
   - 通道宽度必须为1格（最多2格）
   - 通道两侧必须是墙或边界
   - 玩家无法绕行，必须开门才能通过

2. **封闭房间入口**:
   - 门放在封闭房间的唯一入口处
   - 封闭房间四周被墙包围，只有1格开口
   - 门堵住这个开口，玩家必须开门才能进入

3. **玩家移动规则**:
   - 玩家只能上下左右移动，不能斜角移动
   - 门的两侧都必须有地板（玩家站的位置和目标位置）
   - 门不能放在墙角（斜角无法进入）

4. **⭐ 死锁避免原则（CRITICAL）**:
   - 玩家在遇到必须要过的门之前，必须能拿到相应的钥匙
   - 从玩家起点出发，检查可达区域内是否有足够钥匙
   - 钥匙位置必须在门的"解锁侧"（玩家开门前能到达的一侧）
   - 每个门的解锁路径：起点 → 拿钥匙 → 开门 → 新区域

5. **⭐ 封闭区域必须有门（CRITICAL）**:
   - 任何被墙完全包围的封闭区域都必须有门作为入口
   - 封闭区域内的物品/怪物玩家必须能够获取
   - 门是封闭区域的唯一入口，不能有其他绕行路径

6. **⭐ 门旁不能有绕行路（CRITICAL）**:
   - 门旁边的地板必须改成墙
   - 门所在的行/列，门必须是唯一的地板格
   - 玩家无法从门的上下/左右绕过门

### 有意义的门位置示例

```
正确的门设计（封闭房间）:
  墙墙墙墙墙墙墙
  墩 物品  墩
  墙墙墙门墙墙墙    ← 门堵住唯一1格入口，旁边是墙
  墙      墙

正确的门设计（通道）:
  墙墙墙墙墙墙墙
  墙      墙
  墙墙墙门墙墙墙    ← 通道宽度1格，门堵住唯一通道
  墙      墙
  墙墙墙墙墙墙墙

错误的门设计（可绕行）:
  墙墙墙墙墙墙墙
  墩      墩
  墩  门  墩        ← 门旁边是地板，可以从旁边绕过！
  墩      墩
  墙墙墙墙墙墙墙

错误的门设计（死锁）:
  起点 → 墙墙墙门墙墙墙 → 钥匙
         ↑
      没钥匙开不了门，拿不到钥匙，死锁！
```

### 地图设计验证清单

设计新地图时必须检查：

- [ ] **钥匙可达性**：从起点出发，每遇到一个门，之前是否有对应钥匙？
- [ ] **封闭区域**：所有封闭区域是否有门入口？
- [ ] **门旁绕行**：门旁边是否都是墙（不能有地板可绕行）？
- [ ] **门数量平衡**：钥匙数量是否足够开所有门？
- [ ] **门有意义**：门是否堵住唯一通道？不开门能否到达门的另一侧？

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

### 禁止的设计

- ❌ 宽通道放门（通道≥3格时门可绕过）
- ❌ 开阔地带放门（两侧无墙阻挡）
- ❌ 封闭房间没有门入口（玩家永远无法进入）
- ❌ 门后有门（连续门没有地面空间）
- ❌ 门数量超过钥匙数量
- ❌ 门放在墙角（斜角无法进入）
- ❌ **门旁边有地板可绕行**（门失去意义）
- ❌ **钥匙在门后面**（死锁，无法继续游戏）
- ❌ **封闭区域没有入口**（内容物永远无法获取）

---

## 更新日志

### 2026-03-11 (晚上)
- 实现宝石系统：
  - 红宝石：攻击力+3
  - 蓝宝石：防御力+3
  - 前三层地图添加宝石实体
  - 拾取消息显示属性增加

### 2026-03-11 (下午)
- 修复地图1门设计问题：
  - 修复死锁问题：钥匙移到玩家初始可达区域
  - 修复封闭区域：左上/右上封闭区域添加门入口
  - 修复门旁绕行：门旁边地板改成墙
- 完善门设计规则（三大铁律）：
  1. 死锁避免：门之前必须有钥匙
  2. 封闭区域有门：所有封闭区域必须有入口
  3. 门旁无绕行：门旁边必须是墙
- 创建项目文档结构：
  - `CLAUDE.md` 项目指令文件
  - `.claude/memory/MEMORY.md` 项目记忆文件

### 2026-03-11 (上午)
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
