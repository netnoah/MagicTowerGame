"""
Items System - 物品系统

管理游戏中所有物品的定义、效果和使用
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
from pathlib import Path

from entities.player import PlayerStats


class ItemType(Enum):
    """物品类型"""
    KEY = "key"              # 钥匙
    POTION = "potion"        # 药水（消耗品）
    WEAPON = "weapon"        # 武器（装备）
    ARMOR = "armor"          # 防具（装备）
    SPECIAL = "special"      # 特殊物品


class ItemRarity(Enum):
    """物品稀有度"""
    COMMON = "common"        # 普通
    UNCOMMON = "uncommon"    # 稀有
    RARE = "rare"            # 精良
    EPIC = "epic"            # 史诗
    LEGENDARY = "legendary"  # 传说


@dataclass
class ItemEffect:
    """
    物品效果

    定义物品使用后对玩家属性的影响
    """
    hp: int = 0              # HP 变化（正数恢复，负数伤害）
    max_hp: int = 0          # 最大 HP 变化
    attack: int = 0          # 攻击力变化
    defense: int = 0         # 防御力变化
    gold: int = 0            # 金币变化
    experience: int = 0      # 经验变化
    yellow_keys: int = 0     # 黄钥匙变化
    blue_keys: int = 0       # 蓝钥匙变化
    red_keys: int = 0        # 红钥匙变化

    def apply(self, stats: PlayerStats) -> Dict[str, int]:
        """
        应用效果到玩家属性

        Args:
            stats: 玩家属性对象

        Returns:
            实际变化的属性字典
        """
        changes: Dict[str, int] = {}

        if self.hp != 0:
            old_hp = stats.hp
            stats.hp = max(0, min(stats.max_hp + self.max_hp, stats.hp + self.hp))
            changes['hp'] = stats.hp - old_hp

        if self.max_hp != 0:
            old_max = stats.max_hp
            stats.max_hp = max(1, stats.max_hp + self.max_hp)
            changes['max_hp'] = stats.max_hp - old_max
            # 如果增加了最大HP，同时恢复等量HP
            if self.max_hp > 0:
                stats.hp = min(stats.max_hp, stats.hp + self.max_hp)

        if self.attack != 0:
            old_atk = stats.attack
            stats.attack = max(0, stats.attack + self.attack)
            changes['attack'] = stats.attack - old_atk

        if self.defense != 0:
            old_def = stats.defense
            stats.defense = max(0, stats.defense + self.defense)
            changes['defense'] = stats.defense - old_def

        if self.gold != 0:
            old_gold = stats.gold
            stats.gold = max(0, stats.gold + self.gold)
            changes['gold'] = stats.gold - old_gold

        if self.experience != 0:
            old_exp = stats.experience
            stats.experience = max(0, stats.experience + self.experience)
            changes['experience'] = stats.experience - old_exp

        if self.yellow_keys != 0:
            old = stats.yellow_keys
            stats.yellow_keys = max(0, stats.yellow_keys + self.yellow_keys)
            changes['yellow_keys'] = stats.yellow_keys - old

        if self.blue_keys != 0:
            old = stats.blue_keys
            stats.blue_keys = max(0, stats.blue_keys + self.blue_keys)
            changes['blue_keys'] = stats.blue_keys - old

        if self.red_keys != 0:
            old = stats.red_keys
            stats.red_keys = max(0, stats.red_keys + self.red_keys)
            changes['red_keys'] = stats.red_keys - old

        return changes


@dataclass
class ItemData:
    """
    物品数据

    定义物品的基本属性
    """
    id: str                          # 物品唯一ID
    name: str                        # 显示名称
    name_cn: str                     # 中文名称
    item_type: ItemType              # 物品类型
    description: str = ""            # 描述
    effect: Optional[ItemEffect] = None  # 物品效果
    price: int = 0                   # 售价（金币）
    sell_price: int = 0              # 卖出价格
    stackable: bool = True           # 是否可堆叠
    max_stack: int = 99              # 最大堆叠数量
    consumable: bool = True          # 是否消耗品（使用后消失）
    rarity: ItemRarity = ItemRarity.COMMON  # 稀有度
    sprite: str = ""                 # 精灵图名称

    def can_use(self, stats: PlayerStats) -> bool:
        """
        检查是否可以使用

        Args:
            stats: 玩家属性

        Returns:
            是否可以使用
        """
        # 钥匙类物品不能直接使用
        if self.item_type == ItemType.KEY:
            return False

        # 药水类：HP已满时不能使用恢复药水
        if self.item_type == ItemType.POTION and self.effect:
            if self.effect.hp > 0 and stats.hp >= stats.max_hp:
                return False

        return True

    def use(self, stats: PlayerStats) -> Optional[Dict[str, int]]:
        """
        使用物品

        Args:
            stats: 玩家属性

        Returns:
            效果变化字典，失败返回 None
        """
        if not self.can_use(stats):
            return None

        if not self.effect:
            return None

        return self.effect.apply(stats)


class ItemManager:
    """
    物品管理器

    管理所有物品定义，支持从JSON加载
    """

    def __init__(self):
        self._items: Dict[str, ItemData] = {}

    def load_from_json(self, filepath: str) -> bool:
        """
        从JSON文件加载物品定义

        Args:
            filepath: JSON文件路径

        Returns:
            是否加载成功
        """
        try:
            path = Path(filepath)
            if not path.exists():
                print(f"Items file not found: {filepath}")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            items_data = data.get('items', {})
            for item_id, item_info in items_data.items():
                item = self._parse_item(item_id, item_info)
                if item:
                    self._items[item_id] = item

            print(f"Loaded {len(self._items)} items from {filepath}")
            return True

        except Exception as e:
            print(f"Failed to load items: {e}")
            return False

    def _parse_item(self, item_id: str, data: Dict[str, Any]) -> Optional[ItemData]:
        """解析物品数据"""
        try:
            # 解析物品类型
            item_type = ItemType(data.get('type', 'special'))

            # 解析效果
            effect = None
            if 'effect' in data:
                effect = ItemEffect(
                    hp=data['effect'].get('hp', 0),
                    max_hp=data['effect'].get('max_hp', 0),
                    attack=data['effect'].get('attack', 0),
                    defense=data['effect'].get('defense', 0),
                    gold=data['effect'].get('gold', 0),
                    experience=data['effect'].get('experience', 0),
                    yellow_keys=data['effect'].get('yellow_keys', 0),
                    blue_keys=data['effect'].get('blue_keys', 0),
                    red_keys=data['effect'].get('red_keys', 0),
                )

            # 解析稀有度
            rarity_str = data.get('rarity', 'common')
            rarity = ItemRarity(rarity_str)

            return ItemData(
                id=item_id,
                name=data.get('name', item_id),
                name_cn=data.get('name_cn', item_id),
                item_type=item_type,
                description=data.get('description', ''),
                effect=effect,
                price=data.get('price', 0),
                sell_price=data.get('sell_price', data.get('price', 0) // 2),
                stackable=data.get('stackable', True),
                max_stack=data.get('max_stack', 99),
                consumable=data.get('consumable', item_type != ItemType.WEAPON and item_type != ItemType.ARMOR),
                rarity=rarity,
                sprite=data.get('sprite', item_id),
            )

        except Exception as e:
            print(f"Failed to parse item {item_id}: {e}")
            return None

    def get_item(self, item_id: str) -> Optional[ItemData]:
        """获取物品定义"""
        return self._items.get(item_id)

    def get_all_items(self) -> Dict[str, ItemData]:
        """获取所有物品"""
        return self._items.copy()

    def get_items_by_type(self, item_type: ItemType) -> List[ItemData]:
        """按类型获取物品"""
        return [item for item in self._items.values() if item.item_type == item_type]

    def get_items_by_rarity(self, rarity: ItemRarity) -> List[ItemData]:
        """按稀有度获取物品"""
        return [item for item in self._items.values() if item.rarity == rarity]


# ============================================================
# 预定义的物品效果
# ============================================================

def create_default_items() -> Dict[str, ItemData]:
    """
    创建默认物品定义

    用于没有JSON文件时的备用方案
    """
    return {
        # 钥匙
        "yellow_key": ItemData(
            id="yellow_key",
            name="Yellow Key",
            name_cn="黄钥匙",
            item_type=ItemType.KEY,
            description="打开黄色门",
            effect=ItemEffect(yellow_keys=1),
            price=10,
            sell_price=5,
            stackable=True,
            consumable=False,
            sprite="yellow_key",
        ),
        "blue_key": ItemData(
            id="blue_key",
            name="Blue Key",
            name_cn="蓝钥匙",
            item_type=ItemType.KEY,
            description="打开蓝色门",
            effect=ItemEffect(blue_keys=1),
            price=50,
            sell_price=25,
            stackable=True,
            consumable=False,
            sprite="blue_key",
        ),
        "red_key": ItemData(
            id="red_key",
            name="Red Key",
            name_cn="红钥匙",
            item_type=ItemType.KEY,
            description="打开红色门",
            effect=ItemEffect(red_keys=1),
            price=100,
            sell_price=50,
            stackable=True,
            consumable=False,
            sprite="red_key",
        ),

        # 药水
        "small_potion": ItemData(
            id="small_potion",
            name="Small Potion",
            name_cn="小药水",
            item_type=ItemType.POTION,
            description="恢复100点HP",
            effect=ItemEffect(hp=100),
            price=50,
            sell_price=25,
            stackable=True,
            consumable=True,
            rarity=ItemRarity.COMMON,
            sprite="potion_small",
        ),
        "medium_potion": ItemData(
            id="medium_potion",
            name="Medium Potion",
            name_cn="中药水",
            item_type=ItemType.POTION,
            description="恢复300点HP",
            effect=ItemEffect(hp=300),
            price=150,
            sell_price=75,
            stackable=True,
            consumable=True,
            rarity=ItemRarity.UNCOMMON,
            sprite="potion_medium",
        ),
        "large_potion": ItemData(
            id="large_potion",
            name="Large Potion",
            name_cn="大药水",
            item_type=ItemType.POTION,
            description="恢复500点HP",
            effect=ItemEffect(hp=500),
            price=300,
            sell_price=150,
            stackable=True,
            consumable=True,
            rarity=ItemRarity.RARE,
            sprite="potion_large",
        ),
        "full_potion": ItemData(
            id="full_potion",
            name="Full Restore",
            name_cn="完全恢复药",
            item_type=ItemType.POTION,
            description="完全恢复HP",
            effect=ItemEffect(hp=9999),  # 足够大的值
            price=500,
            sell_price=250,
            stackable=True,
            consumable=True,
            rarity=ItemRarity.EPIC,
            sprite="potion_full",
        ),

        # 武器
        "iron_sword": ItemData(
            id="iron_sword",
            name="Iron Sword",
            name_cn="铁剑",
            item_type=ItemType.WEAPON,
            description="攻击力+10",
            effect=ItemEffect(attack=10),
            price=100,
            sell_price=50,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.COMMON,
            sprite="sword_iron",
        ),
        "steel_sword": ItemData(
            id="steel_sword",
            name="Steel Sword",
            name_cn="钢剑",
            item_type=ItemType.WEAPON,
            description="攻击力+25",
            effect=ItemEffect(attack=25),
            price=300,
            sell_price=150,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.UNCOMMON,
            sprite="sword_steel",
        ),
        "silver_sword": ItemData(
            id="silver_sword",
            name="Silver Sword",
            name_cn="银剑",
            item_type=ItemType.WEAPON,
            description="攻击力+50",
            effect=ItemEffect(attack=50),
            price=800,
            sell_price=400,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.RARE,
            sprite="sword_silver",
        ),
        "holy_sword": ItemData(
            id="holy_sword",
            name="Holy Sword",
            name_cn="圣剑",
            item_type=ItemType.WEAPON,
            description="攻击力+100",
            effect=ItemEffect(attack=100),
            price=2000,
            sell_price=1000,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.EPIC,
            sprite="sword_holy",
        ),
        "legend_sword": ItemData(
            id="legend_sword",
            name="Legendary Sword",
            name_cn="传说之剑",
            item_type=ItemType.WEAPON,
            description="攻击力+200",
            effect=ItemEffect(attack=200),
            price=5000,
            sell_price=2500,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.LEGENDARY,
            sprite="sword_legend",
        ),

        # 防具
        "leather_armor": ItemData(
            id="leather_armor",
            name="Leather Armor",
            name_cn="皮甲",
            item_type=ItemType.ARMOR,
            description="防御力+10",
            effect=ItemEffect(defense=10),
            price=100,
            sell_price=50,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.COMMON,
            sprite="armor_leather",
        ),
        "chain_armor": ItemData(
            id="chain_armor",
            name="Chain Armor",
            name_cn="锁子甲",
            item_type=ItemType.ARMOR,
            description="防御力+25",
            effect=ItemEffect(defense=25),
            price=300,
            sell_price=150,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.UNCOMMON,
            sprite="armor_chain",
        ),
        "plate_armor": ItemData(
            id="plate_armor",
            name="Plate Armor",
            name_cn="板甲",
            item_type=ItemType.ARMOR,
            description="防御力+50",
            effect=ItemEffect(defense=50),
            price=800,
            sell_price=400,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.RARE,
            sprite="armor_plate",
        ),
        "holy_armor": ItemData(
            id="holy_armor",
            name="Holy Armor",
            name_cn="圣甲",
            item_type=ItemType.ARMOR,
            description="防御力+100",
            effect=ItemEffect(defense=100),
            price=2000,
            sell_price=1000,
            stackable=False,
            consumable=False,
            rarity=ItemRarity.EPIC,
            sprite="armor_holy",
        ),

        # 特殊物品
        "gold_coin_small": ItemData(
            id="gold_coin_small",
            name="Small Gold Bag",
            name_cn="小金币袋",
            item_type=ItemType.SPECIAL,
            description="获得50金币",
            effect=ItemEffect(gold=50),
            price=0,
            sell_price=50,
            stackable=True,
            consumable=True,
            rarity=ItemRarity.COMMON,
            sprite="gold_small",
        ),
        "gold_coin_large": ItemData(
            id="gold_coin_large",
            name="Large Gold Bag",
            name_cn="大金币袋",
            item_type=ItemType.SPECIAL,
            description="获得200金币",
            effect=ItemEffect(gold=200),
            price=0,
            sell_price=200,
            stackable=True,
            consumable=True,
            rarity=ItemRarity.UNCOMMON,
            sprite="gold_large",
        ),
        "exp_book": ItemData(
            id="exp_book",
            name="Experience Book",
            name_cn="经验之书",
            item_type=ItemType.SPECIAL,
            description="获得50经验",
            effect=ItemEffect(experience=50),
            price=100,
            sell_price=50,
            stackable=True,
            consumable=True,
            rarity=ItemRarity.UNCOMMON,
            sprite="book_exp",
        ),
        "life_crystal": ItemData(
            id="life_crystal",
            name="Life Crystal",
            name_cn="生命水晶",
            item_type=ItemType.SPECIAL,
            description="最大HP+100",
            effect=ItemEffect(max_hp=100),
            price=500,
            sell_price=250,
            stackable=True,
            consumable=True,
            rarity=ItemRarity.RARE,
            sprite="crystal_life",
        ),
    }
