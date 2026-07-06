"""Типы врагов и броня: HP, damage(), усиление (нужен pygame)."""

import pytest

pygame = pytest.importorskip("pygame")

from src import config as c              # noqa: E402
from src.entities.enemy import Enemy     # noqa: E402


def test_basic_dies_in_one_hit(pg):
    e = Enemy(1, 1, kind="basic")
    assert e.hp == 1
    assert e.damage() is True


def test_armor_survives_until_last_hp(pg):
    e = Enemy(1, 1, kind="armor")
    assert e.hp > 1
    for _ in range(e.max_hp - 1):
        assert e.damage() is False     # держит броню
    assert e.damage() is True          # последнее попадание — уничтожен


def test_reinforced_is_tougher_and_bigger(pg):
    base = Enemy(1, 1, kind="basic")
    tough = Enemy(1, 1, kind="basic", reinforced=True)
    assert tough.hp >= c.REINFORCE_MIN_HP
    assert tough.hp > base.hp
    assert tough.size >= base.size


def test_armor_color_changes_with_damage(pg):
    e = Enemy(1, 1, kind="armor")
    full = e.body_color
    e.damage()
    assert e.body_color != full        # цвет краснеет по мере пробития
