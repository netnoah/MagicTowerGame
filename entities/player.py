"""
Player Entity - 玩家实体

管理玩家状态、移动和渲染
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional, Callable
from enum import Enum

import pygame
from pygame.surface import Surface

from config import PLAYER, TILE, Direction
from systems.resource_loader import ResourceLoader, Direction as AnimDirection
from systems.animation import AnimationPlayer


@dataclass
class PlayerStats:
    """玩家属性"""
    level: int = 1
    hp: int = PLAYER.INITIAL_HP
    max_hp: int = PLAYER.INITIAL_HP
    attack: int = PLAYER.INITIAL_ATTACK
    defense: int = PLAYER.INITIAL_DEFENSE
    gold: int = PLAYER.INITIAL_GOLD
    experience: int = PLAYER.INITIAL_EXP
    yellow_keys: int = PLAYER.INITIAL_KEYS[0]
    blue_keys: int = PLAYER.INITIAL_KEYS[1]
    red_keys: int = PLAYER.INITIAL_KEYS[2]
    green_keys: int = 0


class MoveState(Enum):
    """移动状态"""
    IDLE = "idle"
    MOVING = "moving"


@dataclass
class Movement:
    """移动数据"""
    state: MoveState = MoveState.IDLE
    direction: str = Direction.DOWN
    start_x: int = 0
    start_y: int = 0
    target_x: int = 0
    target_y: int = 0
    progress: float = 0.0  # 0.0 - 1.0
    duration: float = PLAYER.MOVE_SPEED


class Player:
    """
    玩家实体

    管理玩家的状态、移动、渲染

    使用示例:
        player = Player(5, 5)  # 在瓦片坐标 (5, 5) 创建玩家
        player.load_resources()

        # 游戏循环中
        player.update(delta_time)
        player.render(screen, offset)

        # 移动
        player.move("up", floor_manager)
    """

    def __init__(self, tile_x: int, tile_y: int):
        """
        初始化玩家

        Args:
            tile_x: 初始瓦片 X 坐标
            tile_y: 初始瓦片 Y 坐标
        """
        # 瓦片坐标
        self._tile_x = tile_x
        self._tile_y = tile_y

        # 玩家属性
        self._stats = PlayerStats()

        # 移动状态
        self._movement = Movement()

        # 动画
        self._animation_player: Optional[AnimationPlayer] = None
        self._facing_direction: str = Direction.DOWN
        self._resources_loaded = False

        # 当前楼层
        self._current_floor: int = 1

    # ============================================================
    # 属性访问
    # ============================================================

    @property
    def tile_x(self) -> int:
        """当前瓦片 X 坐标"""
        return self._tile_x

    @property
    def tile_y(self) -> int:
        """当前瓦片 Y 坐标"""
        return self._tile_y

    @property
    def tile_position(self) -> Tuple[int, int]:
        """当前瓦片坐标"""
        return (self._tile_x, self._tile_y)

    @property
    def stats(self) -> PlayerStats:
        """玩家属性"""
        return self._stats

    @property
    def is_moving(self) -> bool:
        """是否正在移动"""
        return self._movement.state == MoveState.MOVING

    @property
    def facing_direction(self) -> str:
        """面向方向"""
        return self._facing_direction

    @property
    def current_floor(self) -> int:
        """当前楼层"""
        return self._current_floor

    @current_floor.setter
    def current_floor(self, value: int):
        """设置当前楼层"""
        self._current_floor = value

    # ============================================================
    # 资源加载
    # ============================================================

    def load_resources(self) -> bool:
        """
        加载玩家资源

        Returns:
            是否加载成功
        """
        try:
            loader = ResourceLoader("assets/sprites")
            animations = loader.load_entity("playerA")

            self._animation_player = AnimationPlayer(animations)

            # 配置动画
            if "walk" in animations:
                self._animation_player.set_config("walk", frame_duration=0.08, loop=True)
            if "stat" in animations:
                self._animation_player.set_config("stat", frame_duration=0.15, loop=True)

            self._resources_loaded = True

            # 开始播放动画（优先 stat，没有则用 walk）
            if "stat" in animations:
                self._play_animation("stat")
            elif "walk" in animations:
                self._play_animation("walk")

            return True

        except Exception as e:
            print(f"Failed to load player resources: {e}")
            self._resources_loaded = False
            return False

    def _play_animation(self, animation_name: str) -> None:
        """播放动画"""
        if self._animation_player:
            direction = self._direction_to_anim_direction(self._facing_direction)
            self._animation_player.play(animation_name, direction)

    def _set_animation_direction(self) -> None:
        """设置动画方向"""
        if self._animation_player:
            direction = self._direction_to_anim_direction(self._facing_direction)
            self._animation_player.set_direction(direction)

    def _direction_to_anim_direction(self, direction: str) -> AnimDirection:
        """将方向字符串转换为动画方向"""
        mapping = {
            Direction.RIGHT: AnimDirection.RIGHT,
            Direction.UP: AnimDirection.UP,
            Direction.LEFT: AnimDirection.LEFT,
            Direction.DOWN: AnimDirection.DOWN,
        }
        return mapping.get(direction, AnimDirection.DOWN)

    # ============================================================
    # 移动
    # ============================================================

    def move(self, direction: str, floor_manager) -> bool:
        """
        尝试向指定方向移动

        Args:
            direction: 移动方向 ("up", "down", "left", "right")
            floor_manager: 楼层管理器（用于碰撞检测）

        Returns:
            是否可以移动（不一定已经开始移动）
        """
        # 更新朝向
        self._facing_direction = direction
        self._set_animation_direction()

        # 如果正在移动，不处理新移动
        if self.is_moving:
            return False

        # 计算目标位置
        vector = Direction.VECTORS.get(direction, (0, 0))
        target_x = self._tile_x + vector[0]
        target_y = self._tile_y + vector[1]

        # 碰撞检测
        if not floor_manager.is_walkable(target_x, target_y):
            return False

        # 开始移动
        self._movement = Movement(
            state=MoveState.MOVING,
            direction=direction,
            start_x=self._tile_x,
            start_y=self._tile_y,
            target_x=target_x,
            target_y=target_y,
            progress=0.0,
            duration=PLAYER.MOVE_SPEED
        )

        # 播放行走动画
        self._play_animation("walk")

        return True

    def set_position(self, tile_x: int, tile_y: int) -> None:
        """
        直接设置位置（瞬移）

        Args:
            tile_x: 目标 X 坐标
            tile_y: 目标 Y 坐标
        """
        self._tile_x = tile_x
        self._tile_y = tile_y
        self._movement = Movement()

    # ============================================================
    # 更新和渲染
    # ============================================================

    def update(self, delta_time: float) -> None:
        """
        更新玩家状态

        Args:
            delta_time: 时间增量（秒）
        """
        # 更新动画
        if self._animation_player:
            self._animation_player.update(delta_time)

        # 更新移动
        if self.is_moving:
            self._movement.progress += delta_time / self._movement.duration

            if self._movement.progress >= 1.0:
                # 移动完成
                self._tile_x = self._movement.target_x
                self._tile_y = self._movement.target_y
                self._movement = Movement()
                # 播放待机动画
                if self._animation_player and "stat" in self._animation_player.animations:
                    self._play_animation("stat")
                elif self._animation_player and "walk" in self._animation_player.animations:
                    self._play_animation("walk")

    def get_render_position(self, offset: Tuple[int, int] = (0, 0)) -> Tuple[int, int]:
        """
        获取渲染位置（像素坐标）

        Args:
            offset: 地图偏移

        Returns:
            渲染位置
        """
        if self.is_moving:
            # 平滑插值
            t = self._movement.progress
            x = self._movement.start_x + (self._movement.target_x - self._movement.start_x) * t
            y = self._movement.start_y + (self._movement.target_y - self._movement.start_y) * t
        else:
            x = self._tile_x
            y = self._tile_y

        # 转换为像素坐标
        pixel_x = int(x * TILE.SIZE) + offset[0]
        pixel_y = int(y * TILE.SIZE) + offset[1]

        return (pixel_x, pixel_y)

    def render(self, surface: Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """
        渲染玩家

        Args:
            surface: 目标 Surface
            offset: 地图偏移
        """
        # 获取瓦片位置（左上角）
        tile_pos = self.get_render_position(offset)

        if self._animation_player:
            # 动态获取当前帧的 pivot（底部中部）
            pivot_x, pivot_y = self._animation_player.get_pivot()

            # 使用 pivot 偏移：让玩家脚部对齐瓦片中心底部
            # 瓦片中心底部 = (tile_pos + TILE.SIZE/2, tile_pos + TILE.SIZE)
            # 偏移 = 瓦片中心底部 - pivot
            pivot_offset_x = TILE.SIZE // 2 - pivot_x
            pivot_offset_y = TILE.SIZE - pivot_y

            render_pos = (
                tile_pos[0] + pivot_offset_x,
                tile_pos[1] + pivot_offset_y
            )
            self._animation_player.draw(surface, render_pos)
        else:
            # 占位符：绘制一个简单的矩形
            rect = pygame.Rect(
                tile_pos[0],
                tile_pos[1],
                TILE.SIZE,
                TILE.SIZE
            )
            pygame.draw.rect(surface, (100, 200, 100), rect)
            pygame.draw.rect(surface, (50, 150, 50), rect, 2)

    # ============================================================
    # 属性修改
    # ============================================================

    def take_damage(self, damage: int) -> None:
        """
        受到伤害

        Args:
            damage: 伤害值
        """
        self._stats.hp = max(0, self._stats.hp - damage)

    def heal(self, amount: int) -> None:
        """
        治疗

        Args:
            amount: 治疗量
        """
        self._stats.hp = min(self._stats.max_hp, self._stats.hp + amount)

    def add_gold(self, amount: int) -> None:
        """添加金币"""
        self._stats.gold += amount

    def add_experience(self, amount: int) -> None:
        """添加经验"""
        self._stats.experience += amount

    def add_key(self, key_type: str) -> bool:
        """
        添加钥匙

        Args:
            key_type: "yellow", "blue", "red", "green"

        Returns:
            是否成功
        """
        if key_type == "yellow":
            self._stats.yellow_keys += 1
            return True
        elif key_type == "blue":
            self._stats.blue_keys += 1
            return True
        elif key_type == "red":
            self._stats.red_keys += 1
            return True
        elif key_type == "green":
            self._stats.green_keys += 1
            return True
        return False

    def use_key(self, key_type: str) -> bool:
        """
        使用钥匙

        Args:
            key_type: "yellow", "blue", "red", "green"

        Returns:
            是否成功
        """
        if key_type == "yellow" and self._stats.yellow_keys > 0:
            self._stats.yellow_keys -= 1
            return True
        elif key_type == "blue" and self._stats.blue_keys > 0:
            self._stats.blue_keys -= 1
            return True
        elif key_type == "red" and self._stats.red_keys > 0:
            self._stats.red_keys -= 1
            return True
        elif key_type == "green" and self._stats.green_keys > 0:
            self._stats.green_keys -= 1
            return True
        return False

    def has_key(self, key_type: str) -> bool:
        """检查是否有钥匙"""
        if key_type == "yellow":
            return self._stats.yellow_keys > 0
        elif key_type == "blue":
            return self._stats.blue_keys > 0
        elif key_type == "red":
            return self._stats.red_keys > 0
        elif key_type == "green":
            return self._stats.green_keys > 0
        return False

    def is_alive(self) -> bool:
        """是否存活"""
        return self._stats.hp > 0
