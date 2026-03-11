#!/usr/bin/env python
"""
Magic Tower Game - 游戏入口

启动游戏的主文件
"""

import sys
from config import WindowConfig  # 1. 导入配置
from engine.game import Game


def main():
    """游戏入口函数"""
    game = Game(
        width=WindowConfig.WIDTH,   # 2. 使用配置值
        height=WindowConfig.HEIGHT, # 2. 使用配置值
        title=WindowConfig.TITLE,
        fps=WindowConfig.FPS
    )

    try:
        game.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Game error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()