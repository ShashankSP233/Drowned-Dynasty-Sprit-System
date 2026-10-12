"""Attack Builder logic (no browser code, so it can be tested in plain Python)."""

from .attack import SpiritAttack
from .rules import ELEMENTS, RIDER_SAVES, RIDERS


def build_attack(data, character):
    """Calculate an attack for one character profile and add the character's numbers."""
    attack = SpiritAttack(
        element=data["element"],
        level=data["level"],
        proficiency=data["proficiency"],
        power_dice=data["power_dice"],
        power_dice_multiplier=character.get("power_dice_multiplier", 1),
        distance=data["distance"],
        aoe_shape=data["aoe_shape"],
        aoe_size=data["aoe_size"],
        embue_charges=data.get("embue_charges", 0),
        riders=data["riders"],
        element_feature=data["element_feature"],
        element_feature_cost_value=data.get("element_feature_cost_value", 1),
    )
    result = attack.calculate()
    result.update({
        "character_id": character["id"],
        "character_name": character["name"],
        "spirit_modifier": character["spirit_modifier"],
        "attack_bonus": character["spirit_modifier"] + data["proficiency"],
        "save_dc": 8 + character["spirit_modifier"] + data["proficiency"],
    })
    return result


def bonus_text(bonus):
    return f"+{bonus}" if bonus >= 0 else str(bonus)


def get_resolution(riders, aoe_enabled):
    """Rider saves win over the AoE Dexterity save; otherwise it is an attack roll."""
    abilities = []
    for rider in riders:
        ability = RIDER_SAVES.get(rider)
        if ability and ability not in abilities:
            abilities.append(ability)
    if abilities:
        return {"type": "save", "abilities": abilities}
    if aoe_enabled:
        return {"type": "save", "abilities": ["Dexterity"]}
    return {"type": "attack", "abilities": []}


def preview_tags(result, data):
    resolution = get_resolution(data["riders"], bool(data["aoe_shape"]))
    if resolution["type"] == "attack":
        tags = [f"Attack {bonus_text(result['attack_bonus'])}"]
    else:
        tags = [f"{a} Save DC {result['save_dc']}" for a in resolution["abilities"]]
    tags.append(f"{data['distance']} ft" if data["distance"] else "Touch")
    if data["aoe_shape"]:
        tags.append(f"{data['aoe_shape']} {data['aoe_size']} ft")
    if data["element_feature"]:
        tags.append("Element feature")
    return tags


def build_macro(result, data):
    resolution = get_resolution(data["riders"], bool(data["aoe_shape"]))
    name = "".join(ch for ch in str(result["character_name"]) if ch not in "{}|")
    element_key = result["element"]
    element = element_key[:1].upper() + element_key[1:]

    rows = [f"&{{template:default}} {{{{name={name} — {element} Spirit Attack}}}}"]
    if resolution["type"] == "attack":
        rows.append(f"{{{{Attack=[[1d20{bonus_text(result['attack_bonus'])}]]}}}}")
    else:
        for ability in resolution["abilities"]:
            rows.append(f"{{{{{ability} Save DC={result['save_dc']}}}}}")

    distance = data["distance"]
    range_text = f"{distance} ft" if distance else "Touch"
    rows.append(f"{{{{Range={range_text}}}}}")
    if data["aoe_shape"]:
        rows.append(f"{{{{Area of Effect={data['aoe_shape']}, {data['aoe_size']} ft}}}}")

    if data["power_dice"] > 0:
        rows.append(f"{{{{Damage ({element})=[[{data['power_dice']}d6]]}}}}")
    else:
        rows.append(f"{{{{Damage Type={element}}}}}")

    effects = [RIDERS[r][0] for r in data["riders"] if r in RIDERS]
    if data["element_feature"]:
        effects.append(f"{element} Feature: {ELEMENTS[element_key]['feature']}")
    if effects:
        rows.append(f"{{{{Effects={', '.join(effects)}}}}}")
    return " ".join(rows)
