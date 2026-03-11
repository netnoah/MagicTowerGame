"""
HUD - 游戏内 HUD 面板

显示玩家属性、钥匙、金币、楼层等信息
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

import pygame
from pygame.surface import Surface

from ui.base import UIComponent, Panel, Label, IconLabel, Divider, UIFont, UIStyle
from entities.player import PlayerStats


@dataclass
class HUDConfig:
    """HUD 配置"""
    WIDTH: int = 160  # HUD 面板宽度
    PADDING: int = 12
    LINE_HEIGHT: int = 28
    SECTION_GAP: int = 16


class HUD(UIComponent):
    """
    游戏内 HUD 面板

    显示在屏幕左侧，包含：
    - 楼层信息
    - 玩家属性 (HP, 攻击, 防御)
    - 金币
    - 钥匙 (黄/蓝/红)
    """

    def __init__(self, x: int, y: int, height: int, config: Optional[HUDConfig] = None):
        """
        初始化 HUD

        Args:
            x: X 坐标
            y: Y 坐标
            height: 面板高度
            config: HUD 配置
        """
        self._config = config or HUDConfig()

        super().__init__(x, y, self._config.WIDTH, height)

        self._style = UIStyle(
            bg_color=(35, 35, 50),
            border_color=(70, 70, 90),
            text_color=(220, 220, 220),
            highlight_color=(180, 140, 100),
            border_width=2,
            border_radius=8,
            padding=self._config.PADDING
        )

        # 当前显示的数据
        self._floor: int = 1
        self._stats: Optional[PlayerStats] = None

        # 图标路径
        self._icon_paths = {
            'gold': 'assets/ui/icon/gold.png',
            'yellow_key': 'assets/ui/icon/yellow_key.png',
            'blue_key': 'assets/ui/icon/blue_key.png',
            'red_key': 'assets/ui/icon/red_key.png',
        }

        # 预加载图标
        self._icons: dict = {}
        self._load_icons()

    def _load_icons(self) -> None:
        """预加载图标"""
        for key, path in self._icon_paths.items():
            try:
                icon = pygame.image.load(path)
                self._icons[key] = pygame.transform.scale(icon, (20, 20))
            except Exception:
                self._icons[key] = None

    def update_data(self, floor: int, stats: PlayerStats) -> None:
        """
        更新 HUD 数据

        Args:
            floor: 当前楼层
            stats: 玩家属性
        """
        self._floor = floor
        self._stats = stats
        self._dirty = True

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 绘制背景面板
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
        y = self._y + self._config.PADDING
        x = self._x + self._config.PADDING
        content_width = self._config.WIDTH - self._config.PADDING * 2

        # === 楼层信息 ===
        floor_text = f"F {self._floor}"
        floor_surface = font.render(floor_text, 28, self._style.highlight_color)
        surface.blit(floor_surface, (x, y))
        y += 40

        # 分隔线
        self._draw_divider(surface, x, y, content_width)
        y += self._config.SECTION_GAP

        # === 玩家属性 ===
        if self._stats:
            # HP
            y = self._draw_stat_row(surface, x, y, "HP", f"{self._stats.hp}/{self._stats.max_hp}",
                                    (220, 80, 80))

            # 攻击
            y = self._draw_stat_row(surface, x, y, "ATK", str(self._stats.attack),
                                    (255, 180, 80))

            # 防御
            y = self._draw_stat_row(surface, x, y, "DEF", str(self._stats.defense),
                                    (80, 180, 255))

            # 分隔线
            y += 8
            self._draw_divider(surface, x, y, content_width)
            y += self._config.SECTION_GAP

            # === 金币 ===
            y = self._draw_icon_row(surface, x, y, 'gold', str(self._stats.gold))

            # === 钥匙 ===
            y += 8
            y = self._draw_icon_row(surface, x, y, 'yellow_key',
                                    str(self._stats.yellow_keys), (255, 220, 80))
            y = self._draw_icon_row(surface, x, y, 'blue_key',
                                    str(self._stats.blue_keys), (80, 150, 255))
            y = self._draw_icon_row(surface, x, y, 'red_key',
                                    str(self._stats.red_keys), (255, 80, 80))

        # === 快捷键说明 ===
        # 在面板底部显示
        self._draw_hotkeys(surface, x, self._y + self._height - 85)

    def _draw_stat_row(self, surface: Surface, x: int, y: int,
                       label: str, value: str, value_color: Tuple[int, int, int]) -> int:
        """
        绘制属性行

        Returns:
            新的 Y 坐标
        """
        font = UIFont()

        # 标签
        label_surface = font.render(label, 14, self._style.text_color)
        surface.blit(label_surface, (x, y + 4))

        # 值（右对齐）
        value_surface = font.render(value, 18, value_color)
        value_x = x + self._config.WIDTH - self._config.PADDING * 2 - value_surface.get_width()
        surface.blit(value_surface, (value_x, y))

        return y + self._config.LINE_HEIGHT

    def _draw_icon_row(self, surface: Surface, x: int, y: int,
                       icon_key: str, value: str,
                       value_color: Tuple[int, int, int] = (255, 255, 255)) -> int:
        """
        绘制图标+数值行

        Returns:
            新的 Y 坐标
        """
        icon = self._icons.get(icon_key)

        if icon:
            surface.blit(icon, (x, y + 2))
            text_x = x + 28
        else:
            text_x = x

        # 值
        font = UIFont()
        value_surface = font.render(value, 16, value_color)
        surface.blit(value_surface, (text_x, y + 3))

        return y + self._config.LINE_HEIGHT

    def _draw_divider(self, surface: Surface, x: int, y: int, width: int) -> None:
        """绘制分隔线"""
        pygame.draw.line(
            surface,
            self._style.border_color,
            (x, y),
            (x + width, y)
        )

    def _draw_hotkeys(self, surface: Surface, x: int, y: int) -> None:
        """
        绘制快捷键说明

        Args:
            surface: 渲染表面
            x: X 坐标
            y: Y 坐标
        """
        font = UIFont()
        content_width = self._config.WIDTH - self._config.PADDING * 2

        # 分隔线
        self._draw_divider(surface, x, y, content_width)
        y += 10

        # 标题
        title_surface = font.render("Hotkeys", 12, self._style.highlight_color)
        surface.blit(title_surface, (x, y))
        y += 18

        # 快捷键列表
        hotkeys = [
            ("Arrow", "Move"),
            ("ESC", "Pause"),
            ("CTRL", "Monsters"),
        ]

        key_color = (140, 180, 220)
        desc_color = (160, 160, 160)

        for key, desc in hotkeys:
            key_surface = font.render(key, 11, key_color)
            desc_surface = font.render(desc, 11, desc_color)
            surface.blit(key_surface, (x, y))
            surface.blit(desc_surface, (x + 50, y))
            y += 16


class CombatPreview(UIComponent):
    """
    战斗预览面板

    显示玩家与怪物的属性对比和预估伤害
    """

    def __init__(self, width: int = 300, height: int = 200):
        super().__init__(0, 0, width, height)

        self._style = UIStyle(
            bg_color=(40, 40, 55, 230),
            border_color=(100, 100, 140),
            text_color=(255, 255, 255),
            highlight_color=(180, 140, 100),
            border_width=2,
            border_radius=10
        )

        self._visible = False
        self._monster_name: str = ""
        self._monster_hp: int = 0
        self._monster_atk: int = 0
        self._monster_def: int = 0
        self._player_damage: int = 0
        self._rounds: int = 0
        self._victory: bool = False

    def show(self, monster_name: str, monster_hp: int, monster_atk: int, monster_def: int,
             player_damage: int, rounds: int, victory: bool) -> None:
        """显示战斗预览"""
        self._monster_name = monster_name
        self._monster_hp = monster_hp
        self._monster_atk = monster_atk
        self._monster_def = monster_def
        self._player_damage = player_damage
        self._rounds = rounds
        self._victory = victory
        self._visible = True
        self._dirty = True

    def hide(self) -> None:
        """隐藏面板"""
        self._visible = False

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 居中显示
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        self._x = (screen_width - self._width) // 2
        self._y = (screen_height - self._height) // 2

        # 绘制半透明背景
        bg_surface = Surface((self._width, self._height), pygame.SRCALPHA)
        pygame.draw.rect(
            bg_surface,
            (*self._style.bg_color[:3], 230),
            bg_surface.get_rect(),
            border_radius=self._style.border_radius
        )
        surface.blit(bg_surface, (self._x, self._y))

        # 绘制边框
        pygame.draw.rect(
            surface,
            self._style.border_color,
            self.rect,
            width=self._style.border_width,
            border_radius=self._style.border_radius
        )

        font = UIFont()
        y = self._y + 16
        x = self._x + 20

        # 标题
        title = "COMBAT PREVIEW"
        title_surface = font.render(title, 18, self._style.highlight_color)
        title_x = self._x + (self._width - title_surface.get_width()) // 2
        surface.blit(title_surface, (title_x, y))
        y += 36

        # 怪物信息
        monster_label = font.render("Monster:", 14, (180, 180, 180))
        surface.blit(monster_label, (x, y))
        monster_name = font.render(self._monster_name, 16, (255, 150, 150))
        surface.blit(monster_name, (x + 70, y - 2))
        y += 24

        # 怪物属性
        stats_text = f"HP: {self._monster_hp}  ATK: {self._monster_atk}  DEF: {self._monster_def}"
        stats_surface = font.render(stats_text, 14, (200, 200, 200))
        surface.blit(stats_surface, (x, y))
        y += 32

        # 战斗结果
        if self._victory:
            result_color = (100, 255, 100)
            result_text = f"WIN! Rounds: {self._rounds}"
        else:
            result_color = (255, 100, 100)
            result_text = "LOSE!"

        result_surface = font.render(result_text, 20, result_color)
        result_x = self._x + (self._width - result_surface.get_width()) // 2
        surface.blit(result_surface, (result_x, y))
        y += 32

        # 预估伤害
        damage_text = f"Est. Damage Taken: {self._player_damage}"
        damage_color = (255, 200, 100) if self._victory else (255, 100, 100)
        damage_surface = font.render(damage_text, 16, damage_color)
        damage_x = self._x + (self._width - damage_surface.get_width()) // 2
        surface.blit(damage_surface, (damage_x, y))
        y += 36

        # 提示
        hint_text = "Press direction key to engage or other to cancel"
        hint_surface = font.render(hint_text, 12, (150, 150, 150))
        hint_x = self._x + (self._width - hint_surface.get_width()) // 2
        surface.blit(hint_surface, (hint_x, y))


class MessageDisplay(UIComponent):
    """
    消息显示系统

    在屏幕底部显示临时消息
    """

    def __init__(self, x: int, y: int, width: int):
        super().__init__(x, y, width, 40)

        self._messages: List[Tuple[str, float, Tuple[int, int, int]]] = []
        self._max_messages = 3
        self._message_duration = 2.0  # 消息显示时间（秒）

    def add_message(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """添加消息"""
        import time
        self._messages.append((text, time.time(), color))
        # 限制消息数量
        if len(self._messages) > self._max_messages:
            self._messages.pop(0)
        self._dirty = True

    def update(self, delta_time: float) -> None:
        """更新消息（移除过期消息）"""
        import time
        current_time = time.time()
        self._messages = [
            msg for msg in self._messages
            if current_time - msg[1] < self._message_duration
        ]

    def render(self, surface: Surface) -> None:
        if not self._visible or not self._messages:
            return

        font = UIFont()
        y = self._y

        for text, _, color in self._messages:
            text_surface = font.render(text, 16, color)

            # 绘制背景
            padding = 8
            bg_rect = pygame.Rect(
                self._x - padding,
                y - 2,
                text_surface.get_width() + padding * 2,
                24
            )
            pygame.draw.rect(
                surface,
                (40, 40, 55, 200),
                bg_rect,
                border_radius=4
            )

            surface.blit(text_surface, (self._x, y))
            y += 28


class MonsterInfoPanel(UIComponent):
    """
    怪物信息面板

    按 O 键打开，显示当前楼层所有怪物类型及战斗预览
    """

    def __init__(self, width: int = 400, height: int = 500):
        super().__init__(0, 0, width, height)

        self._style = UIStyle(
            bg_color=(45, 45, 65),  # 更明显的背景色
            border_color=(150, 150, 180),  # 更明显的边框
            text_color=(220, 220, 220),
            highlight_color=(255, 200, 100),
            border_width=3,  # 更粗的边框
            border_radius=10
        )

        self._visible = False
        self._floor: int = 1
        self._monster_info_list: List[Dict] = []  # 怪物信息列表
        self._scroll_offset: int = 0
        self._max_visible: int = 8  # 最多显示几个怪物

    def toggle(self) -> None:
        """切换显示/隐藏"""
        self._visible = not self._visible

    def is_visible(self) -> bool:
        return self._visible

    def update_data(self, floor: int, monster_info_list: List[Dict]) -> None:
        """
        更新面板数据

        Args:
            floor: 当前楼层
            monster_info_list: 怪物信息列表，每个元素包含:
                - name: 怪物名称
                - hp, atk, def: 属性
                - count: 当前楼层数量
                - can_win: 能否战胜
                - damage_taken: 预估受到的伤害
                - rounds: 回合数
        """
        self._floor = floor
        self._monster_info_list = monster_info_list
        self._scroll_offset = 0
        self._dirty = True

    def scroll_up(self) -> None:
        """向上滚动"""
        if self._scroll_offset > 0:
            self._scroll_offset -= 1

    def scroll_down(self) -> None:
        """向下滚动"""
        max_scroll = max(0, len(self._monster_info_list) - self._max_visible)
        if self._scroll_offset < max_scroll:
            self._scroll_offset += 1

    def render(self, surface: Surface) -> None:
        if not self._visible:
            return

        # 居中显示
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        self._x = (screen_width - self._width) // 2
        self._y = (screen_height - self._height) // 2

        # 绘制半透明背景
        bg_surface = Surface((self._width, self._height), pygame.SRCALPHA)
        pygame.draw.rect(
            bg_surface,
            (*self._style.bg_color, 240),
            bg_surface.get_rect(),
            border_radius=self._style.border_radius
        )
        surface.blit(bg_surface, (self._x, self._y))

        # 绘制边框
        pygame.draw.rect(
            surface,
            self._style.border_color,
            self.rect,
            width=self._style.border_width,
            border_radius=self._style.border_radius
        )

        font = UIFont()
        y = self._y + 16
        x = self._x + 20

        # 标题
        title = f"Floor {self._floor} - Monsters"
        title_surface = font.render(title, 22, self._style.highlight_color)
        title_x = self._x + (self._width - title_surface.get_width()) // 2
        surface.blit(title_surface, (title_x, y))
        y += 36

        # 分隔线
        pygame.draw.line(
            surface,
            self._style.border_color,
            (x, y),
            (x + self._width - 40, y)
        )
        y += 12

        # 列位置定义（与数据行对齐）
        col_name = x
        col_hp = x + 90
        col_atk = x + 140
        col_def = x + 190
        col_dmg = x + 240
        col_win = x + 295

        # 表头
        header_color = (150, 150, 170)
        surface.blit(font.render("Name", 12, header_color), (col_name, y))
        surface.blit(font.render("HP", 12, header_color), (col_hp, y))
        surface.blit(font.render("ATK", 12, header_color), (col_atk, y))
        surface.blit(font.render("DEF", 12, header_color), (col_def, y))
        surface.blit(font.render("Dmg", 12, header_color), (col_dmg, y))
        surface.blit(font.render("Win", 12, header_color), (col_win, y))
        y += 22

        # 怪物列表
        if not self._monster_info_list:
            no_data = font.render("No monsters on this floor", 16, (150, 150, 150))
            no_data_x = self._x + (self._width - no_data.get_width()) // 2
            surface.blit(no_data, (no_data_x, y + 40))
        else:
            visible_monsters = self._monster_info_list[self._scroll_offset:
                                                        self._scroll_offset + self._max_visible]

            for info in visible_monsters:
                # 怪物名称（可能需要截断）
                name = info.get('name', 'Unknown')[:10]
                name_color = (255, 200, 150) if info.get('can_win') else (255, 120, 120)
                name_surface = font.render(name, 14, name_color)
                surface.blit(name_surface, (col_name, y))

                # HP
                hp_text = str(info.get('hp', 0))
                hp_surface = font.render(hp_text, 13, (180, 180, 180))
                surface.blit(hp_surface, (col_hp, y + 1))

                # ATK
                atk_text = str(info.get('atk', 0))
                atk_surface = font.render(atk_text, 13, (180, 180, 180))
                surface.blit(atk_surface, (col_atk, y + 1))

                # DEF
                def_text = str(info.get('def', 0))
                def_surface = font.render(def_text, 13, (180, 180, 180))
                surface.blit(def_surface, (col_def, y + 1))

                # 预估伤害
                damage = info.get('damage_taken', 0)
                if info.get('can_win'):
                    damage_color = (255, 200, 100) if damage > 0 else (100, 255, 100)
                    damage_text = str(damage)
                    win_text = "Yes"
                    win_color = (100, 255, 100)
                else:
                    damage_color = (255, 100, 100)
                    damage_text = "N/A"
                    win_text = "No"
                    win_color = (255, 100, 100)

                damage_surface = font.render(damage_text, 13, damage_color)
                surface.blit(damage_surface, (col_dmg, y + 1))

                win_surface = font.render(win_text, 13, win_color)
                surface.blit(win_surface, (col_win, y + 1))

                # 数量
                count = info.get('count', 1)
                if count > 1:
                    count_surface = font.render(f"x{count}", 12, (150, 150, 150))
                    surface.blit(count_surface, (col_win + 45, y + 1))

                y += 26

        # 滚动提示
        if len(self._monster_info_list) > self._max_visible:
            scroll_text = f"[{self._scroll_offset + 1}-{min(self._scroll_offset + self._max_visible, len(self._monster_info_list))}/{len(self._monster_info_list)}]"
            scroll_surface = font.render(scroll_text, 12, (120, 120, 140))
            surface.blit(scroll_surface, (x + self._width - 100, y + 10))

        # 底部提示
        hint_y = self._y + self._height - 35
        hint_text = "Press ctrl to close"
        hint_surface = font.render(hint_text, 13, (120, 120, 140))
        hint_x = self._x + (self._width - hint_surface.get_width()) // 2
        surface.blit(hint_surface, (hint_x, hint_y))
