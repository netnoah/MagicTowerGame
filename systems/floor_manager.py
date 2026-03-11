"""
Floor Manager - 楼层管理器

负责加载、管理和渲染游戏地图楼层
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path

import pygame
from pygame.surface import Surface

from config import PATH, TILE, ColorConfig
from systems.tile import (
    TileType, TileManager, TileProperties,
    tile_coords_to_pixels
)
from entities.monster import Monster, MonsterManager
from systems.items import ItemManager, ItemData


@dataclass
class EntityPlacement:
    """实体放置信息"""
    entity_type: str      # 实体类型: "monster", "item", "npc", "player"
    entity_id: str        # 实体ID
    x: int                # 瓦片 X 坐标
    y: int                # 瓦片 Y 坐标
    data: Dict[str, Any] = field(default_factory=dict)  # 额外数据


@dataclass
class FloorData:
    """楼层数据"""
    level: int                          # 楼层编号
    width: int                          # 宽度（瓦片数）
    height: int                         # 高度（瓦片数）
    tiles: List[List[TileType]]         # 瓦片地图
    entities: List[EntityPlacement]     # 实体列表
    player_start: Tuple[int, int]       # 玩家起始位置
    stairs_up: Optional[Tuple[int, int]] = None   # 上楼楼梯位置
    stairs_down: Optional[Tuple[int, int]] = None # 下楼楼梯位置
    name: str = ""                      # 楼层名称


class FloorManager:
    """
    楼层管理器

    管理游戏中的所有楼层

    使用示例:
        floor_manager = FloorManager()
        floor_manager.load_floor(1)

        # 渲染当前楼层
        floor_manager.render(screen)

        # 检查碰撞
        if floor_manager.is_walkable(5, 3):
            player.move_to(5, 3)
    """

    # 地图数据中的瓦片类型映射
    TILE_TYPE_MAP = {
        0: TileType.EMPTY,
        1: TileType.FLOOR,
        2: TileType.WALL,
        10: TileType.DOOR_YELLOW,
        11: TileType.DOOR_BLUE,
        12: TileType.DOOR_RED,
        20: TileType.STAIRS_UP,
        21: TileType.STAIRS_DOWN,
        30: TileType.SHOP,
        31: TileType.NPC,
    }

    def __init__(self, maps_dir: str = None, tile_size: int = None):
        """
        初始化楼层管理器

        Args:
            maps_dir: 地图数据目录
            tile_size: 瓦片尺寸
        """
        self._maps_dir = Path(maps_dir or PATH.MAPS_DIR)
        self._tile_size = tile_size or TILE.SIZE

        # 瓦片管理器
        self._tile_manager = TileManager(tile_size=self._tile_size)

        # 当前楼层
        self._current_floor: Optional[FloorData] = None
        self._current_level: int = 0

        # 楼层缓存
        self._floor_cache: Dict[int, FloorData] = {}

        # 渲染偏移（用于居中地图）
        self._render_offset: Tuple[int, int] = (0, 0)

        # 怪物管理
        self._monster_manager = MonsterManager()
        self._monster_manager.load_monster_data("data/entities/monsters.json")
        self._monsters: Dict[int, List[Monster]] = {}  # {楼层: [怪物列表]}
        self._monsters_cache: Dict[Tuple[int, int, int], Monster] = {}  # {(楼层, x, y): Monster}

        # 物品管理
        self._item_manager = ItemManager()
        self._item_manager.load_from_json("data/entities/items.json")
        self._items: Dict[int, List[EntityPlacement]] = {}  # {楼层: [物品列表]}
        self._items_cache: Dict[Tuple[int, int, int], EntityPlacement] = {}  # {(楼层, x, y): EntityPlacement}

    def load_tiles(self) -> None:
        """加载瓦片资源"""
        self._tile_manager.load_tiles()

    def load_floor(self, level: int) -> bool:
        """
        加载指定楼层

        Args:
            level: 楼层编号

        Returns:
            是否加载成功
        """
        # 检查缓存
        if level in self._floor_cache:
            self._current_floor = self._floor_cache[level]
            self._current_level = level
            return True

        # 尝试加载地图文件
        map_file = self._maps_dir / f"floor_{level:02d}.json"

        if not map_file.exists():
            # 如果文件不存在，创建默认地图
            floor_data = self._create_default_floor(level)
        else:
            floor_data = self._load_floor_from_file(map_file)

        if floor_data:
            self._floor_cache[level] = floor_data
            self._current_floor = floor_data
            self._current_level = level

            # 加载该楼层的怪物
            self._load_floor_monsters(level, floor_data.entities)

            # 加载该楼层的物品
            self._load_floor_items(level, floor_data.entities)

            return True

        return False

    def _load_floor_from_file(self, file_path: Path) -> Optional[FloorData]:
        """从文件加载楼层数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 解析瓦片地图
            tiles = []
            for row in data.get('tiles', []):
                tile_row = []
                for cell in row:
                    if isinstance(cell, int):
                        tile_row.append(self.TILE_TYPE_MAP.get(cell, TileType.FLOOR))
                    else:
                        tile_row.append(TileType.FLOOR)
                tiles.append(tile_row)

            # 解析实体
            entities = []
            for entity_data in data.get('entities', []):
                entities.append(EntityPlacement(
                    entity_type=entity_data.get('type', ''),
                    entity_id=entity_data.get('id', ''),
                    x=entity_data.get('x', 0),
                    y=entity_data.get('y', 0),
                    data=entity_data.get('data', {})
                ))

            # 解析玩家起始位置
            player_start = tuple(data.get('player_start', [0, 0]))

            # 查找楼梯位置
            stairs_up = None
            stairs_down = None
            for y, row in enumerate(tiles):
                for x, tile in enumerate(row):
                    if tile == TileType.STAIRS_UP:
                        stairs_up = (x, y)
                    elif tile == TileType.STAIRS_DOWN:
                        stairs_down = (x, y)

            return FloorData(
                level=data.get('level', 1),
                width=data.get('width', len(tiles[0]) if tiles else 0),
                height=data.get('height', len(tiles)),
                tiles=tiles,
                entities=entities,
                player_start=player_start,
                stairs_up=stairs_up,
                stairs_down=stairs_down,
                name=data.get('name', f"Floor {data.get('level', 1)}")
            )

        except Exception as e:
            print(f"Error loading floor: {e}")
            return None

    def _create_default_floor(self, level: int) -> FloorData:
        """创建默认楼层"""
        width = TILE.MAP_WIDTH
        height = TILE.MAP_HEIGHT

        # 创建空地图
        tiles = [[TileType.FLOOR for _ in range(width)] for _ in range(height)]

        # 设置边界墙壁
        for x in range(width):
            tiles[0][x] = TileType.WALL
            tiles[height - 1][x] = TileType.WALL
        for y in range(height):
            tiles[y][0] = TileType.WALL
            tiles[y][width - 1] = TileType.WALL

        # 添加楼梯
        if level > 1:
            tiles[height - 2][width - 2] = TileType.STAIRS_DOWN
        if level < 21:  # 假设最多21层
            tiles[1][1] = TileType.STAIRS_UP

        return FloorData(
            level=level,
            width=width,
            height=height,
            tiles=tiles,
            entities=[],
            player_start=(width // 2, height // 2),
            stairs_up=(1, 1) if level < 21 else None,
            stairs_down=(width - 2, height - 2) if level > 1 else None,
            name=f"Floor {level}"
        )

    def render(self, surface: Surface, offset: Tuple[int, int] = None,
               viewport: Tuple[int, int, int, int] = None) -> None:
        """渲染当前楼层"""
        if not self._current_floor:
            return

        if not self._tile_manager.is_loaded:
            self._tile_manager.load_tiles()

        offset = offset or self._render_offset
        floor = self._current_floor

        # 确定渲染范围
        if viewport:
            start_x, start_y, end_x, end_y = viewport
        else:
            start_x, start_y = 0, 0
            end_x, end_y = floor.width, floor.height

        # 渲染瓦片
        for y in range(start_y, min(end_y, floor.height)):
            for x in range(start_x, min(end_x, floor.width)):
                tile_type = floor.tiles[y][x]
                pixel_x = x * self._tile_size + offset[0]
                pixel_y = y * self._tile_size + offset[1]
                self._tile_manager.draw_tile(surface, tile_type, (pixel_x, pixel_y))

    def get_tile(self, x: int, y: int) -> Optional[TileType]:
        """获取指定位置的瓦片类型"""
        if not self._current_floor:
            return None

        if 0 <= x < self._current_floor.width and 0 <= y < self._current_floor.height:
            return self._current_floor.tiles[y][x]

        return None

    def set_tile(self, x: int, y: int, tile_type: TileType) -> bool:
        """设置指定位置的瓦片类型"""
        if not self._current_floor:
            return False

        if 0 <= x < self._current_floor.width and 0 <= y < self._current_floor.height:
            self._current_floor.tiles[y][x] = tile_type
            return True

        return False

    def is_walkable(self, x: int, y: int) -> bool:
        """检查指定位置是否可行走"""
        tile_type = self.get_tile(x, y)
        if tile_type is None:
            return False

        return self._tile_manager.is_walkable(tile_type)

    def is_interactive(self, x: int, y: int) -> bool:
        """检查指定位置是否可交互"""
        tile_type = self.get_tile(x, y)
        if tile_type is None:
            return False

        return self._tile_manager.is_interactive(tile_type)

    def get_tile_properties(self, x: int, y: int) -> Optional[TileProperties]:
        """获取指定位置瓦片的属性"""
        tile_type = self.get_tile(x, y)
        if tile_type is None:
            return None

        return self._tile_manager.get_tile_properties(tile_type)

    def get_entities(self) -> List[EntityPlacement]:
        """获取当前楼层的所有实体"""
        if self._current_floor:
            return self._current_floor.entities
        return []

    def add_entity(self, entity: EntityPlacement) -> None:
        """添加实体到当前楼层"""
        if self._current_floor:
            self._current_floor.entities.append(entity)

    def remove_entity(self, x: int, y: int) -> Optional[EntityPlacement]:
        """移除指定位置的实体"""
        if not self._current_floor:
            return None

        for i, entity in enumerate(self._current_floor.entities):
            if entity.x == x and entity.y == y:
                return self._current_floor.entities.pop(i)

        return None

    def get_player_start(self) -> Tuple[int, int]:
        """获取玩家起始位置"""
        if self._current_floor:
            return self._current_floor.player_start
        return (0, 0)

    def get_stairs_up(self) -> Optional[Tuple[int, int]]:
        """获取上楼楼梯位置"""
        if self._current_floor:
            return self._current_floor.stairs_up
        return None

    def get_stairs_down(self) -> Optional[Tuple[int, int]]:
        """获取下楼楼梯位置"""
        if self._current_floor:
            return self._current_floor.stairs_down
        return None

    def calculate_render_offset(self, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """计算渲染偏移，使地图居中显示"""
        if not self._current_floor:
            return (0, 0)

        map_width = self._current_floor.width * self._tile_size
        map_height = self._current_floor.height * self._tile_size

        offset_x = (screen_width - map_width) // 2
        offset_y = (screen_height - map_height) // 2

        self._render_offset = (offset_x, offset_y)
        return self._render_offset

    @property
    def current_level(self) -> int:
        """当前楼层编号"""
        return self._current_level

    @property
    def current_floor(self) -> Optional[FloorData]:
        """当前楼层数据"""
        return self._current_floor

    @property
    def tile_size(self) -> int:
        """瓦片尺寸"""
        return self._tile_size

    @property
    def map_width(self) -> int:
        """地图宽度（瓦片数）"""
        if self._current_floor:
            return self._current_floor.width
        return 0

    @property
    def map_height(self) -> int:
        """地图高度（瓦片数）"""
        if self._current_floor:
            return self._current_floor.height
        return 0

    # ============================================================
    # 怪物管理
    # ============================================================

    def _load_floor_monsters(self, level: int, entities: List[EntityPlacement]) -> None:
        """
        加载楼层怪物

        Args:
            level: 楼层编号
            entities: 实体列表
        """
        if level in self._monsters:
            return  # 已加载

        monsters = []
        for entity in entities:
            if entity.entity_type == "monster":
                monster_data = self._monster_manager.get_monster_data(entity.entity_id)
                if monster_data:
                    monster = Monster(entity.entity_id, entity.x, entity.y, monster_data)
                    monster.load_resources()
                    monsters.append(monster)
                    # 添加到缓存
                    self._monsters_cache[(level, entity.x, entity.y)] = monster

        self._monsters[level] = monsters

    def get_monster_at(self, x: int, y: int) -> Optional[Monster]:
        """
        获取指定位置的怪物

        Args:
            x: 瓦片 X 坐标
            y: 瓦片 Y 坐标

        Returns:
            怪物实体，如果没有则返回 None
        """
        return self._monsters_cache.get((self._current_level, x, y))

    def remove_monster(self, x: int, y: int) -> Optional[Monster]:
        """
        移除指定位置的怪物

        Args:
            x: 瓦片 X 坐标
            y: 瓦片 Y 坐标

        Returns:
            被移除的怪物
        """
        key = (self._current_level, x, y)
        monster = self._monsters_cache.pop(key, None)
        if monster and self._current_level in self._monsters:
            try:
                self._monsters[self._current_level].remove(monster)
            except ValueError:
                pass
        return monster

    def get_current_monsters(self) -> List[Monster]:
        """获取当前楼层的所有怪物"""
        return self._monsters.get(self._current_level, [])

    def update_monsters(self, delta_time: float) -> None:
        """更新当前楼层所有怪物"""
        for monster in self.get_current_monsters():
            monster.update(delta_time)

    def render_monsters(self, surface: Surface, offset: Tuple[int, int]) -> None:
        """渲染当前楼层的所有怪物"""
        for monster in self.get_current_monsters():
            monster.render(surface, offset)

    # ============================================================
    # 物品管理
    # ============================================================

    def _load_floor_items(self, level: int, entities: List[EntityPlacement]) -> None:
        """
        加载楼层物品

        Args:
            level: 楼层编号
            entities: 实体列表
        """
        if level in self._items:
            return  # 已加载

        items = []
        for entity in entities:
            if entity.entity_type == "item":
                items.append(entity)
                # 添加到缓存
                self._items_cache[(level, entity.x, entity.y)] = entity

        self._items[level] = items

    def get_item_at(self, x: int, y: int) -> Optional[EntityPlacement]:
        """
        获取指定位置的物品

        Args:
            x: 瓦片 X 坐标
            y: 瓦片 Y 坐标

        Returns:
            物品实体，如果没有则返回 None
        """
        return self._items_cache.get((self._current_level, x, y))

    def get_item_data(self, item_id: str) -> Optional[ItemData]:
        """
        获取物品数据

        Args:
            item_id: 物品ID

        Returns:
            物品数据
        """
        return self._item_manager.get_item(item_id)

    def remove_item(self, x: int, y: int) -> Optional[EntityPlacement]:
        """
        移除指定位置的物品

        Args:
            x: 瓦片 X 坐标
            y: 瓦片 Y 坐标

        Returns:
            被移除的物品
        """
        key = (self._current_level, x, y)
        item = self._items_cache.pop(key, None)
        if item and self._current_level in self._items:
            try:
                self._items[self._current_level].remove(item)
            except ValueError:
                pass
        # 同时从 entities 列表中移除
        if item and self._current_floor:
            try:
                self._current_floor.entities.remove(item)
            except ValueError:
                pass
        return item

    def get_current_items(self) -> List[EntityPlacement]:
        """获取当前楼层的所有物品"""
        return self._items.get(self._current_level, [])

    def render_items(self, surface: Surface, offset: Tuple[int, int]) -> None:
        """
        渲染当前楼层的所有物品

        Args:
            surface: 目标表面
            offset: 渲染偏移
        """
        font_size = 12
        try:
            font = pygame.font.Font(None, font_size)
        except:
            font = pygame.font.SysFont('arial', font_size)

        for item in self.get_current_items():
            item_data = self._item_manager.get_item(item.entity_id)
            if not item_data:
                continue

            # 计算渲染位置
            pixel_x = item.x * self._tile_size + offset[0]
            pixel_y = item.y * self._tile_size + offset[1]

            # 绘制物品背景
            bg_rect = pygame.Rect(pixel_x + 4, pixel_y + 4,
                                   self._tile_size - 8, self._tile_size - 8)

            # 根据物品类型设置颜色
            color_map = {
                "key": (255, 255, 100),      # 黄色系
                "potion": (255, 100, 255),   # 紫色系
                "weapon": (255, 150, 50),    # 橙色系
                "armor": (100, 150, 255),    # 蓝色系
                "special": (100, 255, 100),  # 绿色系
            }
            bg_color = color_map.get(item_data.item_type.value, (200, 200, 200))

            # 绘制背景
            pygame.draw.rect(surface, bg_color, bg_rect, border_radius=4)
            pygame.draw.rect(surface, (255, 255, 255), bg_rect, 1, border_radius=4)

            # 绘制物品名称首字母
            char = item_data.name_cn[0] if item_data.name_cn else "?"
            text_surface = font.render(char, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=bg_rect.center)
            surface.blit(text_surface, text_rect)
