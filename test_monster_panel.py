"""
测试怪物信息面板

运行此脚本来验证面板是否能正确显示
"""

import pygame
import sys

# 初始化 pygame
pygame.init()

# 创建窗口
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Monster Info Panel Test")

# 导入 UI 组件
from ui.hud import MonsterInfoPanel

# 创建面板
panel = MonsterInfoPanel()

# 测试数据
test_monsters = [
    {
        'name': 'Slime',
        'hp': 50,
        'atk': 10,
        'def': 5,
        'can_win': True,
        'damage_taken': 20,
        'rounds': 5,
        'count': 3
    },
    {
        'name': 'Bat',
        'hp': 30,
        'atk': 15,
        'def': 2,
        'can_win': True,
        'damage_taken': 5,
        'rounds': 3,
        'count': 2
    },
    {
        'name': 'Skeleton',
        'hp': 100,
        'atk': 25,
        'def': 10,
        'can_win': False,
        'damage_taken': 0,
        'rounds': 0,
        'count': 1
    },
]

# 更新面板数据
panel.update_data(floor=1, monster_info_list=test_monsters)

# 打开面板
panel.toggle()
print(f"Panel visible: {panel.is_visible()}")
print(f"Panel position: ({panel._x}, {panel._y})")
print(f"Panel size: {panel._width}x{panel._height}")

# 主循环
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_o:
                panel.toggle()
                print(f"Panel visible: {panel.is_visible()}")
            elif event.key == pygame.K_UP:
                panel.scroll_up()
                print("Scroll up")
            elif event.key == pygame.K_DOWN:
                panel.scroll_down()
                print("Scroll down")

    # 清屏
    screen.fill((30, 30, 40))

    # 绘制一些背景内容
    font = pygame.font.Font(None, 24)
    text = font.render("Press ctrl to toggle panel, ESC to quit", True, (150, 150, 150))
    screen.blit(text, (20, 20))

    # 渲染面板
    panel.render(screen)

    # 更新显示
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
