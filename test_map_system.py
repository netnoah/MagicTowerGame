"""
地图系统测试

这个测试脚本验证瓦片加载和地图渲染功能
"""

import pygame
import sys
import os

# 设置项目路径
project_root = os.path.dirname(os.path.abspath())
sys.path.insert(0, project_root)

from systems.tile import TileManager
from systems.floor_manager import FloorManager

print("Loading tiles...")
tile_manager = TileManager()
tile_manager.load_tiles()

print("Loading floor manager...")
floor_manager = FloorManager()
floor_manager.load_tiles()

# 加载第一层
print("Loading floor 1...")
success = floor_manager.load_floor(1)

if success:
    print(f"  - Map size: {floor_manager.map_width}x{floor_manager.map_height}")
    print(f"  - Tiles loaded: {len(tile_manager._tile_surfaces)}")
    print(f"  - Player start: {floor_manager.get_player_start()}")

    # 渲染地图
    screen = pygame.display.set_mode((800, 600))
    offset = floor_manager.calculate_render_offset(800, 600)
    floor_manager.render(screen, offset)

    print("Map rendered! Press ESC to close.")

    # 保持窗口开一会儿
    pygame.time.delay(2000)

    pygame.quit()
    print("Test completed!")
