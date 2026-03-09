"""
Animation System - 动画播放控制器

与 ResourceLoader 配合使用，播放加载好的动画
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

import pygame
from pygame.surface import Surface

# 导入资源加载器
from systems.resource_loader import Direction, AnimationData, ResourceLoader


@dataclass
class AnimationConfig:
    """动画配置"""
    frame_duration: float = 0.1   # 每帧持续时间（秒）
    loop: bool = True             # 是否循环播放


class AnimationPlayer:
    """
    动画播放器

    负责管理单个实体的动画播放状态

    使用示例:
        # 加载资源
        loader = ResourceLoader("assets/sprites")
        animations = loader.load_entity("playerA")

        # 创建播放器
        player = AnimationPlayer(animations)
        player.set_config("walk", frame_duration=0.08, loop=True)
        player.set_config("attack", frame_duration=0.05, loop=False)

        # 播放动画
        player.play("walk", Direction.RIGHT)

        # 更新和渲染
        player.update(delta_time)
        player.draw(screen, (100, 100))
    """

    def __init__(self, animations: Dict[str, AnimationData]):
        """
        初始化动画播放器

        Args:
            animations: 从 ResourceLoader 加载的动画数据
        """
        self.animations = animations
        self.configs: Dict[str, AnimationConfig] = {}

        # 当前播放状态
        self.current_animation: Optional[str] = None
        self.current_direction: Direction = Direction.RIGHT
        self.current_frame: int = 0
        self.time_elapsed: float = 0.0
        self.is_playing: bool = False
        self.animation_finished: bool = False

        # 为每个动画设置默认配置
        for anim_name in animations:
            self.configs[anim_name] = AnimationConfig()

    def set_config(self, animation_name: str,
                   frame_duration: float = 0.1,
                   loop: bool = True):
        """
        设置动画配置

        Args:
            animation_name: 动画名称
            frame_duration: 每帧持续时间（秒）
            loop: 是否循环
        """
        self.configs[animation_name] = AnimationConfig(
            frame_duration=frame_duration,
            loop=loop
        )

    def play(self, animation_name: str, direction: Direction,
             restart: bool = False):
        """
        播放指定动画

        Args:
            animation_name: 动画名称
            direction: 方向
            restart: 是否从头开始（即使正在播放同一动画）
        """
        if animation_name not in self.animations:
            raise ValueError(f"Animation not found: {animation_name}")

        # 如果是同一动画且不重启，则只更新方向
        if (self.current_animation == animation_name and
            not restart and
            self.current_direction == direction):
            return

        self.current_animation = animation_name
        self.current_direction = direction
        self.current_frame = 0
        self.time_elapsed = 0.0
        self.is_playing = True
        self.animation_finished = False

    def stop(self):
        """停止播放"""
        self.is_playing = False

    def resume(self):
        """继续播放"""
        if self.current_animation:
            self.is_playing = True

    def reset(self):
        """重置到第一帧"""
        self.current_frame = 0
        self.time_elapsed = 0.0
        self.animation_finished = False

    def set_direction(self, direction: Direction):
        """设置方向（不重置动画）"""
        self.current_direction = direction

    def update(self, delta_time: float):
        """
        更新动画状态

        Args:
            delta_time: 时间增量（秒）
        """
        if not self.is_playing or not self.current_animation:
            return

        config = self.configs[self.current_animation]
        self.time_elapsed += delta_time

        # 检查是否需要切换帧
        if self.time_elapsed >= config.frame_duration:
            self.time_elapsed -= config.frame_duration
            self.current_frame += 1

            animation = self.animations[self.current_animation]

            # 检查是否到达最后一帧
            if self.current_frame >= animation.frame_count:
                if config.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = animation.frame_count - 1
                    self.is_playing = False
                    self.animation_finished = True

    def get_current_frame(self) -> Optional[Surface]:
        """
        获取当前帧的 Surface

        Returns:
            当前帧图片，如果没有播放动画则返回 None
        """
        if not self.current_animation:
            return None

        animation = self.animations[self.current_animation]
        frames = animation.frames[self.current_direction]

        if 0 <= self.current_frame < len(frames):
            return frames[self.current_frame]

        return None

    def draw(self, surface: Surface, position: tuple,
             center: bool = False):
        """
        绘制当前帧

        Args:
            surface: 目标 Surface
            position: 绘制位置
            center: 是否以中心点对齐
        """
        frame = self.get_current_frame()
        if frame is None:
            return

        if center:
            # 居中对齐
            rect = frame.get_rect(center=position)
            surface.blit(frame, rect)
        else:
            surface.blit(frame, position)

    def get_frame_size(self) -> tuple:
        """获取帧尺寸"""
        frame = self.get_current_frame()
        if frame:
            return frame.get_size()
        return (0, 0)

    def get_pivot(self) -> tuple:
        """
        获取当前帧的 pivot 点（底部中部）

        Returns:
            (pivot_x, pivot_y) 相对于图片左上角的偏移
        """
        width, height = self.get_frame_size()
        return (width // 2, height)

    def get_animation_names(self) -> list:
        """获取所有动画名称"""
        return list(self.animations.keys())

    def is_animation_complete(self) -> bool:
        """检查非循环动画是否播放完成"""
        return self.animation_finished


# ============================================================
# AnimatedEntity - 带动画的实体基类
# ============================================================

class AnimatedEntity:
    """
    带动画的实体基类

    使用示例:
        class Player(AnimatedEntity):
            def __init__(self, x, y):
                super().__init__("assets/sprites", "playerA")
                self.x = x
                self.y = y

            def move(self, dx, dy):
                # 更新位置
                self.x += dx
                self.y += dy

                # 根据移动方向设置动画
                if dx > 0:
                    self.set_direction(Direction.RIGHT)
                elif dx < 0:
                    self.set_direction(Direction.LEFT)
                elif dy > 0:
                    self.set_direction(Direction.DOWN)
                elif dy < 0:
                    self.set_direction(Direction.UP)

                # 播放行走动画
                self.play_animation("walk")

            def attack(self):
                self.play_animation("attack", restart=True)
    """

    def __init__(self, resource_path: str, entity_name: str):
        """
        初始化实体

        Args:
            resource_path: 资源根目录
            entity_name: 实体文件夹名称
        """
        loader = ResourceLoader(resource_path)
        animations = loader.load_entity(entity_name)

        self.animation_player = AnimationPlayer(animations)
        self.facing_direction = Direction.RIGHT

    def set_animation_config(self, animation_name: str,
                              frame_duration: float = 0.1,
                              loop: bool = True):
        """设置动画配置"""
        self.animation_player.set_config(animation_name, frame_duration, loop)

    def play_animation(self, animation_name: str, restart: bool = False):
        """播放动画"""
        self.animation_player.play(
            animation_name,
            self.facing_direction,
            restart
        )

    def set_direction(self, direction: Direction):
        """设置朝向"""
        self.facing_direction = direction
        self.animation_player.set_direction(direction)

    def update(self, delta_time: float):
        """更新实体状态"""
        self.animation_player.update(delta_time)

    def draw(self, surface: Surface, position: tuple):
        """绘制实体"""
        self.animation_player.draw(surface, position)


# ============================================================
# 使用示例 / 演示代码
# ============================================================

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Animation System Demo")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    # 创建资源加载器
    loader = ResourceLoader("assets/sprites")

    # 尝试加载玩家动画
    try:
        player_animations = loader.load_entity("playerA")
        player = AnimationPlayer(player_animations)

        # 配置动画速度
        player.set_config("walk", frame_duration=0.08, loop=True)
        player.set_config("attack", frame_duration=0.05, loop=False)

        # 开始播放
        player.play("walk", Direction.RIGHT)

        print("Animation system initialized successfully!")
        print(f"Available animations: {player.get_animation_names()}")

    except FileNotFoundError:
        print("No resources found. Creating placeholder...")

        # 创建占位符演示
        placeholder_frames = {
            Direction.RIGHT: [pygame.Surface((32, 32)) for _ in range(4)],
            Direction.UP: [pygame.Surface((32, 32)) for _ in range(4)],
            Direction.LEFT: [pygame.Surface((32, 32)) for _ in range(4)],
            Direction.DOWN: [pygame.Surface((32, 32)) for _ in range(4)],
        }

        # 填充不同颜色作为占位符
        colors = [(100, 200, 100), (120, 220, 120), (100, 200, 100), (80, 180, 80)]
        for direction, frames in placeholder_frames.items():
            for i, frame in enumerate(frames):
                frame.fill(colors[i])

        from systems.resource_loader import AnimationData
        placeholder_anim = AnimationData("walk", placeholder_frames, 4)
        player = AnimationPlayer({"walk": placeholder_anim})
        player.play("walk", Direction.RIGHT)

    # 主循环
    running = True
    current_direction = Direction.RIGHT
    directions = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
    dir_index = 0

    while running:
        delta_time = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # 切换方向
                    dir_index = (dir_index + 1) % 4
                    current_direction = directions[dir_index]
                    player.set_direction(current_direction)

        # 更新
        player.update(delta_time)

        # 绘制
        screen.fill((30, 30, 40))
        player.draw(screen, (384, 284))

        # 显示方向
        dir_text = font.render(f"Direction: {current_direction.name} (SPACE to change)", True, (255, 255, 255))
        screen.blit(dir_text, (10, 10))

        pygame.display.flip()

    pygame.quit()
