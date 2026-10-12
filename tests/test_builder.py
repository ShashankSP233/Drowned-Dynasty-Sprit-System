from web.backend.builder import build_attack, build_macro, get_resolution, preview_tags
from web.backend.characters import get_character


def attack_data(**changes):
    data = {
        "element": "metal", "level": 4, "proficiency": 2, "power_dice": 0,
        "distance": 0, "aoe_shape": None, "aoe_size": None, "embue_charges": 0,
        "riders": [], "element_feature": False, "element_feature_cost_value": 1,
    }
    data.update(changes)
    return data


def test_garris_can_use_double_power_and_pays_per_die():
    data = attack_data(power_dice=8)
    result = build_attack(data, get_character("3"))
    assert result["total_cost"] == 8
    assert result["damage"] == "8d6"


def test_plain_attack_is_an_attack_roll():
    data = attack_data(power_dice=2)
    result = build_attack(data, get_character("1"))
    macro = build_macro(result, data)
    assert result["attack_bonus"] == 6 and result["save_dc"] == 14
    assert "{{Attack=[[1d20+6]]}}" in macro
    assert "[[2d6]]" in macro and "{{Range=Touch}}" in macro


def test_aoe_uses_dexterity_save():
    data = attack_data(aoe_shape="radius", aoe_size=10)
    result = build_attack(data, get_character("1"))
    assert get_resolution(data["riders"], True)["abilities"] == ["Dexterity"]
    assert "Dexterity Save DC=14" in build_macro(result, data)
    assert "{{Area of Effect=radius, 10 ft}}" in build_macro(result, data)


def test_rider_save_replaces_aoe_save():
    data = attack_data(aoe_shape="cone", aoe_size=15, riders=["constitution_blind"])
    result = build_attack(data, get_character("1"))
    macro = build_macro(result, data)
    assert "Constitution Save DC=14" in macro and "Dexterity Save" not in macro
    assert "Constitution Save DC 14" in preview_tags(result, data)


def test_element_feature_costs_one_and_is_named():
    data = attack_data(element_feature=True)
    result = build_attack(data, get_character("1"))
    assert result["total_cost"] == 1
    assert "Metal Feature:" in build_macro(result, data)
