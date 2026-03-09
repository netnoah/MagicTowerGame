"""
Game Engine - 游戏引擎核心

管理游戏主循环、状态和核心逻辑
"""

from typing import Optional, Callable, Any
from dataclasses import dataclass
import time

import pygame

from config import WindowConfig, GameState, Direction
from engine.display import DisplayManager
from engine.input import InputHandler, KeyAction, create_default_bindings
from engine.state_machine import GameStateMachine
from systems.floor_manager import FloorManager
from systems.tile import TileType
from systems.combat import CombatSystem, CombatResult
from entities.player import Player
from entities.monster import Monster


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

    def _update_menu(self) -> None:
        """更新菜单状态"""
        pass

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
        # 渲染地图
        offset = (0, 0)
        if self._floor_manager:
            offset = self._floor_manager.calculate_render_offset(
                self._display.width, self._display.height
            )
            self._floor_manager.render(self._display.render_surface, offset)

            # 渲染怪物
            self._floor_manager.render_monsters(self._display.render_surface, offset)

        # 渲染玩家
        if self._player:
            self._player.render(self._display.render_surface, offset)

        # 显示调试信息
        floor_text = f"Floor {self._floor_manager.current_level if self._floor_manager else 1}"
        if self._player:
            floor_text += f" | HP: {self._player.stats.hp}"
        self._display.draw_text(
            floor_text,
            (10, 10),
            font_size=16
        )

    def _render_menu(self) -> None:
        """渲染菜单状态"""
        center = self._display.get_center()
        self._display.draw_text(
            "MAGIC TOWER",
            (center[0], center[1] - 50),
            font_size=48,
            color=(255, 200, 100)
        )
        self._display.draw_text(
            "Press ENTER to Start",
            (center[0], center[1] + 20),
            font_size=24
        )
        self._display.draw_text(
            "Press ESC to Quit",
            (center[0], center[1] + 60),
            font_size=20,
            color=(150, 150, 150)
        )

    def _render_paused(self) -> None:
        """渲染暂停状态"""
        # 先渲染游戏画面（半透明）
        self._render_playing()

        # 暂停覆盖层
        overlay = pygame.Surface((self._display.width, self._display.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self._display.draw(overlay, (0, 0), camera_offset=False)

        center = self._display.get_center()
        self._display.draw_text(
            "PAUSED",
            center,
            font_size=48,
            color=(255, 255, 100)
        )
        self._display.draw_text(
            "Press ESC to Resume",
            (center[0], center[1] + 50),
            font_size=20
        )

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

    def move_player(self, direction: str) -> None:
        """
        移动玩家（由输入处理器调用）

        Args:
            direction: 移动方向 ("up", "down", "left", "right")
        """
        if self._state_machine.current_state != GameState.PLAYING:
            return

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
                # 触发战斗
                self._handle_combat(monster, target_x, target_y)
            else:
                # 正常移动
                moved = self._player.move(direction, self._floor_manager)
                if moved:
                    # 玩家成功移动后，允许再次切换楼层
                    self._can_change_floor = True

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
        else:
            # 无法击败，不执行战斗（避免玩家死亡）
            # 可以显示提示信息
            pass

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

    def toggle_pause(self) -> None:
        """切换暂停状态"""
        current = self._state_machine.current_state

        if current == GameState.PLAYING:
            self._state_machine.transition_to(GameState.PAUSED)
            self._input.disable()
        elif current == GameState.PAUSED:
            self._state_machine.transition_to(GameState.PLAYING)
            self._input.enable()

    def confirm(self) -> None:
        """确认/交互（由输入处理器调用）"""
        current = self._state_machine.current_state

        if current == GameState.MENU:
            self._state_machine.transition_to(GameState.PLAYING)
        elif current == GameState.DIALOG:
            # TODO: 推进对话
            pass
        elif current == GameState.SHOP:
            # TODO: 确认购买
            pass

    def start_new_game(self) -> None:
        """开始新游戏"""
        # TODO: 初始化玩家、地图等
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

    def _on_enter_paused(self) -> None:
        """进入暂停状态"""
        self._input.disable()
