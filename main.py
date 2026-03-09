#!/usr/bin/env python
"""
Magic Tower Game - 游戏入口

启动游戏的主文件
"""

import sys
from engine.game import Game


def main():
    """游戏入口函数"""
    game = Game(
        width=800,
        height=600,
        title="Magic Tower",
        fps=60
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
