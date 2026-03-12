"""
Shop System - 商店系统

管理商店数据、交易逻辑和属性升级
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from pathlib import Path

from entities.player import PlayerStats
from systems.items import ItemManager, ItemData, ItemEffect


class UpgradeType(Enum):
    """属性升级类型"""
    ATTACK = "attack"
    DEFENSE = "defense"
    MAX_HP = "max_hp"


@dataclass
class ShopItem:
    """商店物品"""
    item_id: str          # 物品ID
    price: int            # 价格（覆盖默认价格）
    item_data: Optional[ItemData] = None  # 物品数据（运行时填充）


@dataclass
class ShopUpgrade:
    """属性升级"""
    upgrade_type: str     # 升级类型 (attack/defense/max_hp)
    amount: int           # 提升数量
    price: int            # 价格
    name: str             # 名称
    name_cn: str          # 中文名称


@dataclass
class ShopData:
    """商店数据"""
    shop_id: str
    name: str
    name_cn: str
    description: str = ""
    items: List[ShopItem] = field(default_factory=list)
    upgrades: List[ShopUpgrade] = field(default_factory=list)


class ShopManager:
    """
    商店管理器

    管理所有商店定义，支持从JSON加载
    """

    def __init__(self, item_manager: Optional[ItemManager] = None):
        self._shops: Dict[str, ShopData] = {}
        self._item_manager = item_manager

    def set_item_manager(self, item_manager: ItemManager) -> None:
        """设置物品管理器"""
        self._item_manager = item_manager

    def load_from_json(self, filepath: str) -> bool:
        """
        从JSON文件加载商店定义

        Args:
            filepath: JSON文件路径

        Returns:
            是否加载成功
        """
        try:
            path = Path(filepath)
            if not path.exists():
                print(f"Shops file not found: {filepath}")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            shops_data = data.get('shops', {})
            for shop_id, shop_info in shops_data.items():
                shop = self._parse_shop(shop_id, shop_info)
                if shop:
                    self._shops[shop_id] = shop

            print(f"Loaded {len(self._shops)} shops from {filepath}")
            return True

        except Exception as e:
            print(f"Failed to load shops: {e}")
            return False

    def _parse_shop(self, shop_id: str, data: Dict[str, Any]) -> Optional[ShopData]:
        """解析商店数据"""
        try:
            # 解析物品
            items: List[ShopItem] = []
            for item_info in data.get('items', []):
                item_id = item_info.get('id', '')
                price = item_info.get('price', 0)

                shop_item = ShopItem(
                    item_id=item_id,
                    price=price
                )

                # 如果有物品管理器，填充物品数据
                if self._item_manager:
                    shop_item.item_data = self._item_manager.get_item(item_id)

                items.append(shop_item)

            # 解析升级
            upgrades: List[ShopUpgrade] = []
            for upgrade_info in data.get('upgrades', []):
                upgrade = ShopUpgrade(
                    upgrade_type=upgrade_info.get('type', ''),
                    amount=upgrade_info.get('amount', 0),
                    price=upgrade_info.get('price', 0),
                    name=upgrade_info.get('name', ''),
                    name_cn=upgrade_info.get('name_cn', '')
                )
                upgrades.append(upgrade)

            return ShopData(
                shop_id=shop_id,
                name=data.get('name', shop_id),
                name_cn=data.get('name_cn', shop_id),
                description=data.get('description', ''),
                items=items,
                upgrades=upgrades
            )

        except Exception as e:
            print(f"Failed to parse shop {shop_id}: {e}")
            return None

    def get_shop(self, shop_id: str) -> Optional[ShopData]:
        """获取商店定义"""
        return self._shops.get(shop_id)

    def get_all_shops(self) -> Dict[str, ShopData]:
        """获取所有商店"""
        return self._shops.copy()

    def can_buy_item(self, stats: PlayerStats, shop_item: ShopItem) -> bool:
        """
        检查是否可以购买物品

        Args:
            stats: 玩家属性
            shop_item: 商店物品

        Returns:
            是否可以购买
        """
        return stats.gold >= shop_item.price

    def buy_item(self, stats: PlayerStats, shop_item: ShopItem) -> bool:
        """
        购买物品

        Args:
            stats: 玩家属性
            shop_item: 商店物品

        Returns:
            是否购买成功
        """
        if not self.can_buy_item(stats, shop_item):
            return False

        # 扣除金币
        stats.gold -= shop_item.price

        # 应用物品效果
        if shop_item.item_data and shop_item.item_data.effect:
            shop_item.item_data.effect.apply(stats)

        return True

    def can_buy_upgrade(self, stats: PlayerStats, upgrade: ShopUpgrade) -> bool:
        """
        检查是否可以购买升级

        Args:
            stats: 玩家属性
            upgrade: 属性升级

        Returns:
            是否可以购买
        """
        return stats.gold >= upgrade.price

    def buy_upgrade(self, stats: PlayerStats, upgrade: ShopUpgrade) -> bool:
        """
        购买属性升级

        Args:
            stats: 玩家属性
            upgrade: 属性升级

        Returns:
            是否购买成功
        """
        if not self.can_buy_upgrade(stats, upgrade):
            return False

        # 扣除金币
        stats.gold -= upgrade.price

        # 应用升级效果
        if upgrade.upgrade_type == "attack":
            stats.attack += upgrade.amount
        elif upgrade.upgrade_type == "defense":
            stats.defense += upgrade.amount
        elif upgrade.upgrade_type == "max_hp":
            stats.max_hp += upgrade.amount
            stats.hp = min(stats.hp + upgrade.amount, stats.max_hp)

        return True


# ============================================================
# 预定义商店（备用）
# ============================================================

def create_default_shops() -> Dict[str, ShopData]:
    """
    创建默认商店定义

    用于没有JSON文件时的备用方案
    """
    return {
        "general_store": ShopData(
            shop_id="general_store",
            name="General Store",
            name_cn="杂货店",
            description="出售钥匙和药水",
            items=[
                ShopItem("yellow_key", 10),
                ShopItem("blue_key", 50),
                ShopItem("red_key", 100),
                ShopItem("red_potion", 50),
                ShopItem("blue_potion", 150),
            ],
            upgrades=[]
        ),
        "attribute_dealer": ShopData(
            shop_id="attribute_dealer",
            name="Attribute Dealer",
            name_cn="属性商人",
            description="用金币提升属性",
            items=[],
            upgrades=[
                ShopUpgrade("attack", 5, 100, "ATK+5", "攻击力+5"),
                ShopUpgrade("defense", 5, 100, "DEF+5", "防御力+5"),
                ShopUpgrade("max_hp", 100, 50, "MaxHP+100", "最大HP+100"),
            ]
        ),
    }
