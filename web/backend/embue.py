"""Embue Tracker logic (no browser code, so it can be tested in plain Python).

Stored dictionaries keep the camelCase keys the site already saves in the
browser (spiritPoints, remainingCharges, ...), so existing saved data and the
Attack Builder page keep working.
"""

from .player import Player
from .rules import (
    RIDERS,
    RIDER_SAVES,
    max_embue_power,
    proficiency_for_level,
    spirit_mana_pool,
)


def _number(value, default=0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number:  # NaN
        return default
    return int(number)


def load_resources(saved, default_level=4, default_element="fire"):
    saved = saved if isinstance(saved, dict) else {}
    level = max(1, _number(saved.get("level"), 0) or default_level)
    proficiency = proficiency_for_level(level)
    spirit_max = spirit_mana_pool(level)
    spirit = _number(saved.get("spiritPoints"), spirit_max) if saved.get("spiritPoints") is not None else spirit_max
    prof = _number(saved.get("proficiencyPoints"), proficiency) if saved.get("proficiencyPoints") is not None else proficiency
    return {
        "level": level,
        "default_level": default_level,
        "element": saved.get("element") or default_element,
        "proficiency": proficiency,
        "spiritPoints": min(spirit_max, max(0, spirit)),
        "proficiencyPoints": min(proficiency, max(0, prof)),
    }


def held_charges(batches):
    return sum(max(0, _number(b.get("remainingCharges"))) for b in batches)


def make_selection(resources, batches, charges, power, riders, multiplier=1):
    max_charges = max(0, resources["level"] - held_charges(batches))
    charges = max(1, min(max_charges, _number(charges, 1) or 1))
    max_power = max_embue_power(resources["proficiency"], multiplier)
    power_dice = min(max_power, max(0, _number(power)))
    riders = [r for r in riders if r in RIDERS]
    rider_cost = sum(RIDERS[r][1] for r in riders)
    return {
        "max_charges": max_charges,
        "max_power": max_power,
        "charges": charges,
        "power_dice": power_dice,
        "riders": riders,
        "rider_cost": rider_cost,
        "effect_cost": power_dice + rider_cost,
        "total_cost": charges + power_dice + rider_cost,
    }


def can_afford(resources, cost):
    return cost <= resources["spiritPoints"] + resources["proficiencyPoints"]


def spend(resources, cost):
    """Spend proficiency points first, then spirit points."""
    player = Player(
        "embue",
        resources["level"],
        resources["proficiency"],
        spirit_mana=resources["spiritPoints"],
        reusable_mana=resources["proficiencyPoints"],
    )
    player.use_spirit_attack(cost)
    resources["spiritPoints"] = player.spirit_mana
    resources["proficiencyPoints"] = player.reusable_mana


def new_batch(batch_id, number, chosen, resources, profile):
    return {
        "id": batch_id,
        "number": number,
        "totalCharges": chosen["charges"],
        "remainingCharges": chosen["charges"],
        "powerDice": chosen["power_dice"],
        "riders": list(chosen["riders"]),
        "characterName": profile.get("name"),
        "spiritModifier": profile.get("spirit_modifier"),
        "proficiency": resources["proficiency"],
        "element": resources.get("element") or profile.get("default_element") or "fire",
    }


def start_round(resources):
    resources["proficiencyPoints"] = resources["proficiency"]


def long_rest(resources):
    resources["spiritPoints"] = spirit_mana_pool(resources["level"])
    resources["proficiencyPoints"] = resources["proficiency"]


def batch_effects(batch):
    parts = []
    if batch.get("powerDice"):
        parts.append(f"{batch['powerDice']}d6 bonus damage on hit")
    for rider in batch.get("riders", []):
        if rider in RIDERS:
            parts.append(f"{RIDERS[rider][0]} on hit")
    return " · ".join(parts) if parts else "No effects selected"


def build_macro(batch, profile, resources):
    name = str(batch.get("characterName") or profile.get("name") or "Character")
    name = "".join(ch for ch in name if ch not in "{}|")
    element = str(batch.get("element") or resources.get("element") or profile.get("default_element") or "fire")
    title = element[:1].upper() + element[1:]
    modifier = _number(batch.get("spiritModifier", profile.get("spirit_modifier")))
    proficiency = _number(batch.get("proficiency", resources["proficiency"]))
    save_dc = 8 + modifier + proficiency

    rows = [f"&{{template:default}} {{{{name={name} — {title} Embue}}}}"]
    if batch.get("powerDice", 0) > 0:
        rows.append(f"{{{{Damage ({title})=[[{batch['powerDice']}d6]]}}}}")

    riders = batch.get("riders") or []
    abilities = []
    for rider in riders:
        ability = RIDER_SAVES.get(rider)
        if ability and ability not in abilities:
            abilities.append(ability)
    for ability in abilities:
        rows.append(f"{{{{{ability} Save DC={save_dc}}}}}")

    labels = [RIDERS[r][0] for r in riders if r in RIDERS]
    if labels:
        rows.append(f"{{{{Effects={', '.join(labels)}}}}}")
    return " ".join(rows)
