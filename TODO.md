# 魔塔游戏 - 任务列表

> 最后更新: 2026-03-09

---

## 当前状态

**当前阶段**: Phase 3 - 战斗系统
**下一步**: 实现怪物实体和战斗逻辑

---

## Phase 1: 基础框架 ✅ 已完成

- [x] 1.1 资源加载器 (`systems/resource_loader.py`)
- [x] 1.2 动画播放系统 (`systems/animation.py`)
- [x] 1.3 全局配置 (`config.py`)
- [x] 1.4 游戏入口 (`main.py`)
- [x] 1.5 游戏引擎 (`engine/game.py`)
- [x] 1.6 显示管理 (`engine/display.py`)
- [x] 1.7 输入处理 (`engine/input.py`)
- [x] 1.8 状态机 (`engine/state_machine.py`)

---

## Phase 2: 地图系统 ✅ 已完成

- [x] 2.1 瓦片系统 (`systems/tile.py`)
- [x] 2.2 楼层管理 (`systems/floor_manager.py`)
- [x] 2.3 地图数据格式 (JSON)
- [x] 2.4 创建第一层测试地图 (`data/maps/floor_01.json`)
- [x] 2.5 集成地图到主游戏 (`engine/game.py`)
- [x] 2.6 碰撞检测（集成在 FloorManager.is_walkable）

---

## Phase 3: 战斗系统 ✅ 已完成

- [x] 3.1 玩家实体 (`entities/player.py`)
  - [x] 属性系统 (HP/攻击/防御/金币/钥匙)
  - [x] 移动系统 (平滑移动/方向控制)
  - [x] 碰撞检测 (与地图瓦片)
  - [x] 动画渲染 (stat/walk/attack)
  - [x] 方向翻转 (左/右使用水平翻转)
  - [x] Pivot 对齐 (动态获取底部中心)
- [x] 3.2 怪物实体 (`entities/monster.py`)
  - [x] MonsterManager 怪物数据管理
  - [x] Monster 怪物实体类
  - [x] 属性和渲染
- [x] 3.3 战斗逻辑 (`systems/combat.py`)
  - [x] 回合制战斗计算
  - [x] 伤害公式 (攻击-防御, 最小1)
  - [x] 战斗结果预览
  - [x] 战斗执行
- [x] 3.4 怪物数据定义 (`data/entities/monsters.json`)
  - [x] 10种怪物定义
- [x] 3.5 集成怪物到地图
  - [x] FloorManager 加载/渲染怪物
  - [x] 玩家碰撞怪物触发战斗

---

## 配置说明

### 玩家 Pivot 配置 (`config.py`)

```python
SPRITE_PIVOT_X: int = 256  # 脚部在图片中的 X 坐标
SPRITE_PIVOT_Y: int = 480  # 脚部在图片中的 Y 坐标
```

用于将玩家脚部对齐到瓦片位置，根据实际图片调整这两个值。

---

## Phase 3: 战斗系统

- [ ] 3.1 玩家实体 (`entities/player.py`)
- [ ] 3.2 怪物实体 (`entities/monster.py`)
- [ ] 3.3 战斗逻辑 (`systems/combat.py`)
- [ ] 3.4 怪物数据定义

---

## Phase 4: 物品和商店

- [ ] 4.1 物品系统
- [ ] 4.2 背包系统
- [ ] 4.3 商店系统
- [ ] 4.4 商店界面

---

## Phase 5: 界面和完善

- [ ] 5.1 游戏HUD
- [ ] 5.2 菜单系统
- [ ] 5.3 存档系统
- [ ] 5.4 音频系统

---

## 待讨论事项

- [ ] 确定瓦片尺寸 (32x32 或 48x48?)
- [ ] 战斗界面风格 (弹窗 vs 即时?)
- [ ] 是否需要地图编辑器?

---

## 资源准备清单

### 玩家
- [ ] walk 动画 (行走)
- [ ] attack 动画 (攻击)
- [ ] idle 动画 (待机)

### 怪物
- [ ] 史莱姆
- [ ] 蝙蝠
- [ ] 骷髅
- [ ] Boss

### 地图
- [ ] 地板
- [ ] 墙壁
- [ ] 门 (黄/蓝/红)
- [ ] 楼梯 (上/下)

### 物品
- [ ] 钥匙 (黄/蓝/红)
- [ ] 药水
- [ ] 武器
- [ ] 防具

### UI
- [ ] HUD 背景
- [ ] 按钮
- [ ] 面板
- [ ] 图标
