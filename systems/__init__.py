"""
Systems Module - 游戏系统模块

包含:
- resource_loader: 资源加载器（自动加载图片并生成多方向动画）
- animation: 动画播放系统
"""

from systems.resource_loader import (
    ResourceLoader,
    Direction,
    AnimationData,
    load_player_animations,
    load_monster_animations,
)

from systems.animation import (
    AnimationPlayer,
    AnimationConfig,
    AnimatedEntity,
)

__all__ = [
    # Resource Loader
    'ResourceLoader',
    'Direction',
    'AnimationData',
    'load_player_animations',
    'load_monster_animations',

    # Animation
    'AnimationPlayer',
    'AnimationConfig',
    'AnimatedEntity',
]
