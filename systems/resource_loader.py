"""
Resource Loader - 自动加载图片资源并生成多方向动画

资源命名规范:
  walk_0.png, walk_1.png, ...  -> walk 动画
  attack_0.png, attack_1.png, ... -> attack 动画

方向生成:
  原图 = 向右 (RIGHT)
  旋转90° = 向上 (UP)
  旋转180° = 向左 (LEFT)
  旋转270° = 向下 (DOWN)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import pygame
from pygame.surface import Surface


class Direction(Enum):
    """四个方向"""
    RIGHT = 0    # 原图
    UP = 90      # 逆时针90°
    LEFT = 180   # 逆时针180°
    DOWN = 270   # 逆时针270°


@dataclass
class AnimationData:
    """动画数据"""
    name: str                    # 动画名称 (walk, attack, idle...)
    frames: Dict[Direction, List[Surface]]  # 按方向分组的帧列表
    frame_count: int             # 帧数


class ResourceLoader:
    """
    资源加载器

    使用示例:
        loader = ResourceLoader("assets/sprites")

        # 加载角色动画
        player_animations = loader.load_entity("playerA")

        # 获取向右走的动画帧
        walk_right_frames = player_animations["walk"].frames[Direction.RIGHT]

        # 获取向上攻击的动画帧
        attack_up_frames = player_animations["attack"].frames[Direction.UP]
    """

    # 支持的图片格式
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp'}

    def __init__(self, base_path: str):
        """
        初始化资源加载器

        Args:
            base_path: 资源根目录路径
        """
        self.base_path = Path(base_path)
        self._cache: Dict[str, Dict[str, AnimationData]] = {}

    def load_entity(self, entity_name: str, use_cache: bool = True) -> Dict[str, AnimationData]:
        """
        加载一个实体的所有动画

        Args:
            entity_name: 实体名称 (对应文件夹名，如 "playerA")
            use_cache: 是否使用缓存

        Returns:
            字典: {动画名称: AnimationData}
        """
        if use_cache and entity_name in self._cache:
            return self._cache[entity_name]

        entity_path = self.base_path / entity_name

        if not entity_path.exists():
            raise FileNotFoundError(f"Entity folder not found: {entity_path}")

        # 扫描文件夹，按动画名称分组
        animation_files = self._scan_animation_files(entity_path)

        # 加载每个动画
        animations: Dict[str, AnimationData] = {}
        for anim_name, files in animation_files.items():
            animations[anim_name] = self._load_animation(anim_name, files)

        self._cache[entity_name] = animations
        return animations

    def _scan_animation_files(self, folder_path: Path) -> Dict[str, List[Tuple[int, Path]]]:
        """
        扫描文件夹，按动画名称分组文件

        文件命名格式: <animation_name>_<frame_number>.<ext>
        例如: walk_0.png, walk_1.png, attack_0.png, attack_15.png

        Returns:
            {动画名称: [(帧序号, 文件路径), ...]}
        """
        pattern = re.compile(r'^(.+)_(\d+)$')
        animation_files: Dict[str, List[Tuple[int, Path]]] = {}

        for file_path in folder_path.iterdir():
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            # 解析文件名
            stem = file_path.stem  # 不含扩展名
            match = pattern.match(stem)

            if match:
                anim_name = match.group(1)
                frame_num = int(match.group(2))

                if anim_name not in animation_files:
                    animation_files[anim_name] = []

                animation_files[anim_name].append((frame_num, file_path))

        # 按帧序号排序
        for anim_name in animation_files:
            animation_files[anim_name].sort(key=lambda x: x[0])

        return animation_files

    def _load_animation(self, anim_name: str, files: List[Tuple[int, Path]]) -> AnimationData:
        """
        加载单个动画的所有帧，并生成四个方向

        方向生成（使用翻转而非旋转）：
        - RIGHT: 原图
        - LEFT: 水平翻转
        - UP: 和 RIGHT 一样（原图）
        - DOWN: 和 LEFT 一样（水平翻转）

        Args:
            anim_name: 动画名称
            files: [(帧序号, 文件路径), ...]

        Returns:
            AnimationData
        """
        frames_by_direction: Dict[Direction, List[Surface]] = {
            Direction.RIGHT: [],
            Direction.UP: [],
            Direction.LEFT: [],
            Direction.DOWN: [],
        }

        for frame_num, file_path in files:
            # 加载原始图片
            original = pygame.image.load(str(file_path)).convert_alpha()

            # 生成四个方向（使用翻转）
            flipped = pygame.transform.flip(original, True, False)  # 水平翻转

            frames_by_direction[Direction.RIGHT].append(original)
            frames_by_direction[Direction.UP].append(original)  # 上和右一样
            frames_by_direction[Direction.LEFT].append(flipped)
            frames_by_direction[Direction.DOWN].append(flipped)  # 下和左一样

        return AnimationData(
            name=anim_name,
            frames=frames_by_direction,
            frame_count=len(files)
        )

    def load_single_sprite(self, entity_name: str, sprite_name: str) -> Dict[Direction, Surface]:
        """
        加载单个精灵图片（非动画），生成四个方向

        Args:
            entity_name: 实体/文件夹名称
            sprite_name: 精灵文件名（不含扩展名）

        Returns:
            {Direction: Surface}
        """
        entity_path = self.base_path / entity_name

        # 查找匹配的文件
        for ext in self.SUPPORTED_EXTENSIONS:
            file_path = entity_path / f"{sprite_name}{ext}"
            if file_path.exists():
                original = pygame.image.load(str(file_path)).convert_alpha()
                return {
                    Direction.RIGHT: original,
                    Direction.UP: pygame.transform.rotate(original, 90),
                    Direction.LEFT: pygame.transform.rotate(original, 180),
                    Direction.DOWN: pygame.transform.rotate(original, 270),
                }

        raise FileNotFoundError(f"Sprite not found: {entity_path / sprite_name}")

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()

    def get_animation_info(self, entity_name: str) -> Dict[str, int]:
        """
        获取实体动画信息（帧数统计）

        Returns:
            {动画名称: 帧数}
        """
        animations = self.load_entity(entity_name)
        return {name: anim.frame_count for name, anim in animations.items()}


# ============================================================
# 便捷函数
# ============================================================

def load_player_animations(base_path: str = "assets/sprites",
                           player_folder: str = "playerA") -> Dict[str, AnimationData]:
    """
    快捷加载玩家动画

    Returns:
        {"walk": AnimationData, "attack": AnimationData, ...}
    """
    loader = ResourceLoader(base_path)
    return loader.load_entity(player_folder)


def load_monster_animations(base_path: str = "assets/sprites",
                            monster_folder: str = "slime") -> Dict[str, AnimationData]:
    """
    快捷加载怪物动画
    """
    loader = ResourceLoader(base_path)
    return loader.load_entity(f"monsters/{monster_folder}")


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    # 测试资源加载器

    # 初始化 Pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Resource Loader Test")
    clock = pygame.time.Clock()

    # 创建测试目录结构
    test_path = Path("assets/sprites/playerA")
    test_path.mkdir(parents=True, exist_ok=True)

    # 生成测试图片（如果没有真实资源）
    print("Testing Resource Loader...")
    print(f"Test path: {test_path.absolute()}")

    # 尝试加载
    try:
        loader = ResourceLoader("assets/sprites")
        info = loader.get_animation_info("playerA")
        print(f"Found animations: {info}")

        # 显示动画信息
        animations = loader.load_entity("playerA")
        for anim_name, anim_data in animations.items():
            print(f"\nAnimation: {anim_name}")
            print(f"  Frames: {anim_data.frame_count}")
            print(f"  Directions: {list(anim_data.frames.keys())}")

    except FileNotFoundError as e:
        print(f"Expected (no resources yet): {e}")
        print("\nTo test, create files like:")
        print("  assets/sprites/playerA/walk_0.png")
        print("  assets/sprites/playerA/walk_1.png")
        print("  assets/sprites/playerA/attack_0.png")
        print("  ...")

    pygame.quit()
