"""
Shop UI - 商店界面

提供商店购买、属性升级的UI界面
"""

from typing import Optional, List, Callable, Tuple
from dataclasses import dataclass

import pygame
from pygame.surface import Surface
from pygame.rect import Rect

from ui.base import UIComponent, UIStyle, UIFont, Panel, Label
from systems.shop import ShopData, ShopItem, ShopUpgrade
from entities.player import PlayerStats
from config import COLOR


@dataclass
class ShopEntry:
    """商店条目（用于UI显示）"""
    display_name: str      # 显示名称
    description: str       # 描述
    price: int             # 价格
    entry_type: str        # 类型: "item" 或 "upgrade"
    data: any              # 原始数据 (ShopItem 或 ShopUpgrade)


class ShopUI(UIComponent):
    """
    商店界面

    显示商店物品和升级选项，支持购买操作
    """

    def __init__(self, screen_width: int = 1120, screen_height: int = 608,
                 width: int = 600, height: int = 500):
        # 居中显示
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        super().__init__(x, y, width, height)

        self._shop_data: Optional[ShopData] = None
        self._player_stats: Optional[PlayerStats] = None
        self._entries: List[ShopEntry] = []
        self._selected_index: int = 0
        self._scroll_offset: int = 0
        self._visible_items: int = 8  # 可见条目数
        self._item_height: int = 48   # 每条目高度

        # 回调
        self._on_buy: Optional[Callable[[ShopEntry], bool]] = None
        self._on_close: Optional[Callable[[], None]] = None

        # 消息显示
        self._message: str = ""
        self._message_color: Tuple[int, int, int] = (255, 255, 255)
        self._message_timer: float = 0

        # 样式
        self._style = UIStyle(
            bg_color=(30, 30, 45),
            border_color=(80, 80, 120),
            text_color=(255, 255, 255),
            highlight_color=(100, 120, 180),
            border_width=2,
            border_radius=8
        )

        # 颜色
        self._gold_color = (255, 215, 0)
        self._can_afford_color = (100, 255, 100)
        self._cannot_afford_color = (255, 100, 100)
        self._selected_bg = (60, 80, 120)

    # ============================================================
    # 属性
    # ============================================================

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def is_visible(self) -> bool:
        return self._visible

    # ============================================================
    # 公共方法
    # ============================================================

    def open(self, shop_data: ShopData, player_stats: PlayerStats) -> None:
        """
        打开商店

        Args:
            shop_data: 商店数据
            player_stats: 玩家属性
        """
        self._shop_data = shop_data
        self._player_stats = player_stats
        self._selected_index = 0
        self._scroll_offset = 0
        self._message = ""
        self._build_entries()
        self._visible = True

    def close(self) -> None:
        """关闭商店"""
        self._visible = False
        self._shop_data = None
        self._player_stats = None
        self._entries.clear()
        if self._on_close:
            self._on_close()

    def set_callbacks(self, on_buy: Callable[[ShopEntry], bool],
                      on_close: Callable[[], None]) -> None:
        """设置回调函数"""
        self._on_buy = on_buy
        self._on_close = on_close

    def select_up(self) -> None:
        """选择上一项"""
        if not self._entries:
            return
        self._selected_index = (self._selected_index - 1) % len(self._entries)
        self._adjust_scroll()

    def select_down(self) -> None:
        """选择下一项"""
        if not self._entries:
            return
        self._selected_index = (self._selected_index + 1) % len(self._entries)
        self._adjust_scroll()

    def confirm(self) -> None:
        """确认购买当前选中项"""
        if not self._entries or not self._player_stats:
            return

        entry = self._entries[self._selected_index]

        # 检查是否买得起
        if self._player_stats.gold < entry.price:
            self._show_message("Not enough gold!", self._cannot_afford_color)
            return

        # 调用购买回调
        if self._on_buy and self._on_buy(entry):
            self._show_message(f"Bought {entry.display_name}!", self._can_afford_color)
        else:
            self._show_message("Cannot buy!", self._cannot_afford_color)

    def cancel(self) -> None:
        """取消/关闭"""
        self.close()

    # ============================================================
    # 更新和渲染
    # ============================================================

    def update(self, delta_time: float) -> None:
        """更新界面"""
        if self._message_timer > 0:
            self._message_timer -= delta_time
            if self._message_timer <= 0:
                self._message = ""

    def render(self, surface: Surface) -> None:
        """渲染商店界面"""
        if not self._visible:
            return

        # 绘制半透明背景遮罩
        overlay = Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        # 绘制主面板
        self._render_panel(surface)

        # 绘制标题
        self._render_title(surface)

        # 绘制玩家金币
        self._render_gold(surface)

        # 绘制物品列表
        self._render_items(surface)

        # 绘制操作提示
        self._render_hints(surface)

        # 绘制消息
        if self._message:
            self._render_message(surface)

    # ============================================================
    # 内部方法
    # ============================================================

    def _build_entries(self) -> None:
        """构建显示条目"""
        self._entries.clear()

        if not self._shop_data:
            return

        # 添加物品
        for shop_item in self._shop_data.items:
            if shop_item.item_data:
                display_name = shop_item.item_data.name_cn or shop_item.item_data.name
                description = shop_item.item_data.description
            else:
                display_name = shop_item.item_id
                description = ""

            self._entries.append(ShopEntry(
                display_name=display_name,
                description=description,
                price=shop_item.price,
                entry_type="item",
                data=shop_item
            ))

        # 添加升级
        for upgrade in self._shop_data.upgrades:
            self._entries.append(ShopEntry(
                display_name=upgrade.name_cn or upgrade.name,
                description=f"+{upgrade.amount}",
                price=upgrade.price,
                entry_type="upgrade",
                data=upgrade
            ))

    def _adjust_scroll(self) -> None:
        """调整滚动位置"""
        if self._selected_index < self._scroll_offset:
            self._scroll_offset = self._selected_index
        elif self._selected_index >= self._scroll_offset + self._visible_items:
            self._scroll_offset = self._selected_index - self._visible_items + 1

    def _show_message(self, text: str, color: Tuple[int, int, int]) -> None:
        """显示消息"""
        self._message = text
        self._message_color = color
        self._message_timer = 1.5

    def _render_panel(self, surface: Surface) -> None:
        """绘制主面板"""
        # 背景
        pygame.draw.rect(
            surface,
            self._style.bg_color,
            self.rect,
            border_radius=self._style.border_radius
        )

        # 边框
        pygame.draw.rect(
            surface,
            self._style.border_color,
            self.rect,
            width=self._style.border_width,
            border_radius=self._style.border_radius
        )

    def _render_title(self, surface: Surface) -> None:
        """绘制标题"""
        if not self._shop_data:
            return

        font = UIFont()
        title = self._shop_data.name_cn or self._shop_data.name
        title_surface = font.render(title, 20, self._style.highlight_color)
        surface.blit(title_surface, (self._x + 16, self._y + 12))

        # 描述
        if self._shop_data.description:
            desc_surface = font.render(
                self._shop_data.description, 14, (150, 150, 170)
            )
            surface.blit(desc_surface, (self._x + 16, self._y + 38))

    def _render_gold(self, surface: Surface) -> None:
        """绘制玩家金币"""
        if not self._player_stats:
            return

        font = UIFont()
        gold_text = f"Gold: {self._player_stats.gold}"
        gold_surface = font.render(gold_text, 18, self._gold_color)
        surface.blit(gold_surface, (self._x + self._width - 120, self._y + 16))

    def _render_items(self, surface: Surface) -> None:
        """绘制物品列表"""
        if not self._entries:
            font = UIFont()
            empty_text = font.render("No items available", 16, (150, 150, 150))
            surface.blit(empty_text, (self._x + 20, self._y + 70))
            return

        font = UIFont()
        start_y = self._y + 60

        for i in range(self._visible_items):
            index = self._scroll_offset + i
            if index >= len(self._entries):
                break

            entry = self._entries[index]
            y = start_y + i * self._item_height

            # 选中高亮
            if index == self._selected_index:
                highlight_rect = Rect(
                    self._x + 8, y,
                    self._width - 16, self._item_height - 4
                )
                pygame.draw.rect(
                    surface, self._selected_bg,
                    highlight_rect, border_radius=4
                )

            # 名称
            name_color = self._style.text_color
            name_surface = font.render(entry.display_name, 16, name_color)
            surface.blit(name_surface, (self._x + 20, y + 4))

            # 描述
            if entry.description:
                desc_surface = font.render(entry.description, 12, (150, 150, 170))
                surface.blit(desc_surface, (self._x + 20, y + 26))

            # 价格
            can_afford = self._player_stats and self._player_stats.gold >= entry.price
            price_color = self._can_afford_color if can_afford else self._cannot_afford_color
            price_text = f"{entry.price} G"
            price_surface = font.render(price_text, 14, price_color)
            surface.blit(price_surface, (self._x + self._width - 80, y + 12))

        # 滚动指示器
        if len(self._entries) > self._visible_items:
            if self._scroll_offset > 0:
                up_arrow = font.render("^", 14, (150, 150, 150))
                surface.blit(up_arrow, (self._x + self._width // 2 - 5, self._y + 48))

            if self._scroll_offset + self._visible_items < len(self._entries):
                down_arrow = font.render("v", 14, (150, 150, 150))
                surface.blit(down_arrow, (self._x + self._width // 2 - 5,
                                          self._y + self._height - 60))

    def _render_hints(self, surface: Surface) -> None:
        """绘制操作提示"""
        font = UIFont()
        hints = [
            "UP/DOWN: Select",
            "ENTER: Buy",
            "ESC: Close"
        ]

        y = self._y + self._height - 35
        for i, hint in enumerate(hints):
            hint_surface = font.render(hint, 12, (120, 120, 140))
            x = self._x + 16 + i * 140
            surface.blit(hint_surface, (x, y))

    def _render_message(self, surface: Surface) -> None:
        """绘制消息"""
        font = UIFont()
        msg_surface = font.render(self._message, 16, self._message_color)
        msg_rect = msg_surface.get_rect(
            center=(self._x + self._width // 2, self._y + self._height - 55)
        )
        surface.blit(msg_surface, msg_rect)
