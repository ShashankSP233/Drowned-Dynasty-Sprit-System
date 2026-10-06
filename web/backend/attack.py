"""Spirit Attack model and calculator."""

from dataclasses import dataclass, field

from .rules import (
    ELEMENTS,
    power_cost,
    distance_cost,
    aoe_cost,
    embue_cost,
    rider_cost,
)


@dataclass
class SpiritAttack:
    element: str
    level: int
    proficiency: int

    power_dice: int = 0
    distance: int = 0

    aoe_shape: str | None = None
    aoe_size: int | None = None

    embue_charges: int = 0
    riders: list[str] = field(default_factory=list)

    # The source document contains "Unique feature 1=each".
    # This remains an explicit toggle, but its cost is configurable.
    element_feature: bool = False
    element_feature_cost_value: int = 1

    def validate(self):
        if self.element not in ELEMENTS:
            raise ValueError("Unknown element.")
        if self.level < 1:
            raise ValueError("Level must be at least 1.")
        if self.proficiency < 0:
            raise ValueError("Proficiency cannot be negative.")

    def calculate(self):
        self.validate()

        breakdown = []

        cost, labels = power_cost(self.level, self.power_dice)
        breakdown.append(("Power", cost, labels))

        cost, labels = distance_cost(self.distance)
        breakdown.append(("Distance", cost, labels))

        cost, labels = aoe_cost(self.aoe_shape, self.aoe_size)
        breakdown.append(("AoE", cost, labels))

        cost, labels = embue_cost(self.level, self.embue_charges)
        breakdown.append(("Embue", cost, labels))

        cost, labels = rider_cost(self.riders)
        breakdown.append(("Riders", cost, labels))

        if self.element_feature:
            breakdown.append((
                f"{ELEMENTS[self.element]['name']} feature",
                self.element_feature_cost_value,
                ["Element feature enabled"],
            ))

        total = sum(item[1] for item in breakdown)

        return {
            "valid": True,
            "element": self.element,
            "damage": f"{self.power_dice}d6" if self.power_dice else "No damage selected",
            "total_cost": total,
            "breakdown": [
                {
                    "category": category,
                    "cost": cost,
                    "details": details,
                }
                for category, cost, details in breakdown
                if cost or details
            ],
        }
