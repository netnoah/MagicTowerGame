"""
Display Manager - 显示管理

负责窗口创建、渲染、相机系统
"""

from typing import Optional, Tuple
from dataclasses import dataclass

import pygame
from pygame.surface import Surface
from pygame.rect import Rect

from config import WindowConfig, ColorConfig


@dataclass
class Camera:
    """相机配置"""
    x: float = 0.0
    y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    smoothing: float = 0.1  # 相机跟随平滑度 (0-1, 越小越平滑)


class DisplayManager:
    """
    显示管理器

    管理窗口、渲染和相机

    使用示例:
        display = DisplayManager()

        # 清屏
        display.clear()

        # 绘制
        display.draw(sprite, (100, 100))

        # 更新显示
        display.present()
    """

    def __init__(self,
                 width: int = WindowConfig.WIDTH,
                 height: int = WindowConfig.HEIGHT,
                 title: str = WindowConfig.TITLE,
                 fullscreen: bool = False):
        """
        初始化显示管理器

        Args:
            width: 窗口宽度
            height: 窗口高度
            title: 窗口标题
            fullscreen: 是否全屏
        """
        pygame.init()

        # 设置显示模式
        if fullscreen:
            self._screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self._width = self._screen.get_width()
            self._height = self._screen.get_height()
        else:
            self._screen = pygame.display.set_mode((width, height))
            self._width = width
            self._height = height

        pygame.display.set_caption(title)

        # 创建渲染表面（用于缩放）
        self._render_surface = Surface((width, height))
        self._scale = 1.0

        # 相机
        self._camera = Camera()

        # 背景色
        self._background_color = WindowConfig.BACKGROUND_COLOR

        # 字体缓存
        self._fonts: dict[str, pygame.font.Font] = {}

    # ============================================================
    # 属性
    # ============================================================

    @property
    def width(self) -> int:
        """窗口宽度"""
        return self._width

    @property
    def height(self) -> int:
        """窗口高度"""
        return self._height

    @property
    def screen(self) -> Surface:
        """主屏幕 Surface"""
        return self._screen

    @property
    def render_surface(self) -> Surface:
        """渲染 Surface（相机变换前的表面）"""
        return self._render_surface

    @property
    def camera(self) -> Camera:
        """相机配置"""
        return self._camera

    # ============================================================
    # 渲染方法
    # ============================================================

    def clear(self, color: Optional[Tuple[int, int, int]] = None) -> None:
        """
        清屏

        Args:
            color: 背景色，默认使用配置的颜色
        """
        bg_color = color or self._background_color
        self._render_surface.fill(bg_color)

    def draw(self,
            surface: Surface,
            position: Tuple[int, int],
            camera_offset: bool = True) -> None:
        """
        绘制 Surface 到渲染表面

        Args:
            surface: 要绘制的 Surface
            position: 绘制位置
            camera_offset: 是否应用相机偏移
        """
        if camera_offset:
            x = position[0] - self._camera.x
            y = position[1] - self._camera.y
        else:
            x, y = position

        self._render_surface.blit(surface, (x, y))

    def draw_rect(self,
                  rect: Rect,
                  color: Tuple[int, int, int],
                  width: int = 0) -> None:
        """
        绘制矩形

        Args:
            rect: 矩形区域
            color: 颜色
            width: 边框宽度，0 表示填充
        """
        pygame.draw.rect(self._render_surface, color, rect, width)

    def draw_text(self,
                  text: str,
                  position: Tuple[int, int],
                  font_size: int = 24,
                  color: Tuple[int, int, int] = ColorConfig.WHITE,
                  font_name: Optional[str] = None,
                  camera_offset: bool = False) -> None:
        """
        绘制文本

        Args:
            text: 文本内容
            position: 位置
            font_size: 字体大小
            color: 颜色
            font_name: 字体名称（None 使用默认字体）
            camera_offset: 是否应用相机偏移
        """
        font = self._get_font(font_name, font_size)
        text_surface = font.render(text, True, color)

        if camera_offset:
            x = position[0] - self._camera.x
            y = position[1] - self._camera.y
        else:
            x, y = position

        self._render_surface.blit(text_surface, (x, y))

    def present(self) -> None:
        """
        将渲染表面呈现到屏幕

        应该在每帧绘制的最后调用
        """
        if self._scale != 1.0:
            # 缩放渲染表面到屏幕大小
            scaled = pygame.transform.scale(
                self._render_surface,
                (self._width, self._height)
            )
            self._screen.blit(scaled, (0, 0))
        else:
            self._screen.blit(self._render_surface, (0, 0))

        pygame.display.flip()

    # ============================================================
    # 相机方法
    # ============================================================

    def set_camera_target(self, x: float, y: float) -> None:
        """
        设置相机目标位置

        相机会平滑跟随到目标位置

        Args:
            x: 目标 X 坐标
            y: 目标 Y 坐标
        """
        self._camera.target_x = x - self._width / 2
        self._camera.target_y = y - self._height / 2

    def update_camera(self, delta_time: float) -> None:
        """
        更新相机位置

        Args:
            delta_time: 时间增量（秒）
        """
        # 平滑跟随
        self._camera.x += (self._camera.target_x - self._camera.x) * self._camera.smoothing
        self._camera.y += (self._camera.target_y - self._camera.y) * self._camera.smoothing

    def reset_camera(self) -> None:
        """重置相机位置"""
        self._camera.x = 0
        self._camera.y = 0
        self._camera.target_x = 0
        self._camera.target_y = 0

    # ============================================================
    # 工具方法
    # ============================================================

    def _get_font(self, font_name: Optional[str], size: int) -> pygame.font.Font:
        """获取或创建字体"""
        key = f"{font_name or 'default'}_{size}"
        if key not in self._fonts:
            if font_name:
                try:
                    self._fonts[key] = pygame.font.Font(font_name, size)
                except:
                    self._fonts[key] = pygame.font.Font(None, size)
            else:
                self._fonts[key] = pygame.font.Font(None, size)
        return self._fonts[key]

    def screen_to_world(self, screen_pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        将屏幕坐标转换为世界坐标

        Args:
            screen_pos: 屏幕坐标

        Returns:
            世界坐标
        """
        return (
            int(screen_pos[0] + self._camera.x),
            int(screen_pos[1] + self._camera.y)
        )

    def world_to_screen(self, world_pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        将世界坐标转换为屏幕坐标

        Args:
            world_pos: 世界坐标

        Returns:
            屏幕坐标
        """
        return (
            int(world_pos[0] - self._camera.x),
            int(world_pos[1] - self._camera.y)
        )

    def get_center(self) -> Tuple[int, int]:
        """获取渲染表面中心点"""
        return (self._width // 2, self._height // 2)

    def quit(self) -> None:
        """清理资源"""
        self._fonts.clear()
