"""
UI Base - UI 基础组件

提供基础的 UI 组件类，如面板、文本、图标等
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any, List, Callable
from abc import ABC, abstractmethod

import pygame
from pygame.surface import Surface
from pygame.rect import Rect

from config import COLOR


@dataclass
class UIStyle:
    """UI 样式配置"""
    bg_color: Tuple[int, int, int] = (40, 40, 55)
    border_color: Tuple[int, int, int] = (80, 80, 100)
    text_color: Tuple[int, int, int] = (255, 255, 255)
    highlight_color: Tuple[int, int, int] = (100, 100, 140)
    border_width: int = 2
    border_radius: int = 8
    padding: int = 8


class UIFont:
    """字体管理器"""

    _instance: Optional['UIFont'] = None
    _fonts: Dict[str, pygame.font.Font] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._default_font_path = "assets/fonts/semibold.ttf"

    def get_font(self, size: int = 16, font_path: Optional[str] = None) -> pygame.font.Font:
        """
        获取字体

        Args:
            size: 字体大小
            font_path: 字体路径，None 使用默认字体

        Returns:
            pygame.font.Font 实例
        """
        path = font_path or self._default_font_path
        key = f"{path}_{size}"

        if key not in self._fonts:
            try:
                self._fonts[key] = pygame.font.Font(path, size)
            except Exception:
                # 回退到系统默认字体
                self._fonts[key] = pygame.font.Font(None, size)

        return self._fonts[key]

    def render(self, text: str, size: int = 16, color: Tuple[int, int, int] = (255, 255, 255),
               font_path: Optional[str] = None) -> Surface:
        """
        渲染文本

        Args:
            text: 文本内容
            size: 字体大小
            color: 文本颜色
            font_path: 字体路径

        Returns:
            渲染后的 Surface
        """
        font = self.get_font(size, font_path)
        return font.render(text, True, color)

    def get_text_size(self, text: str, size: int = 16, font_path: Optional[str] = None) -> Tuple[int, int]:
        """获取文本尺寸"""
        font = self.get_font(size, font_path)
        return font.size(text)


class UIComponent(ABC):
    """
    UI 组件基类

    所有 UI 组件的抽象基类
    """

    def __init__(self, x: int, y: int, width: int, height: int, style: Optional[UIStyle] = None):
        """
        初始化 UI 组件

        Args:
            x: X 坐标
            y: Y 坐标
            width: 宽度
            height: 高度
            style: 样式配置
        """
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._style = style or UIStyle()
        self._visible = True
        self._dirty = True  # 需要重绘

    @property
    def rect(self) -> Rect:
        """获取组件矩形区域"""
        return Rect(self._x, self._y, self._width, self._height)

    @property
    def visible(self) -> bool:
        """是否可见"""
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        self._visible = value
        self._dirty = True

    def set_position(self, x: int, y: int) -> None:
        """设置位置"""
        self._x = x
        self._y = y
        self._dirty = True

    def set_size(self, width: int, height: int) -> None:
        """设置尺寸"""
        self._width = width
        self._height = height
        self._dirty = True

    @abstractmethod
    def render(self, surface: Surface) -> None:
        """
        渲染组件

        Args:
            surface: 目标 Surface
        """
        pass

    def update(self, delta_time: float) -> None:
        """
        更新组件

        Args:
            delta_time: 时间增量（秒）
        """
        pass


class Panel(UIComponent):
    """
    面板组件

    一个带边框的矩形面板，可以作为其他组件的容器
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 style: Optional[UIStyle] = None, title: str = ""):
        super().__init__(x, y, width, height, style)
        self._title = title
        self._title_height = 24 if title else 0

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 绘制背景
        pygame.draw.rect(
            surface,
            self._style.bg_color,
            self.rect,
            border_radius=self._style.border_radius
        )

        # 绘制边框
        pygame.draw.rect(
            surface,
            self._style.border_color,
            self.rect,
            width=self._style.border_width,
            border_radius=self._style.border_radius
        )

        # 绘制标题
        if self._title:
            font = UIFont()
            title_surface = font.render(
                self._title,
                size=14,
                color=self._style.highlight_color
            )
            surface.blit(title_surface, (self._x + 8, self._y + 4))


class Label(UIComponent):
    """
    文本标签组件
    """

    def __init__(self, x: int, y: int, text: str = "",
                 font_size: int = 16,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 style: Optional[UIStyle] = None):
        # 计算尺寸
        font = UIFont()
        text_size = font.get_text_size(text, font_size)

        super().__init__(x, y, text_size[0], text_size[1], style)

        self._text = text
        self._font_size = font_size
        self._color = color

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        # 更新尺寸
        font = UIFont()
        text_size = font.get_text_size(value, self._font_size)
        self._width, self._height = text_size
        self._dirty = True

    def render(self, surface: Surface) -> None:
        if not self._visible or not self._text:
            return

        font = UIFont()
        text_surface = font.render(self._text, self._font_size, self._color)
        surface.blit(text_surface, (self._x, self._y))


