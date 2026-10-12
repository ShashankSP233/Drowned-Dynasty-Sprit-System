from web.backend.rules import power_cost, distance_cost, aoe_cost, embue_cost
from web.backend.attack import SpiritAttack
from web.backend.player import Player


def test_power():
    assert power_cost(5, 4)[0] == 4


def test_distance():
    assert distance_cost(60)[0] == 2


def test_cone():
    assert aoe_cost("cone", 30)[0] == 4


def test_radius():
    assert aoe_cost("radius", 30)[0] == 5


def test_line():
    assert aoe_cost("line", 100)[0] == 3


def test_embue():
    assert embue_cost(5, 2)[0] == 2


def test_attack():
    attack = SpiritAttack(
        element="fire",
        level=5,
        proficiency=3,
        power_dice=4,
        distance=60,
        aoe_shape="cone",
        aoe_size=30,
        embue_charges=2,
    )
    assert attack.calculate()["total_cost"] == 12


def test_player():
    player = Player("Sion", 5, 3)
    assert player.spirit_mana == 15
    player.use_spirit_attack(10)
    assert player.spirit_mana == 8


def _rejects(fn, *args):
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def test_garris_double_power_cap():
    from web.backend.characters import get_character

    mult = get_character("3")["power_dice_multiplier"]
    assert mult == 2
    # level 4: 8d6 allowed, and it still costs 8 points
    assert power_cost(4, 8, mult)[0] == 8
    assert _rejects(power_cost, 4, 9, mult)
    # everyone else stays capped at level
    assert _rejects(power_cost, 4, 5)
    attack = SpiritAttack(element="metal", level=4, proficiency=2,
                          power_dice=8, power_dice_multiplier=mult)
    assert attack.calculate()["total_cost"] == 8
