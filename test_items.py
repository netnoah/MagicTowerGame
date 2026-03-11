"""
物品系统测试脚本
"""

import sys
sys.path.insert(0, '.')

from systems.items import (
    ItemManager, ItemType, ItemRarity, ItemEffect, create_default_items
)
from entities.player import PlayerStats


def test_item_manager():
    """测试物品管理器"""
    print("=" * 50)
    print("测试物品管理器")
    print("=" * 50)

    manager = ItemManager()

    # 从JSON加载
    success = manager.load_from_json("data/entities/items.json")
    print(f"JSON加载: {'成功' if success else '失败'}")

    # 检查物品数量
    items = manager.get_all_items()
    print(f"物品总数: {len(items)}")

    # 按类型统计
    for item_type in ItemType:
        type_items = manager.get_items_by_type(item_type)
        print(f"  {item_type.value}: {len(type_items)}")

    # 获取一个物品
    sword = manager.get_item("iron_sword")
    if sword:
        print(f"\n物品详情: {sword.name_cn}")
        print(f"  类型: {sword.item_type.value}")
        print(f"  描述: {sword.description}")
        print(f"  价格: {sword.price}G")
        print(f"  稀有度: {sword.rarity.value}")


def test_item_effect():
    """测试物品效果"""
    print("\n" + "=" * 50)
    print("测试物品效果")
    print("=" * 50)

    # 创建玩家属性
    stats = PlayerStats()
    print(f"初始属性: HP={stats.hp}, ATK={stats.attack}, DEF={stats.defense}, Gold={stats.gold}")

    # 测试药水效果
    effect = ItemEffect(hp=100)
    changes = effect.apply(stats)
    print(f"使用药水(+100HP): {changes}")
    print(f"当前HP: {stats.hp}/{stats.max_hp}")

    # 测试武器效果
    effect = ItemEffect(attack=25)
    changes = effect.apply(stats)
    print(f"装备武器(+25ATK): {changes}")
    print(f"当前攻击: {stats.attack}")

    # 测试防具效果
    effect = ItemEffect(defense=15)
    changes = effect.apply(stats)
    print(f"装备防具(+15DEF): {changes}")
    print(f"当前防御: {stats.defense}")

    # 测试生命水晶
    effect = ItemEffect(max_hp=100)
    changes = effect.apply(stats)
    print(f"使用生命水晶(+100最大HP): {changes}")
    print(f"当前HP: {stats.hp}/{stats.max_hp}")


def test_item_use():
    """测试物品使用"""
    print("\n" + "=" * 50)
    print("测试物品使用")
    print("=" * 50)

    # 使用默认物品
    items = create_default_items()

    # 创建玩家属性
    stats = PlayerStats()
    print(f"初始HP: {stats.hp}/{stats.max_hp}")

    # 测试小药水
    potion = items["small_potion"]
    print(f"\n使用 {potion.name_cn}: {potion.description}")
    if potion.can_use(stats):
        changes = potion.use(stats)
        print(f"效果: {changes}")
        print(f"当前HP: {stats.hp}/{stats.max_hp}")
    else:
        print("无法使用")

    # 测试满血时使用药水
    stats.hp = stats.max_hp
    print(f"\nHP已满: {stats.hp}/{stats.max_hp}")
    print(f"能否使用药水: {potion.can_use(stats)}")

    # 测试钥匙（不能直接使用）
    key = items["yellow_key"]
    print(f"\n钥匙 {key.name_cn} 能否直接使用: {key.can_use(stats)}")

    # 测试武器
    sword = items["iron_sword"]
    print(f"\n装备 {sword.name_cn}: {sword.description}")
    changes = sword.use(stats)
    print(f"效果: {changes}")
    print(f"当前攻击: {stats.attack}")


def test_default_items():
    """测试默认物品"""
    print("\n" + "=" * 50)
    print("测试默认物品")
    print("=" * 50)

    items = create_default_items()
    print(f"默认物品数量: {len(items)}")

    # 列出所有物品
    for item_id, item in items.items():
        effect_str = ""
        if item.effect:
            effects = []
            if item.effect.hp:
                effects.append(f"HP{item.effect.hp:+d}")
            if item.effect.max_hp:
                effects.append(f"MaxHP{item.effect.max_hp:+d}")
            if item.effect.attack:
                effects.append(f"ATK{item.effect.attack:+d}")
            if item.effect.defense:
                effects.append(f"DEF{item.effect.defense:+d}")
            if item.effect.gold:
                effects.append(f"Gold{item.effect.gold:+d}")
            if item.effect.yellow_keys:
                effects.append(f"黄钥匙{item.effect.yellow_keys:+d}")
            if item.effect.blue_keys:
                effects.append(f"蓝钥匙{item.effect.blue_keys:+d}")
            if item.effect.red_keys:
                effects.append(f"红钥匙{item.effect.red_keys:+d}")
            effect_str = ", ".join(effects)

        print(f"  [{item.rarity.value:9}] {item.name_cn:10} | {item.item_type.value:7} | {effect_str}")


if __name__ == "__main__":
    test_item_manager()
    test_item_effect()
    test_item_use()
    test_default_items()
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
