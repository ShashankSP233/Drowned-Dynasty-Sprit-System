from web.backend.embue import build_macro, load_resources, make_selection, new_batch, spend


def test_garris_embue_power_cap():
    resources = load_resources(None, 4, "metal")  # level 4 -> proficiency 2
    normal = make_selection(resources, [], 1, 9, [], multiplier=1)
    garris = make_selection(resources, [], 1, 9, [], multiplier=2)
    assert normal["power_dice"] == 2
    assert garris["power_dice"] == 4
    assert garris["total_cost"] == 1 + 4  # cost is still 1 point per die


def test_spend_uses_proficiency_first():
    resources = load_resources(None, 4, "fire")
    spend(resources, 7)
    assert resources["proficiencyPoints"] == 0
    assert resources["spiritPoints"] == 12 - 5


def test_macro_has_save_dc():
    resources = load_resources(None, 4, "metal")
    chosen = make_selection(resources, [], 1, 2, ["dexterity_prone"])
    profile = {"name": "Garris", "spirit_modifier": 4, "default_element": "metal"}
    macro = build_macro(new_batch("x", 1, chosen, resources, profile), profile, resources)
    assert "Dexterity Save DC=14" in macro and "[[2d6]]" in macro
