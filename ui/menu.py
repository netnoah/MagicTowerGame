"""
Menu - 菜单系统

提供主菜单、暂停菜单等界面
"""

from dataclasses import dataclass
from typing import Optional, List, Callable, Tuple

import pygame
from pygame.surface import Surface
from pygame.rect import Rect

from ui.base import UIComponent, UIStyle, UIFont


@dataclass
class MenuItem:
    """菜单项"""
    text: str
    action: Optional[Callable] = None
    enabled: bool = True


class Menu(UIComponent):
    """
    菜单组件

    显示一个带选项的菜单
    """

    def __init__(self, x: int, y: int, width: int,
                 title: str = "",
                 items: Optional[List[MenuItem]] = None,
                 style: Optional[UIStyle] = None):
        # 计算高度
        self._title = title
        self._items = items or []
        self._selected_index = 0
        self._item_height = 36

        # 计算总高度
        title_height = 50 if title else 0
        items_height = len(self._items) * self._item_height if self._items else 100
        height = title_height + items_height + 40

        super().__init__(x - width // 2, y - height // 2, width, height, style)

        self._style = style or UIStyle(
            bg_color=(35, 35, 50),
            border_color=(100, 100, 140),
            text_color=(220, 220, 220),
            highlight_color=(255, 200, 100),
            border_width=2,
            border_radius=12
        )

        self._select_color = (60, 60, 80)
        self._disabled_color = (100, 100, 100)

    def add_item(self, text: str, action: Optional[Callable] = None,
                 enabled: bool = True) -> None:
        """添加菜单项"""
        self._items.append(MenuItem(text, action, enabled))
        # 更新高度
        title_height = 50 if self._title else 0
        items_height = len(self._items) * self._item_height
        self._height = title_height + items_height + 40

    def select_next(self) -> None:
        """选择下一个菜单项"""
        for i in range(1, len(self._items)):
            idx = (self._selected_index + i) % len(self._items)
            if self._items[idx].enabled:
                self._selected_index = idx
                break

    def select_prev(self) -> None:
        """选择上一个菜单项"""
        for i in range(1, len(self._items)):
            idx = (self._selected_index - i) % len(self._items)
            if self._items[idx].enabled:
                self._selected_index = idx
                break

    def confirm(self) -> Optional[Callable]:
        """确认当前选择"""
        if self._items and self._selected_index < len(self._items):
            item = self._items[self._selected_index]
            if item.enabled and item.action:
                return item.action
        return None

    @property
    def selected_index(self) -> int:
        return self._selected_index

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

        font = UIFont()
        y = self._y + 20
        x = self._x + 20
        content_width = self._width - 40

        # 绘制标题
        if self._title:
            title_surface = font.render(self._title, 28, self._style.highlight_color)
            title_x = self._x + (self._width - title_surface.get_width()) // 2
            surface.blit(title_surface, (title_x, y))
            y += 50

            # 分隔线
            pygame.draw.line(
                surface,
                self._style.border_color,
                (x, y),
                (x + content_width, y)
            )
            y += 16

        # 绘制菜单项
        for i, item in enumerate(self._items):
            item_rect = Rect(x - 5, y - 4, content_width + 10, self._item_height)

            # 选中高亮
            if i == self._selected_index:
                pygame.draw.rect(
                    surface,
                    self._select_color,
                    item_rect,
                    border_radius=6
                )

            # 文本
            if item.enabled:
                color = self._style.highlight_color if i == self._selected_index else self._style.text_color
            else:
                color = self._disabled_color

            text_surface = font.render(item.text, 18, color)
            text_x = self._x + (self._width - text_surface.get_width()) // 2
            surface.blit(text_surface, (text_x, y + 4))

            y += self._item_height


class MainMenu(UIComponent):
    """
    主菜单界面

    游戏启动时显示的主菜单
    """

    def __init__(self, width: int, height: int):
        super().__init__(0, 0, width, height)

        self._style = UIStyle(
            bg_color=(25, 25, 40),
            border_color=(80, 80, 100),
            text_color=(220, 220, 220),
            highlight_color=(255, 200, 100)
        )

        # 菜单项
        self._menu_items = [
            {"text": "New Game", "key": "new_game"},
            {"text": "Continue", "key": "continue"},
            {"text": "Quit", "key": "quit"}
        ]
        self._selected_index = 0

        # 动画
        self._time = 0.0

    def select_next(self) -> None:
        self._selected_index = (self._selected_index + 1) % len(self._menu_items)

    def select_prev(self) -> None:
        self._selected_index = (self._selected_index - 1) % len(self._menu_items)

    @property
    def selected_action(self) -> str:
        return self._menu_items[self._selected_index]["key"]

    def update(self, delta_time: float) -> None:
        self._time += delta_time

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 背景
        surface.fill(self._style.bg_color)

        font = UIFont()
        center_x = self._width // 2
        center_y = self._height // 2

        # 标题
        title = "MAGIC TOWER"
        # 标题动画效果
        offset = int(pygame.time.get_ticks() / 500) % 2
        title_color = (255, 200 + offset * 30, 100)

        title_surface = font.render(title, 48, title_color)
        title_rect = title_surface.get_rect(center=(center_x, center_y - 100))
        surface.blit(title_surface, title_rect)

        # 副标题
        subtitle = "A Classic Adventure"
        subtitle_surface = font.render(subtitle, 16, (150, 150, 180))
        subtitle_rect = subtitle_surface.get_rect(center=(center_x, center_y - 50))
        surface.blit(subtitle_surface, subtitle_rect)

        # 菜单项
        menu_y = center_y + 20
        for i, item in enumerate(self._menu_items):
            if i == self._selected_index:
                # 选中项高亮
                text = f"> {item['text']} <"
                color = self._style.highlight_color
            else:
                text = f"  {item['text']}  "
                color = self._style.text_color

            text_surface = font.render(text, 24, color)
            text_rect = text_surface.get_rect(center=(center_x, menu_y))
            surface.blit(text_surface, text_rect)

            menu_y += 45

        # 提示
        hint = "Press UP/DOWN to select, ENTER to confirm"
        hint_surface = font.render(hint, 14, (100, 100, 120))
        hint_rect = hint_surface.get_rect(center=(center_x, self._height - 40))
        surface.blit(hint_surface, hint_rect)


class PauseMenu(UIComponent):
    """
    暂停菜单

    游戏暂停时显示的菜单
    """

    def __init__(self, width: int, height: int):
        super().__init__(0, 0, width, height)

        self._style = UIStyle(
            bg_color=(35, 35, 50),
            border_color=(100, 100, 140),
            text_color=(220, 220, 220),
            highlight_color=(255, 200, 100),
            border_radius=12
        )

        self._menu_items = [
            {"text": "Resume", "key": "resume"},
            {"text": "Main Menu", "key": "main_menu"},
            {"text": "Quit", "key": "quit"}
        ]
        self._selected_index = 0

    def select_next(self) -> None:
        self._selected_index = (self._selected_index + 1) % len(self._menu_items)

    def select_prev(self) -> None:
        self._selected_index = (self._selected_index - 1) % len(self._menu_items)

    @property
    def selected_action(self) -> str:
        return self._menu_items[self._selected_index]["key"]

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 半透明背景
        overlay = Surface((self._width, self._height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        font = UIFont()
        center_x = self._width // 2
        center_y = self._height // 2

        # 菜单面板
        panel_width = 280
        panel_height = 250
        panel_x = center_x - panel_width // 2
        panel_y = center_y - panel_height // 2
        panel_rect = Rect(panel_x, panel_y, panel_width, panel_height)

        pygame.draw.rect(
            surface,
            self._style.bg_color,
            panel_rect,
            border_radius=self._style.border_radius
        )
        pygame.draw.rect(
            surface,
            self._style.border_color,
            panel_rect,
            width=2,
            border_radius=self._style.border_radius
        )

        # 标题
        title = "PAUSED"
        title_surface = font.render(title, 32, self._style.highlight_color)
        title_rect = title_surface.get_rect(center=(center_x, panel_y + 40))
        surface.blit(title_surface, title_rect)

        # 菜单项
        menu_y = panel_y + 90
        for i, item in enumerate(self._menu_items):
            if i == self._selected_index:
                text = f"> {item['text']}"
                color = self._style.highlight_color
            else:
                text = f"  {item['text']}"
                color = self._style.text_color

            text_surface = font.render(text, 20, color)
            text_rect = text_surface.get_rect(center=(center_x, menu_y))
            surface.blit(text_surface, text_rect)

            menu_y += 40

        # 提示
        hint = "Press ESC to resume"
        hint_surface = font.render(hint, 14, (100, 100, 120))
        hint_rect = hint_surface.get_rect(center=(center_x, panel_y + panel_height - 25))
        surface.blit(hint_surface, hint_rect)


class GameOverScreen(UIComponent):
    """
    游戏结束界面
    """

    def __init__(self, width: int, height: int, victory: bool = False):
        super().__init__(0, 0, width, height)

        self._victory = victory

        self._style = UIStyle(
            bg_color=(35, 35, 50),
            text_color=(220, 220, 220),
            highlight_color=(255, 200, 100)
        )

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 半透明背景
        overlay = Surface((self._width, self._height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        font = UIFont()
        center_x = self._width // 2
        center_y = self._height // 2

        # 标题
        if self._victory:
            title = "VICTORY!"
            title_color = (100, 255, 100)
        else:
            title = "GAME OVER"
            title_color = (255, 100, 100)

        title_surface = font.render(title, 48, title_color)
        title_rect = title_surface.get_rect(center=(center_x, center_y - 30))
        surface.blit(title_surface, title_rect)

        # 提示
        hint = "Press ENTER to continue"
        hint_surface = font.render(hint, 18, self._style.text_color)
        hint_rect = hint_surface.get_rect(center=(center_x, center_y + 40))
        surface.blit(hint_surface, hint_rect)
