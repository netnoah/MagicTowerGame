"""
Game Engine - 游戏引擎核心

管理游戏主循环、状态和核心逻辑
"""

from typing import Optional, Callable, Any, List, Dict
from dataclasses import dataclass
import time

import pygame

from config import WindowConfig, GameState, Direction, HUD
from engine.display import DisplayManager
from engine.input import InputHandler, KeyAction, create_default_bindings
from engine.state_machine import GameStateMachine
from systems.floor_manager import FloorManager
from systems.tile import TileType
from systems.combat import CombatSystem, CombatResult
from entities.player import Player
from entities.monster import Monster
from ui.hud import HUD as GameHUD, MessageDisplay, MonsterInfoPanel
from ui.menu import MainMenu, PauseMenu


@dataclass
class GameTime:
    """游戏时间数据"""
    total_time: float = 0.0      # 总游戏时间
    delta_time: float = 0.0      # 上一帧到这一帧的时间（秒）
    fps: float = 0.0             # 当前 FPS
    frame_count: int = 0         # 总帧数


class Game:
    """
    游戏引擎主类

    管理游戏的生命周期和主循环

    使用示例:
        game = Game()
        game.run()
    """

    def __init__(self,
                 width: int = WindowConfig.WIDTH,
                 height: int = WindowConfig.HEIGHT,
                 title: str = WindowConfig.TITLE,
                 fps: int = WindowConfig.FPS):
        """
        初始化游戏引擎

        Args:
            width: 窗口宽度
            height: 窗口高度
            title: 窗口标题
            fps: 目标帧率
        """
        # 配置
        self._target_fps = fps
        self._running = False

        # 核心组件
        self._display = DisplayManager(width, height, title)
        self._input = InputHandler()
        self._state_machine = GameStateMachine(GameState.MENU)

        # 禁用文本输入模式，防止 IME 拦截按键
        pygame.key.stop_text_input()

        # 时间追踪
        self._time = GameTime()
        self._clock = pygame.time.Clock()

        # 游戏数据（将在其他模块中初始化）
        self._player: Optional[Any] = None
        self._current_floor: Optional[Any] = None

        # 地图系统
        self._floor_manager: Optional[FloorManager] = None

        # 楼层切换状态
        self._can_change_floor: bool = True  # 是否可以切换楼层

        # 战斗系统
        self._combat_system = CombatSystem()
        self._last_combat_result: Optional[CombatResult] = None

        # UI 系统
        self._hud: Optional[GameHUD] = None
        self._message_display: Optional[MessageDisplay] = None
        self._monster_info_panel: Optional[MonsterInfoPanel] = None
        self._main_menu: Optional[MainMenu] = None
        self._pause_menu: Optional[PauseMenu] = None

        # 初始化主菜单
        self._main_menu = MainMenu(width, height)

        # 设置默认按键绑定
        self._setup_default_bindings()

        # 注册状态回调
        self._setup_state_callbacks()

    # ============================================================
    # 属性
    # ============================================================

    @property
    def display(self) -> DisplayManager:
        """显示管理器"""
        return self._display

    @property
    def input(self) -> InputHandler:
        """输入处理器"""
        return self._input

    @property
    def state_machine(self) -> GameStateMachine:
        """状态机"""
        return self._state_machine

    @property
    def time(self) -> GameTime:
        """游戏时间数据"""
        return self._time

    @property
    def is_running(self) -> bool:
        """游戏是否在运行"""
        return self._running

    # ============================================================
    # 游戏生命周期
    # ============================================================

    def run(self) -> None:
        """
        启动游戏主循环

        这是游戏的主入口点
        """
        self._running = True
        self._input.enable()

        last_time = time.time()

        while self._running:
            # 计算时间增量
            current_time = time.time()
            self._time.delta_time = current_time - last_time
            last_time = current_time
            self._time.total_time += self._time.delta_time
            self._time.frame_count += 1

            # 处理事件
            self._handle_events()

            # 更新游戏逻辑
            self._update()

            # 渲染
            self._render()

            # 控制帧率
            self._clock.tick(self._target_fps)
            self._time.fps = self._clock.get_fps()

        # 清理
        self._quit()

    def _handle_events(self) -> None:
        """处理所有 pygame 事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                return

            # 让输入处理器处理
            self._input.handle_event(event)

        # 处理持续按键
        self._input.update()

    def _update(self) -> None:
        """更新游戏逻辑"""
        # 更新状态机
        self._state_machine.update(self._time.delta_time)

        # 根据当前状态更新
        current_state = self._state_machine.current_state

        if current_state == GameState.PLAYING:
            self._update_playing()
        elif current_state == GameState.MENU:
            self._update_menu()
        elif current_state == GameState.PAUSED:
            self._update_paused()
        elif current_state == GameState.COMBAT:
            self._update_combat()
        elif current_state == GameState.SHOP:
            self._update_shop()
        elif current_state == GameState.DIALOG:
            self._update_dialog()

    def _render(self) -> None:
        """渲染游戏画面"""
        self._display.clear()

        current_state = self._state_machine.current_state

        if current_state == GameState.PLAYING:
            self._render_playing()
        elif current_state == GameState.MENU:
            self._render_menu()
        elif current_state == GameState.PAUSED:
            self._render_paused()
        elif current_state == GameState.COMBAT:
            self._render_combat()
        elif current_state == GameState.SHOP:
            self._render_shop()
        elif current_state == GameState.DIALOG:
            self._render_dialog()
        elif current_state == GameState.GAME_OVER:
            self._render_game_over()
        elif current_state == GameState.VICTORY:
            self._render_victory()

        self._display.present()

    def _quit(self) -> None:
        """清理游戏资源"""
        self._input.disable()
        self._display.quit()
        pygame.quit()

    # ============================================================
    # 状态更新方法（子类可以重写）
    # ============================================================

    def _update_playing(self) -> None:
        """更新游戏进行中状态"""
        # 更新玩家
        if self._player:
            self._player.update(self._time.delta_time)

            # 检测楼梯（玩家不在移动时才检测）
            if not self._player.is_moving:
                self._check_stairs()

        # 更新怪物
        if self._floor_manager:
            self._floor_manager.update_monsters(self._time.delta_time)

        # 更新消息显示
        if self._message_display:
            self._message_display.update(self._time.delta_time)

    def _update_menu(self) -> None:
        """更新菜单状态"""
        if self._main_menu:
            self._main_menu.update(self._time.delta_time)

    def _update_paused(self) -> None:
        """更新暂停状态"""
        pass

    def _update_combat(self) -> None:
        """更新战斗状态"""
        pass

    def _update_shop(self) -> None:
        """更新商店状态"""
        pass

    def _update_dialog(self) -> None:
        """更新对话状态"""
        pass

    # ============================================================
    # 状态渲染方法（子类可以重写）
    # ============================================================

    def _render_playing(self) -> None:
        """渲染游戏进行中状态"""
        # 地图偏移（为 HUD 留出空间）
        map_offset_x = HUD.MAP_OFFSET_X

        # 渲染地图
        offset = (map_offset_x, 0)
        if self._floor_manager:
            # 计算地图渲染偏移（考虑 HUD 空间）
            original_offset = self._floor_manager.calculate_render_offset(
                self._display.width - HUD.WIDTH, self._display.height
            )
            offset = (original_offset[0] + map_offset_x, original_offset[1])
            self._floor_manager.render(self._display.render_surface, offset)

            # 渲染怪物
            self._floor_manager.render_monsters(self._display.render_surface, offset)
            # 渲染物品
            self._floor_manager.render_items(self._display.render_surface, offset)
            # 渲染物品
            self._floor_manager.render_items(self._display.render_surface, offset)

        # 渲染玩家
        if self._player:
            self._player.render(self._display.render_surface, offset)

        # 渲染 HUD
        if self._hud and self._player:
            self._hud.update_data(
                floor=self._floor_manager.current_level if self._floor_manager else 1,
                stats=self._player.stats
            )
            self._hud.render(self._display.render_surface)

        # 渲染怪物信息面板
        if self._monster_info_panel:
            self._monster_info_panel.render(self._display.render_surface)

        # 渲染消息
        if self._message_display:
            self._message_display.render(self._display.render_surface)

    def _render_menu(self) -> None:
        """渲染菜单状态"""
        if self._main_menu:
            self._main_menu.render(self._display.render_surface)

    def _render_paused(self) -> None:
        """渲染暂停状态"""
        # 先渲染游戏画面
        self._render_playing()

        # 渲染暂停菜单
        if self._pause_menu is None:
            self._pause_menu = PauseMenu(self._display.width, self._display.height)

        self._pause_menu.render(self._display.render_surface)

    def _render_combat(self) -> None:
        """渲染战斗状态"""
        pass

    def _render_shop(self) -> None:
        """渲染商店状态"""
        pass

    def _render_dialog(self) -> None:
        """渲染对话状态"""
        pass

    def _render_game_over(self) -> None:
        """渲染游戏结束状态"""
        center = self._display.get_center()
        self._display.draw_text(
            "GAME OVER",
            center,
            font_size=48,
            color=(255, 80, 80)
        )

    def _render_victory(self) -> None:
        """渲染胜利状态"""
        center = self._display.get_center()
        self._display.draw_text(
            "VICTORY!",
            center,
            font_size=48,
            color=(100, 255, 100)
        )

    # ============================================================
    # 游戏操作方法
    # ============================================================

    def _check_stairs(self) -> None:
        """检测玩家是否站在楼梯上"""
        if not self._player or not self._floor_manager:
            return

        # 只有在允许切换时才检测
        if not self._can_change_floor:
            return

        tile = self._floor_manager.get_tile(
            self._player.tile_x,
            self._player.tile_y
        )

        if tile == TileType.STAIRS_UP:
            # 上楼
            self._change_floor(self._floor_manager.current_level + 1, is_going_up=True)
        elif tile == TileType.STAIRS_DOWN:
            # 下楼
            self._change_floor(self._floor_manager.current_level - 1, is_going_up=False)

    def _change_floor(self, target_level: int, is_going_up: bool) -> None:
        """
        切换楼层

        Args:
            target_level: 目标楼层
            is_going_up: 是否是上楼
        """
        if target_level < 1:
            return  # 不能下到 0 层

        # 加载目标楼层
        if not self._floor_manager.load_floor(target_level):
            return  # 加载失败

        # 更新玩家楼层
        self._player.current_floor = target_level

        # 设置玩家位置到对应楼梯
        if is_going_up:
            # 上楼后出现在下楼楼梯位置
            stairs_pos = self._floor_manager.get_stairs_down()
        else:
            # 下楼后出现在上楼楼梯位置
            stairs_pos = self._floor_manager.get_stairs_up()

        if stairs_pos:
            self._player.set_position(stairs_pos[0], stairs_pos[1])
        else:
            # 没有楼梯则使用玩家起始位置
            start_pos = self._floor_manager.get_player_start()
            self._player.set_position(start_pos[0], start_pos[1])

        # 禁用楼层切换，直到玩家移动
        self._can_change_floor = False

        # 显示消息
        self._show_message(f"Floor {target_level}", (255, 200, 100))

    def move_player(self, direction: str) -> None:
        """
        移动玩家（由输入处理器调用）

        Args:
            direction: 移动方向 ("up", "down", "left", "right")
        """
        if self._state_machine.current_state != GameState.PLAYING:
            return

        # 如果怪物信息面板打开，用 UP/DOWN 键滚动，LEFT/RIGHT 仍然可以移动
        if self._monster_info_panel and self._monster_info_panel.is_visible():
            if direction == "up":
                self._monster_info_panel.scroll_up()
                return
            elif direction == "down":
                self._monster_info_panel.scroll_down()
                return
            # LEFT/RIGHT 继续执行移动逻辑

        if self._player and self._floor_manager:
            # 如果正在移动，不处理
            if self._player.is_moving:
                return

            # 计算目标位置
            vector = Direction.VECTORS.get(direction, (0, 0))
            target_x = self._player.tile_x + vector[0]
            target_y = self._player.tile_y + vector[1]

            # 检查目标位置是否有怪物
            monster = self._floor_manager.get_monster_at(target_x, target_y)
            if monster and monster.is_alive:
                # 直接战斗
                self._handle_combat(monster, target_x, target_y)
            else:
                # 正常移动
                moved = self._player.move(direction, self._floor_manager)
                if moved:
                    # 玩家成功移动后，允许再次切换楼层
                    self._can_change_floor = True

                    # 检查并拾取物品
                    self._check_and_pickup_item()

    def _handle_combat(self, monster: Monster, target_x: int, target_y: int) -> None:
        """
        处理战斗

        Args:
            monster: 怪物实体
            target_x: 目标 X 坐标
            target_y: 目标 Y 坐标
        """
        # 预览战斗结果
        result = self._combat_system.preview_battle(
            self._player.stats, monster.stats
        )

        if result.victory:
            # 执行战斗
            self._combat_system.execute_battle(self._player, monster, result)

            # 移除怪物
            self._floor_manager.remove_monster(target_x, target_y)

            # 移动玩家到怪物位置
            self._player.set_position(target_x, target_y)
            self._can_change_floor = True

            # 更新面向方向
            self._player._facing_direction = self._get_direction_to(target_x, target_y)

            # 显示战斗结果消息
            monster_name = monster.stats.name_cn or monster.stats.name or monster.monster_id
            self._show_message(f"Defeated {monster_name}!", (100, 255, 100))
            if result.player_damage > 0:
                self._show_message(f"Lost {result.player_damage} HP", (255, 150, 100))
        else:
            # 无法击败
            self._show_message("Cannot defeat!", (255, 100, 100))

    def _show_message(self, text: str, color: tuple = (255, 255, 255)) -> None:
        """显示消息"""
        if self._message_display:
            self._message_display.add_message(text, color)

    def _check_and_pickup_item(self) -> None:
        """检查并拾取玩家当前位置的物品"""
        if not self._player or not self._floor_manager:
            return

        # 获取玩家当前位置的物品
        item_entity = self._floor_manager.get_item_at(
            self._player.tile_x, self._player.tile_y
        )

        if not item_entity:
            return

        # 获取物品数据
        item_data = self._floor_manager.get_item_data(item_entity.entity_id)
        if not item_data:
            return

        # 应用物品效果
        if item_data.effect:
            changes = item_data.effect.apply(self._player.stats)

            # 显示效果消息
            item_name = item_data.name_cn or item_data.name

            # 根据物品类型显示不同消息
            if item_data.item_type.value == "key":
                key_colors = {
                    "yellow": (255, 255, 100),
                    "blue": (100, 150, 255),
                    "red": (255, 100, 100)
                }
                color = key_colors.get(item_entity.entity_id.split('_')[0], (255, 255, 255))
                self._show_message(f"Got {item_name}!", color)
            elif item_data.item_type.value == "potion":
                hp_change = changes.get('hp', 0)
                self._show_message(f"Used {item_name}: HP+{hp_change}", (100, 255, 100))
            elif item_data.item_type.value == "weapon":
                atk_change = changes.get('attack', 0)
                self._show_message(f"Equipped {item_name}: ATK+{atk_change}", (255, 180, 80))
            elif item_data.item_type.value == "armor":
                def_change = changes.get('defense', 0)
                self._show_message(f"Equipped {item_name}: DEF+{def_change}", (80, 180, 255))
            elif item_data.item_type.value == "special":
                if changes.get('gold', 0) > 0:
                    self._show_message(f"Got {changes['gold']} Gold!", (255, 215, 0))
                elif changes.get('experience', 0) > 0:
                    self._show_message(f"Got {changes['experience']} EXP!", (200, 150, 255))
                elif changes.get('max_hp', 0) > 0:
                    self._show_message(f"Max HP+{changes['max_hp']}!", (255, 100, 200))
                else:
                    self._show_message(f"Got {item_name}!", (100, 255, 100))
            else:
                self._show_message(f"Got {item_name}!", (255, 255, 255))

        # 移除物品
        self._floor_manager.remove_item(self._player.tile_x, self._player.tile_y)

    def _get_direction_to(self, target_x: int, target_y: int) -> str:
        """获取从玩家当前位置到目标位置的方向"""
        dx = target_x - self._player.tile_x
        dy = target_y - self._player.tile_y

        if dx > 0:
            return Direction.RIGHT
        elif dx < 0:
            return Direction.LEFT
        elif dy > 0:
            return Direction.DOWN
        elif dy < 0:
            return Direction.UP
        return self._player.facing_direction

    def toggle_monster_info(self) -> None:
        """切换怪物信息面板"""
        if self._state_machine.current_state != GameState.PLAYING:
            return

        if self._monster_info_panel:
            self._monster_info_panel.toggle()

            # 如果打开，更新数据
            if self._monster_info_panel.is_visible():
                self._update_monster_info()

    def _update_monster_info(self) -> None:
        """更新怪物信息面板数据"""
        if not self._monster_info_panel or not self._floor_manager or not self._player:
            return

        # 获取当前楼层所有怪物
        monsters = self._floor_manager.get_current_monsters()

        # 按类型分组并计算战斗预览
        monster_dict: Dict[str, Dict] = {}

        for monster in monsters:
            if not monster.is_alive:
                continue

            monster_id = monster.monster_id

            if monster_id not in monster_dict:
                # 预览战斗
                result = self._combat_system.preview_battle(
                    self._player.stats, monster.stats
                )

                monster_dict[monster_id] = {
                    'name': monster.stats.name_cn or monster.stats.name or monster_id,
                    'hp': monster.stats.hp,
                    'atk': monster.stats.attack,
                    'def': monster.stats.defense,
                    'can_win': result.victory,
                    'damage_taken': result.player_damage if result.victory else 0,
                    'rounds': result.rounds if result.victory else 0,
                    'count': 1
                }
            else:
                monster_dict[monster_id]['count'] += 1

        # 转换为列表
        monster_list = list(monster_dict.values())

        # 更新面板
        self._monster_info_panel.update_data(
            floor=self._floor_manager.current_level,
            monster_info_list=monster_list
        )

    def toggle_pause(self) -> None:
        """切换暂停状态"""
        current = self._state_machine.current_state

        # 如果怪物信息面板打开，先关闭它
        if current == GameState.PLAYING:
            if self._monster_info_panel and self._monster_info_panel.is_visible():
                self._monster_info_panel.toggle()
                return

        if current == GameState.PLAYING:
            self._state_machine.transition_to(GameState.PAUSED)
        elif current == GameState.PAUSED:
            self._state_machine.transition_to(GameState.PLAYING)

    def menu_select_up(self) -> None:
        """菜单选择上一项"""
        current = self._state_machine.current_state
        if current == GameState.MENU and self._main_menu:
            self._main_menu.select_prev()
        elif current == GameState.PAUSED and self._pause_menu:
            self._pause_menu.select_prev()

    def menu_select_down(self) -> None:
        """菜单选择下一项"""
        current = self._state_machine.current_state
        if current == GameState.MENU and self._main_menu:
            self._main_menu.select_next()
        elif current == GameState.PAUSED and self._pause_menu:
            self._pause_menu.select_next()

    def menu_confirm(self) -> None:
        """菜单确认选择"""
        current = self._state_machine.current_state

        if current == GameState.MENU and self._main_menu:
            action = self._main_menu.selected_action
            if action == "new_game":
                self._state_machine.transition_to(GameState.PLAYING)
            elif action == "quit":
                self._running = False
        elif current == GameState.PAUSED and self._pause_menu:
            action = self._pause_menu.selected_action
            if action == "resume":
                self._state_machine.transition_to(GameState.PLAYING)
                self._input.enable()
            elif action == "main_menu":
                self._state_machine.transition_to(GameState.MENU)
            elif action == "quit":
                self._running = False

    def confirm(self) -> None:
        """确认/交互（由输入处理器调用）"""
        current = self._state_machine.current_state

        if current == GameState.MENU:
            self.menu_confirm()
        elif current == GameState.PAUSED:
            self.menu_confirm()
        elif current == GameState.DIALOG:
            # TODO: 推进对话
            pass
        elif current == GameState.SHOP:
            # TODO: 确认购买
            pass

    def start_new_game(self) -> None:
        """开始新游戏"""
        self._state_machine.transition_to(GameState.PLAYING)

    def quit_game(self) -> None:
        """退出游戏"""
        self._running = False

    # ============================================================
    # 内部方法
    # ============================================================

    def _setup_default_bindings(self) -> None:
        """设置默认按键绑定"""
        create_default_bindings(self._input, self)

        # 退出游戏（在菜单中）
        self._input.bind_key(
            pygame.K_q, KeyAction.PRESS,
            self._quit_from_menu,
            "quit_from_menu"
        )

        # 菜单上下选择
        self._input.bind_key(
            pygame.K_UP, KeyAction.PRESS,
            self.menu_select_up,
            "menu_select_up"
        )
        self._input.bind_key(
            pygame.K_DOWN, KeyAction.PRESS,
            self.menu_select_down,
            "menu_select_down"
        )

        self._input.bind_key(
            pygame.K_LCTRL, KeyAction.PRESS,
            self.toggle_monster_info,
            "toggle_monster_info_ctrl"
        )

    def _quit_from_menu(self) -> None:
        """从菜单退出游戏"""
        if self._state_machine.current_state == GameState.MENU:
            self._running = False

    def _setup_state_callbacks(self) -> None:
        """设置状态回调"""
        self._state_machine.on_enter(
            GameState.PLAYING,
            self._on_enter_playing
        )
        self._state_machine.on_enter(
            GameState.PAUSED,
            self._on_enter_paused
        )

    def _on_enter_playing(self) -> None:
        """进入游戏进行中状态"""
        self._input.enable()

        # 初始化地图系统
        if self._floor_manager is None:
            self._floor_manager = FloorManager()
            self._floor_manager.load_tiles()
            self._floor_manager.load_floor(1)

        # 初始化玩家
        if self._player is None and self._floor_manager:
            start_pos = self._floor_manager.get_player_start()
            self._player = Player(start_pos[0], start_pos[1])
            self._player.load_resources()

        # 初始化 HUD
        if self._hud is None:
            self._hud = GameHUD(
                x=HUD.OFFSET_X,
                y=HUD.OFFSET_Y,
                height=self._display.height
            )

        # 初始化怪物信息面板
        if self._monster_info_panel is None:
            self._monster_info_panel = MonsterInfoPanel()

        # 初始化消息显示
        if self._message_display is None:
            self._message_display = MessageDisplay(
                x=HUD.WIDTH + 10,
                y=self._display.height - 100,
                width=self._display.width - HUD.WIDTH - 20
            )

    def _on_enter_paused(self) -> None:
        """进入暂停状态"""
        pass  # 输入处理器保持启用，按键回调会根据状态处理
