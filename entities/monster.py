"""
Monster Entity - 怪物实体

管理怪物状态和渲染
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import json
from pathlib import Path

import pygame
from pygame.surface import Surface

from config import TILE
from systems.resource_loader import ResourceLoader, Direction
from systems.animation import AnimationPlayer


@dataclass
class MonsterStats:
    """怪物属性"""
    monster_id: str = ""
    name: str = ""
    name_cn: str = ""
    hp: int = 0
    attack: int = 0
    defense: int = 0
    gold: int = 0
    experience: int = 0


class MonsterManager:
    """
    怪物管理器

    负责加载怪物数据和创建怪物实例

    使用示例:
        manager = MonsterManager()
        manager.load_monster_data("data/entities/monsters.json")

        monster = manager.create_monster("slime_green", 5, 3)
    """

    def __init__(self, data_path: str = None):
        """
        初始化怪物管理器

        Args:
            data_path: 怪物数据文件路径
        """
        self._data_path = Path(data_path) if data_path else None
        self._monster_data: Dict[str, Dict[str, Any]] = {}

    def load_monster_data(self, file_path: str = None) -> bool:
        """
        加载怪物数据

        Args:
            file_path: 数据文件路径

        Returns:
            是否加载成功
        """
        path = Path(file_path) if file_path else self._data_path
        if not path or not path.exists():
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._monster_data = data.get('monsters', {})
            return True
        except Exception as e:
            print(f"Error loading monster data: {e}")
            return False

    def get_monster_data(self, monster_id: str) -> Optional[Dict[str, Any]]:
        """获取怪物数据"""
        return self._monster_data.get(monster_id)

    def get_all_monster_ids(self) -> list:
        """获取所有怪物ID"""
        return list(self._monster_data.keys())


class Monster:
    """
    怪物实体

    管理单个怪物的状态和渲染

    使用示例:
        monster = Monster("slime_green", 5, 3, monster_data)
        monster.load_resources()

        # 游戏循环中
        monster.update(delta_time)
        monster.render(screen, offset)
    """

    def __init__(self, monster_id: str, tile_x: int, tile_y: int,
                 monster_data: Dict[str, Any] = None):
        """
        初始化怪物

        Args:
            monster_id: 怪物ID
            tile_x: 瓦片 X 坐标
            tile_y: 瓦片 Y 坐标
            monster_data: 怪物数据（如果为 None，需要后续设置）
        """
        self._monster_id = monster_id
        self._tile_x = tile_x
        self._tile_y = tile_y
        self._alive = True

        # 怪物属性
        if monster_data:
            self._stats = MonsterStats(
                monster_id=monster_id,
                name=monster_data.get('name', ''),
                name_cn=monster_data.get('name_cn', ''),
                hp=monster_data.get('hp', 0),
                attack=monster_data.get('attack', 0),
                defense=monster_data.get('defense', 0),
                gold=monster_data.get('gold', 0),
                experience=monster_data.get('experience', 0)
            )
            self._sprite_name = monster_data.get('sprite', monster_id)
        else:
            self._stats = MonsterStats(monster_id=monster_id)
            self._sprite_name = monster_id

        # 动画
        self._animation_player: Optional[AnimationPlayer] = None
        self._resources_loaded = False

    # ============================================================
    # 属性访问
    # ============================================================

    @property
    def monster_id(self) -> str:
        """怪物ID"""
        return self._monster_id

    @property
    def tile_x(self) -> int:
        """瓦片 X 坐标"""
        return self._tile_x

    @property
    def tile_y(self) -> int:
        """瓦片 Y 坐标"""
        return self._tile_y

    @property
    def tile_position(self) -> Tuple[int, int]:
        """瓦片坐标"""
        return (self._tile_x, self._tile_y)

    @property
    def stats(self) -> MonsterStats:
        """怪物属性"""
        return self._stats

    @property
    def is_alive(self) -> bool:
        """是否存活"""
        return self._alive

    # ============================================================
    # 资源加载
    # ============================================================

    def load_resources(self, sprite_path: str = "assets/sprites/monsters") -> bool:
        """
        加载怪物资源

        Args:
            sprite_path: 精灵资源路径

        Returns:
            是否加载成功
        """
        try:
            loader = ResourceLoader(sprite_path)
            # 怪物不缩放，保持原始大小
            animations = loader.load_entity(self._sprite_name, scale=False)

            self._animation_player = AnimationPlayer(animations)

            # 配置动画（怪物默认面向右边）
            if "idle" in animations:
                self._animation_player.set_config("idle", frame_duration=0.15, loop=True)
                self._animation_player.play("idle", Direction.RIGHT)
            elif "walk" in animations:
                self._animation_player.set_config("walk", frame_duration=0.15, loop=True)
                self._animation_player.play("walk", Direction.RIGHT)

            self._resources_loaded = True
            return True

        except Exception as e:
            print(f"Failed to load monster resources ({self._sprite_name}): {e}")
            self._resources_loaded = False
            return False

    # ============================================================
    # 更新和渲染
    # ============================================================

    def update(self, delta_time: float) -> None:
        """
        更新怪物状态

        Args:
            delta_time: 时间增量（秒）
        """
        if self._animation_player:
            self._animation_player.update(delta_time)

    def render(self, surface: Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """
        渲染怪物

        Args:
            surface: 目标 Surface
            offset: 地图偏移
        """
        if not self._alive:
            return

        # 计算渲染位置
        pixel_x = self._tile_x * TILE.SIZE + offset[0]
        pixel_y = self._tile_y * TILE.SIZE + offset[1]

        if self._animation_player:
            # 获取动态 pivot
            pivot_x, pivot_y = self._animation_player.get_pivot()

            # 使用 pivot 偏移
            pivot_offset_x = TILE.SIZE // 2 - pivot_x
            pivot_offset_y = TILE.SIZE - pivot_y

            render_pos = (
                pixel_x + pivot_offset_x,
                pixel_y + pivot_offset_y
            )
            self._animation_player.draw(surface, render_pos)
        else:
            # 占位符 - 更明显的颜色
            rect = pygame.Rect(pixel_x, pixel_y, TILE.SIZE, TILE.SIZE)
            pygame.draw.rect(surface, (255, 100, 100), rect)  # 亮红色填充
            pygame.draw.rect(surface, (200, 50, 50), rect, 2)  # 深红边框

    # ============================================================
    # 战斗相关
    # ============================================================

    def kill(self) -> None:
        """击杀怪物"""
        self._alive = False
