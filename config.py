"""
Config - 游戏全局配置

所有游戏常量和配置项集中管理
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class WindowConfig:
    """窗口配置"""
    WIDTH: int = 800
    HEIGHT: int = 600
    TITLE: str = "Magic Tower"
    FPS: int = 60
    BACKGROUND_COLOR: Tuple[int, int, int] = (30, 30, 40)


@dataclass(frozen=True)
class TileConfig:
    """瓦片配置"""
    SIZE: int = 32  # 每个瓦片的像素尺寸

    # 地图尺寸（瓦片数）- 刚好填充 800x600 窗口
    MAP_WIDTH: int = 25   # 25 * 32 = 800
    MAP_HEIGHT: int = 19  # 19 * 32 = 608 (略高于 600，向上取整)


@dataclass(frozen=True)
class PlayerConfig:
    """玩家配置"""
    INITIAL_HP: int = 1000
    INITIAL_ATTACK: int = 10
    INITIAL_DEFENSE: int = 10
    INITIAL_GOLD: int = 0
    INITIAL_EXP: int = 0
    INITIAL_KEYS: Tuple[int, int, int] = (0, 0, 0)  # (yellow, blue, red)
    MOVE_SPEED: float = 0.15  # 移动动画持续时间（秒）


@dataclass(frozen=True)
class PathConfig:
    """路径配置"""
    ASSETS_DIR: str = "assets"
    SPRITES_DIR: str = "assets/sprites"
    MAPS_DIR: str = "data/maps"
    SAVES_DIR: str = "data/saves"
    FONTS_DIR: str = "assets/fonts"


@dataclass(frozen=True)
class ColorConfig:
    """颜色配置"""
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    RED: Tuple[int, int, int] = (255, 80, 80)
    GREEN: Tuple[int, int, int] = (80, 255, 80)
    BLUE: Tuple[int, int, int] = (80, 80, 255)
    YELLOW: Tuple[int, int, int] = (255, 255, 80)
    GRAY: Tuple[int, int, int] = (128, 128, 128)
    DARK_GRAY: Tuple[int, int, int] = (64, 64, 64)

    # UI 颜色
    HUD_BG: Tuple[int, int, int] = (40, 40, 50)
    HUD_BORDER: Tuple[int, int, int] = (80, 80, 100)
    HP_BAR: Tuple[int, int, int] = (220, 60, 60)
    HP_BAR_BG: Tuple[int, int, int] = (60, 30, 30)
    GOLD_COLOR: Tuple[int, int, int] = (255, 215, 0)


# 全局配置实例
WINDOW = WindowConfig()
TILE = TileConfig()
PLAYER = PlayerConfig()
PATH = PathConfig()
COLOR = ColorConfig()


# 游戏状态枚举
class GameState:
    """游戏状态"""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    DIALOG = "dialog"
    SHOP = "shop"
    COMBAT = "combat"
    GAME_OVER = "game_over"
    VICTORY = "victory"


# 方向枚举（与 systems/resource_loader.py 保持一致）
class Direction:
    """四个方向"""
    RIGHT = "right"
    UP = "up"
    LEFT = "left"
    DOWN = "down"

    # 方向对应的移动向量
    VECTORS = {
        "right": (1, 0),
        "up": (0, -1),
        "left": (-1, 0),
        "down": (0, 1),
    }