class IconLabel(UIComponent):
    """
    图标+文本组件
    """

    def __init__(self, x: int, y: int, icon_path: str, text: str = "",
                 font_size: int = 16, icon_size: int = 24,
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 spacing: int = 4):
        self._icon_path = icon_path
        self._icon_size = icon_size
        self._spacing = spacing
        self._text = text
        self._font_size = font_size
        self._text_color = text_color

        # 计算尺寸
        text_width = UIFont().get_text_size(text, font_size)[0] if text else 0
        width = icon_size + spacing + text_width
        height = max(icon_size, font_size)

        super().__init__(x, y, width, height)

        self._icon_surface: Optional[Surface] = None
        self._load_icon()

    def _load_icon(self) -> None:
        """加载图标"""
        try:
            icon = pygame.image.load(self._icon_path)
            self._icon_surface = pygame.transform.scale(icon, (self._icon_size, self._icon_size))
        except Exception:
            self._icon_surface = None

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        # 更新尺寸
        text_width = UIFont().get_text_size(value, self._font_size)[0] if value else 0
        self._width = self._icon_size + self._spacing + text_width
        self._dirty = True

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 绘制图标
        if self._icon_surface:
            surface.blit(self._icon_surface, (self._x, self._y))

        # 绘制文本
        if self._text:
            font = UIFont()
            text_surface = font.render(self._text, self._font_size, self._text_color)
            text_x = self._x + self._icon_size + self._spacing
            text_y = self._y + (self._icon_size - self._font_size) // 2
            surface.blit(text_surface, (text_x, text_y))


class StatBar(UIComponent):
    """
    属性条组件（如血条）
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 current: int = 0, maximum: int = 100,
                 bar_color: Tuple[int, int, int] = (220, 60, 60),
                 bg_color: Tuple[int, int, int] = (60, 30, 30),
                 show_text: bool = True):
        super().__init__(x, y, width, height)

        self._current = current
        self._maximum = maximum
        self._bar_color = bar_color
        self._bg_color = bg_color
        self._show_text = show_text

    @property
    def value(self) -> Tuple[int, int]:
        return (self._current, self._maximum)

    @value.setter
    def value(self, val: Tuple[int, int]):
        self._current, self._maximum = val
        self._dirty = True

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 绘制背景
        pygame.draw.rect(surface, self._bg_color, self.rect, border_radius=3)

        # 绘制当前值
        if self._maximum > 0:
            ratio = self._current / self._maximum
            fill_width = int(self._width * ratio)
            if fill_width > 0:
                fill_rect = Rect(self._x, self._y, fill_width, self._height)
                pygame.draw.rect(surface, self._bar_color, fill_rect, border_radius=3)

        # 绘制文本
        if self._show_text:
            font = UIFont()
            text = f"{self._current}/{self._maximum}"
            text_surface = font.render(text, 12, (255, 255, 255))
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)


class Divider(UIComponent):
    """
    分隔线组件
    """

    def __init__(self, x: int, y: int, width: int, color: Tuple[int, int, int] = (80, 80, 100)):
        super().__init__(x, y, width, 1)
        self._color = color

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        pygame.draw.line(surface, self._color,
                        (self._x, self._y),
                        (self._x + self._width, self._y))


class MessageBox(UIComponent):
    """
    消息框组件

    用于显示提示信息
    """

    def __init__(self, x: int, y: int, width: int,
                 text: str = "", font_size: int = 16,
                 style: Optional[UIStyle] = None):
        self._text = text
        self._font_size = font_size

        # 计算高度
        font = UIFont()
        lines = text.split('\n') if text else ['']
        line_height = font_size + 4
        height = len(lines) * line_height + 16

        super().__init__(x, y, width, height, style)

    def set_text(self, text: str) -> None:
        """设置文本"""
        self._text = text
        # 更新高度
        font = UIFont()
        lines = text.split('\n') if text else ['']
        line_height = self._font_size + 4
        self._height = len(lines) * line_height + 16
        self._dirty = True

    def render(self, surface: Surface) -> None:
        if not self._visible or not self._text:
            return

        # 绘制背景
        pygame.draw.rect(surface, self._style.bg_color, self.rect, border_radius=4)
        pygame.draw.rect(surface, self._style.border_color, self.rect, width=1, border_radius=4)

        # 绘制文本
        font = UIFont()
        lines = self._text.split('\n')
        line_height = self._font_size + 4

        for i, line in enumerate(lines):
            text_surface = font.render(line, self._font_size, self._style.text_color)
            surface.blit(text_surface, (self._x + 8, self._y + 8 + i * line_height))


# 全局字体管理器实例
ui_font = UIFont()
