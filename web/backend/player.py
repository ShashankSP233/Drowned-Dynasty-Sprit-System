"""Player resource model.

This is intentionally independent of persistence. A later database/cloud
layer can store these values without changing the attack calculator.
"""

from dataclasses import dataclass

from .rules import spirit_mana_pool, reusable_mana_pool


@dataclass
class Player:
    name: str
    level: int
    proficiency: int

    spirit_mana: int | None = None
    reusable_mana: int | None = None

    def __post_init__(self):
        if self.spirit_mana is None:
            self.spirit_mana = spirit_mana_pool(self.level)
        if self.reusable_mana is None:
            self.reusable_mana = reusable_mana_pool(self.proficiency)

    @property
    def maximum_spirit_mana(self):
        return spirit_mana_pool(self.level)

    @property
    def maximum_reusable_mana(self):
        return reusable_mana_pool(self.proficiency)

    def can_use_spirit_attack(self, attack_cost: int) -> bool:
        return 0 <= attack_cost <= self.spirit_mana

    def use_spirit_attack(self, attack_cost: int):
        if not self.can_use_spirit_attack(attack_cost):
            raise ValueError("Not enough spirit-form mana.")
        self.spirit_mana -= attack_cost

    def start_turn(self):
        self.reusable_mana = self.maximum_reusable_mana

    def restore_spirit_mana(self):
        self.spirit_mana = self.maximum_spirit_mana
