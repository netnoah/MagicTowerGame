"""
Tile System - 瓦片系统

定义瓦片类型、加载瓦片资源、管理瓦片渲染
"""

from enum import Enum, auto
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import pygame
from pygame.surface import Surface

from config import PATH, TILE


class TileType(Enum):
    """瓦片类型枚举"""
    # 基础地形
    EMPTY = 0        # 空白（不可见）
    FLOOR = auto()   # 地板（可行走）
    WALL = auto()    # 墙壁（不可通行）

    # 门
    DOOR_YELLOW = auto()  # 黄门（需要黄钥匙）
    DOOR_BLUE = auto()    # 蓝门（需要蓝钥匙）
    DOOR_RED = auto()     # 红门（需要红钥匙）
    DOOR_GREEN = auto()   # 绿门（需要绿钥匙）

    # 楼梯
    STAIRS_UP = auto()    # 上楼楼梯
    STAIRS_DOWN = auto()  # 下楼楼梯

    # 功能建筑
    SHOP = auto()         # 商店
    NPC = auto()          # NPC
    FOUNTAIN = auto()     # 泉水（恢复HP）
    ALTAR = auto()        # 祭坛（属性提升）

    # 特殊
    SECRET_WALL = auto()  # 暗墙（可用道具打破）
    TELEPORT = auto()     # 传送点
    TRAP = auto()         # 陷阱


@dataclass(frozen=True)
class TileProperties:
    """瓦片属性"""
    walkable: bool = False       # 是否可行走
    interactive: bool = False    # 是否可交互
    blocks_view: bool = True     # 是否阻挡视线
    requires_key: Optional[str] = None  # 需要的钥匙类型


# 瓦片类型到属性的映射
TILE_PROPERTIES: Dict[TileType, TileProperties] = {
    TileType.EMPTY: TileProperties(walkable=False, interactive=False, blocks_view=False),
    TileType.FLOOR: TileProperties(walkable=True, interactive=False, blocks_view=False),
    TileType.WALL: TileProperties(walkable=False, interactive=False, blocks_view=True),
    TileType.DOOR_YELLOW: TileProperties(walkable=True, interactive=True, blocks_view=True, requires_key="yellow"),
    TileType.DOOR_BLUE: TileProperties(walkable=True, interactive=True, blocks_view=True, requires_key="blue"),
    TileType.DOOR_RED: TileProperties(walkable=True, interactive=True, blocks_view=True, requires_key="red"),
    TileType.DOOR_GREEN: TileProperties(walkable=True, interactive=True, blocks_view=True, requires_key="green"),
    TileType.STAIRS_UP: TileProperties(walkable=True, interactive=True, blocks_view=False),
    TileType.STAIRS_DOWN: TileProperties(walkable=True, interactive=True, blocks_view=False),
    TileType.SHOP: TileProperties(walkable=True, interactive=True, blocks_view=False),
    TileType.NPC: TileProperties(walkable=True, interactive=True, blocks_view=False),
    TileType.FOUNTAIN: TileProperties(walkable=True, interactive=True, blocks_view=False),
    TileType.ALTAR: TileProperties(walkable=True, interactive=True, blocks_view=False),
    TileType.SECRET_WALL: TileProperties(walkable=False, interactive=True, blocks_view=True),
    TileType.TELEPORT: TileProperties(walkable=True, interactive=True, blocks_view=False),
    TileType.TRAP: TileProperties(walkable=True, interactive=True, blocks_view=False),
}


