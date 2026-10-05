"""Drowned Dynasty Spirit Attack rules.

This module is deliberately kept independent of the UI.
Only rules explicitly represented in the supplied homebrew document
are encoded here.
"""

ELEMENTS = {
    "fire": {
        "name": "Fire",
        "feature": "Reroll 2 damage dice",
    },
    "water": {
        "name": "Water",
        "feature": "If the first target is hit/fails, target another creature within 10 ft for half damage",
    },
    "wood": {
        "name": "Wood",
        "feature": "After the target is hit/fails, the next attack against them gains 1d4 to hit",
    },
    "metal": {
        "name": "Metal",
        "feature": "After the target is hit/fails, their next save is reduced by 1d4",
    },
    "earth": {
        "name": "Earth",
        "feature": "After the target is hit/fails, their next attack's damage is reduced by 1d4",
    },
}

DISTANCE_COSTS = {
    0: ("Touch", 0),
    30: ("30 ft", 1),
    60: ("60 ft", 2),
    120: ("120 ft", 3),
    300: ("300 ft", 4),
}

AOE_COSTS = {
    "cone": {
        15: 2,
        30: 4,
        60: 6,
        90: 8,
    },
    "radius": {
        5: 1,
        10: 2,
        15: 3,
        20: 4,
        30: 5,
        60: 6,
    },
    "line": {
        30: 1,
        60: 2,
        100: 3,
        300: 4,
    },
}

RIDERS = {
    "dexterity_prone": ("Dexterity — Prone", 2),
    "strength_prone_knockback": ("Strength — Prone + 30 ft knockback", 4),
    "constitution_blind": ("Constitution — Blind", 6),
    "strength_restrained": ("Strength — Restrained", 8),
    "constitution_incapacitate": ("Constitution — Incapacitate", 10),
    "difficult_terrain": ("Difficult terrain — 1 minute", 2),
}


def spirit_mana_pool(level: int) -> int:
    return max(1, int(level)) * 3


def reusable_mana_pool(proficiency: int) -> int:
    return max(0, int(proficiency))


def power_cost(level: int, dice: int) -> tuple[int, list[str]]:
    level = max(1, int(level))
    dice = max(0, int(dice))
    if dice > level:
        raise ValueError("Power dice cannot exceed character level.")
    return dice, ([f"{dice}d6 Power"] if dice else [])


def distance_cost(distance: int) -> tuple[int, list[str]]:
    try:
        name, cost = DISTANCE_COSTS[int(distance)]
    except KeyError as exc:
        raise ValueError("Invalid distance.") from exc
    return cost, ([f"Distance: {name}"] if cost else [])


def aoe_cost(shape: str | None, size: int | None) -> tuple[int, list[str]]:
    if not shape:
        return 0, []
    if shape not in AOE_COSTS:
        raise ValueError("Invalid AoE shape.")
    if size not in AOE_COSTS[shape]:
        raise ValueError("Invalid AoE size.")
    cost = AOE_COSTS[shape][size]
    return cost, [f"AoE: {shape} {size} ft"]


def embue_cost(level: int, charges: int) -> tuple[int, list[str]]:
    level = max(1, int(level))
    charges = max(0, int(charges))
    if charges > level:
        raise ValueError("Embue charges cannot exceed character level.")
    return charges, ([f"Embue: {charges} charge(s)"] if charges else [])


def rider_cost(riders: list[str]) -> tuple[int, list[str]]:
    total = 0
    labels = []
    for rider in riders:
        if rider not in RIDERS:
            raise ValueError(f"Unknown rider: {rider}")
        name, cost = RIDERS[rider]
        total += cost
        labels.append(f"Rider: {name}")
    return total, labels
