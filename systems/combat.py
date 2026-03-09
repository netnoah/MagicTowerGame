"""
Combat System - 战斗系统

回合制战斗逻辑，预计算战斗结果
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class CombatResult:
    """战斗结果"""
    victory: bool              # 玩家是否胜利
    player_damage: int         # 玩家受到的总伤害
    rounds: int                # 战斗回合数
    monster_name: str = ""     # 怪物名称
    gold_gained: int = 0       # 获得金币
    exp_gained: int = 0        # 获得经验


class CombatSystem:
    """
    战斗系统

    魔塔风格的回合制战斗：
    - 玩家攻击 -> 怪物受伤
    - 怪物攻击 -> 玩家受伤
    - 重复直到一方死亡

    使用示例:
        combat = CombatSystem()

        # 预览战斗结果
        result = combat.preview_battle(player, monster)
        if result.victory:
            print(f"胜利！损失 HP: {result.player_damage}")
        else:
            print(f"失败！无法击败怪物")

        # 执行战斗
        combat.execute_battle(player, monster, result)
    """

    @staticmethod
    def calculate_damage(attacker_attack: int, defender_defense: int) -> int:
        """
        计算伤害

        Args:
            attacker_attack: 攻击者攻击力
            defender_defense: 防御者防御力

        Returns:
            伤害值（最小为 1）
        """
        damage = attacker_attack - defender_defense
        return max(1, damage)

    def preview_battle(self, player_stats, monster_stats) -> CombatResult:
        """
        预览战斗结果（不执行战斗）

        Args:
            player_stats: 玩家属性（需要有 hp, attack, defense）
            monster_stats: 怪物属性（需要有 hp, attack, defense, gold, experience）

        Returns:
            CombatResult 战斗结果
        """
        # 计算每回合伤害
        player_damage_per_round = self.calculate_damage(
            player_stats.attack, monster_stats.defense
        )
        monster_damage_per_round = self.calculate_damage(
            monster_stats.attack, player_stats.defense
        )

        # 计算需要的回合数
        rounds_to_kill_monster = math.ceil(
            monster_stats.hp / player_damage_per_round
        )

        # 计算玩家受到的总伤害
        total_player_damage = (rounds_to_kill_monster - 1) * monster_damage_per_round

        # 判断胜负
        victory = total_player_damage < player_stats.hp

        return CombatResult(
            victory=victory,
            player_damage=total_player_damage if victory else player_stats.hp,
            rounds=rounds_to_kill_monster,
            monster_name=getattr(monster_stats, 'name_cn', monster_stats.name if hasattr(monster_stats, 'name') else ''),
            gold_gained=monster_stats.gold if victory else 0,
            exp_gained=monster_stats.experience if victory else 0
        )

    def execute_battle(self, player, monster, result: CombatResult = None) -> CombatResult:
        """
        执行战斗

        Args:
            player: 玩家实体
            monster: 怪物实体
            result: 预计算的战斗结果（如果为 None，会自动计算）

        Returns:
            CombatResult 战斗结果
        """
        if result is None:
            result = self.preview_battle(player.stats, monster.stats)

        if result.victory:
            # 玩家胜利
            player.take_damage(result.player_damage)
            player.add_gold(result.gold_gained)
            player.add_experience(result.exp_gained)
            monster.kill()
        else:
            # 玩家失败
            player.take_damage(result.player_damage)

        return result

    def can_defeat(self, player_stats, monster_stats) -> bool:
        """
        判断玩家是否能击败怪物

        Args:
            player_stats: 玩家属性
            monster_stats: 怪物属性

        Returns:
            是否能击败
        """
        result = self.preview_battle(player_stats, monster_stats)
        return result.victory


# 全局战斗系统实例
combat_system = CombatSystem()


def preview_battle(player_stats, monster_stats) -> CombatResult:
    """快捷函数：预览战斗"""
    return combat_system.preview_battle(player_stats, monster_stats)


def execute_battle(player, monster) -> CombatResult:
    """快捷函数：执行战斗"""
    return combat_system.execute_battle(player, monster)
