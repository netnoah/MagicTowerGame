# 魔塔游戏 - 任务列表

> 最后更新: 2026-03-11

---

## 当前状态

**当前阶段**: Phase 4 - 物品和商店系统
**下一步**: 实现物品系统

### 快捷键说明

> **注意**: 为兼容中文输入法，不使用 a-z 字母键作为快捷键

| 功能 | 按键 |
|------|------|
| 移动 | ↑ ↓ ← → |
| 菜单导航 | ↑ ↓ |
| 确认/交互 | Enter / Space |
| 暂停/恢复 | ESC |
| 怪物信息面板 | 左Ctrl |

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

## Phase 3.5: UI 系统 ✅ 已完成

- [x] 3.5.1 UI 基础框架 (`ui/base.py`)
  - [x] UIComponent 基类
  - [x] UIFont 字体管理器
  - [x] Panel 面板组件
  - [x] Label 文本标签
  - [x] IconLabel 图标+文本
  - [x] StatBar 属性条
  - [x] MessageBox 消息框
- [x] 3.5.2 HUD 面板 (`ui/hud.py`)
  - [x] HUD 主面板（左侧显示）
  - [x] 楼层、属性、金币、钥匙显示
  - [x] 图标加载和渲染
- [x] 3.5.3 怪物信息面板
  - [x] MonsterInfoPanel 组件
  - [x] 快捷键打开/关闭面板
  - [x] 显示当前楼层所有怪物类型
  - [x] 显示能否战胜和预估伤害
  - [x] 上下键滚动列表
- [x] 3.5.4 消息系统
  - [x] MessageDisplay 组件
  - [x] 战斗结果提示
  - [x] 楼层切换提示
- [x] 3.5.5 菜单系统 (`ui/menu.py`)
  - [x] MainMenu 主菜单
  - [x] PauseMenu 暂停菜单
  - [x] GameOverScreen 结束界面
  - [x] 菜单导航（上下选择、确认）
- [x] 3.5.6 配置和集成
  - [x] HUDConfig 配置
  - [x] Game 类集成所有 UI 组件
  - [x] 地图偏移调整

---

## 配置说明

### 玩家 Pivot 配置 (`config.py`)

```python
SPRITE_PIVOT_X: int = 256  # 脚部在图片中的 X 坐标
SPRITE_PIVOT_Y: int = 480  # 脚部在图片中的 Y 坐标
```

用于将玩家脚部对齐到瓦片位置，根据实际图片调整这两个值。

---

## Phase 4: 物品和商店 (待实现)

- [ ] 4.1 物品系统 (`systems/items.py`)
  - [ ] 物品基类
  - [ ] 钥匙、药水、武器、防具
  - [ ] 物品效果
- [ ] 4.2 背包系统 (`systems/inventory.py`)
  - [ ] 背包管理
  - [ ] 物品使用
- [ ] 4.3 商店系统 (`systems/shop.py`)
  - [ ] 商店数据
  - [ ] 交易逻辑
- [ ] 4.4 商店界面 (`ui/shop_ui.py`)
  - [ ] 商店 UI
  - [ ] 交易确认

---

## Phase 5: 存档和音频 (待实现)

- [ ] 5.1 存档系统
  - [ ] 保存/加载
  - [ ] 存档槽管理
- [ ] 5.2 音频系统
  - [ ] BGM 播放
  - [ ] 音效系统

---

## 已知问题

### ~~怪物信息面板按键问题~~ ✅ 已解决
- **原因**: 中文输入法下 a-z 键会被拦截，导致字母键快捷键失效
- **解决方案**: 不使用 a-z 字母键作为快捷键，改用方向键、功能键、数字键

---

## 待讨论事项

- [x] ~~确定瓦片尺寸~~ → 48x48
- [x] ~~战斗界面风格~~ → 即时战斗，快捷键查看预览
- [x] ~~快捷键风格~~ → 不使用字母键，兼容中文输入法
- [ ] 是否需要地图编辑器?
- [ ] 是否需要更多楼层地图?

---

## 资源状态

### 已有资源
- [x] 玩家动画 (walk, attack, idle)
- [x] 怪物精灵 (10种)
- [x] 地图瓦片 (地板、墙壁、门、楼梯)
- [x] UI 图标 (金币、钥匙)
- [x] 字体文件 (semibold.ttf)

### 待补充资源
- [ ] 更多 UI 图标
- [ ] 物品图标
- [ ] 音效资源
- [ ] BGM
