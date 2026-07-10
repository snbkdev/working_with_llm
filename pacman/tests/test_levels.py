"""Параметры уровня: рост скорости/таймингов и ограничители."""

from src import config as c
from src.world import levels


def test_speeds_increase_with_level():
    lo = levels.params(1, 1)
    hi = levels.params(5, 1)
    assert hi["pac_speed"] > lo["pac_speed"]
    assert hi["ghost_speed"] > lo["ghost_speed"]
    assert hi["fright_ms"] < lo["fright_ms"]


def test_caps_and_floors():
    p = levels.params(50, 2)
    assert p["pac_speed"] <= 1.0
    assert p["ghost_speed"] <= 0.98
    assert p["fright_ms"] >= 1000
    assert p["scatter_ms"] >= 3000


def test_difficulty_affects_base():
    easy = levels.params(1, 0)
    hard = levels.params(1, 2)
    assert hard["ghost_speed"] > easy["ghost_speed"]
    assert hard["fright_ms"] < easy["fright_ms"]