class TileManager:
    """
    瓦片管理器

    负责加载和管理瓦片精灵

    使用示例:
        tile_manager = TileManager()
        tile_manager.load_tiles()

        # 获取瓦片图片
        floor_surface = tile_manager.get_tile_surface(TileType.FLOOR)

        # 绘制瓦片
        tile_manager.draw_tile(screen, TileType.FLOOR, (100, 100))
    """

    # 瓦片类型到文件名的映射
    TILE_FILES = {
        TileType.FLOOR: "floor.png",
        TileType.WALL: "wall.png",
        TileType.DOOR_YELLOW: "door_yellow.png",
        TileType.DOOR_BLUE: "door_blue.png",
        TileType.DOOR_RED: "door_red.png",
        TileType.DOOR_GREEN: "door_green.png",
        TileType.STAIRS_UP: "stairs_up.png",
        TileType.STAIRS_DOWN: "stairs_down.png",
        TileType.SHOP: "shop.png",
    }

    def __init__(self, tiles_dir: str = None, tile_size: int = None):
        """
        初始化瓦片管理器

        Args:
            tiles_dir: 瓦片资源目录
            tile_size: 瓦片尺寸
        """
        self._tiles_dir = Path(tiles_dir or f"{PATH.SPRITES_DIR}/tiles")
        self._tile_size = tile_size or TILE.SIZE

        # 瓦片表面缓存
        self._tile_surfaces: Dict[TileType, Surface] = {}

        # 是否已加载
        self._loaded = False

    def load_tiles(self) -> None:
        """
        加载所有瓦片资源

        如果资源不存在，创建占位符
        """
        for tile_type, filename in self.TILE_FILES.items():
            file_path = self._tiles_dir / filename

            if file_path.exists():
                # 加载实际图片
                surface = pygame.image.load(str(file_path)).convert_alpha()
                # 缩放到目标尺寸
                if surface.get_size() != (self._tile_size, self._tile_size):
                    surface = pygame.transform.scale(
                        surface,
                        (self._tile_size, self._tile_size)
                    )
                self._tile_surfaces[tile_type] = surface
            else:
                # 创建占位符
                self._tile_surfaces[tile_type] = self._create_placeholder(tile_type)

        self._loaded = True

    def _create_placeholder(self, tile_type: TileType) -> Surface:
        """
        创建瓦片占位符

        Args:
            tile_type: 瓦片类型

        Returns:
            占位符 Surface
        """
        surface = Surface((self._tile_size, self._tile_size))

        # 根据类型设置不同颜色
        colors = {
            TileType.FLOOR: (60, 60, 70),
            TileType.WALL: (100, 100, 120),
            TileType.DOOR_YELLOW: (200, 200, 50),
            TileType.DOOR_BLUE: (50, 50, 200),
            TileType.DOOR_RED: (200, 50, 50),
            TileType.DOOR_GREEN: (50, 200, 50),
            TileType.STAIRS_UP: (100, 200, 100),
            TileType.STAIRS_DOWN: (200, 100, 100),
            TileType.SHOP: (200, 150, 50),
        }

        color = colors.get(tile_type, (128, 128, 128))
        surface.fill(color)

        # 绘制边框
        pygame.draw.rect(surface, (50, 50, 50), surface.get_rect(), 1)

        return surface

    def get_tile_surface(self, tile_type: TileType) -> Optional[Surface]:
        """
        获取瓦片表面

        Args:
            tile_type: 瓦片类型

        Returns:
            瓦片 Surface，如果不存在返回 None
        """
        if not self._loaded:
            self.load_tiles()

        return self._tile_surfaces.get(tile_type)

    def draw_tile(self,
                  surface: Surface,
                  tile_type: TileType,
                  position: Tuple[int, int]) -> None:
        """
        绘制瓦片

        Args:
            surface: 目标表面
            tile_type: 瓦片类型
            position: 绘制位置（像素坐标）
        """
        tile_surface = self.get_tile_surface(tile_type)
        if tile_surface:
            surface.blit(tile_surface, position)

    def get_tile_properties(self, tile_type: TileType) -> TileProperties:
        """
        获取瓦片属性

        Args:
            tile_type: 瓦片类型

        Returns:
            瓦片属性
        """
        return TILE_PROPERTIES.get(tile_type, TileProperties())

    def is_walkable(self, tile_type: TileType) -> bool:
        """检查瓦片是否可行走"""
        props = self.get_tile_properties(tile_type)
        return props.walkable

    def is_interactive(self, tile_type: TileType) -> bool:
        """检查瓦片是否可交互"""
        props = self.get_tile_properties(tile_type)
        return props.interactive

    @property
    def tile_size(self) -> int:
        """瓦片尺寸"""
        return self._tile_size

    @property
    def is_loaded(self) -> bool:
        """是否已加载"""
        return self._loaded


def tile_coords_to_pixels(tile_x: int, tile_y: int, tile_size: int = None) -> Tuple[int, int]:
    """
    将瓦片坐标转换为像素坐标

    Args:
        tile_x: 瓦片 X 坐标
        tile_y: 瓦片 Y 坐标
        tile_size: 瓦片尺寸

    Returns:
        像素坐标 (x, y)
    """
    size = tile_size or TILE.SIZE
    return (tile_x * size, tile_y * size)


def pixels_to_tile_coords(pixel_x: int, pixel_y: int, tile_size: int = None) -> Tuple[int, int]:
    """
    将像素坐标转换为瓦片坐标

    Args:
        pixel_x: 像素 X 坐标
        pixel_y: 像素 Y 坐标
        tile_size: 瓦片尺寸

    Returns:
        瓦片坐标 (x, y)
    """
    size = tile_size or TILE.SIZE
    return (pixel_x // size, pixel_y // size)
