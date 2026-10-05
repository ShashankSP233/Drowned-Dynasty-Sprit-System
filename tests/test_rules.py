from web.python.rules import power_cost, distance_cost, aoe_cost, embue_cost
from web.python.attack import SpiritAttack
from web.python.player import Player


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
    assert player.spirit_mana == 5
