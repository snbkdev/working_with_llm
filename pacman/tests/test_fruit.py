"""Фрукт-бонус: появление, съедание, таймаут, очки по уровню."""

from src import config as c
from src.entities.fruit import Fruit


def test_spawn_and_index_by_level():
    f = Fruit()
    f.spawn(1, now=0)
    assert f.active and f.idx == 0            # уровень 1 — вишня
    f.spawn(3, now=0)
    assert f.idx == 2                         # уровень 3 — апельсин
    f.spawn(99, now=0)
    assert f.idx == len(c.FRUITS) - 1         # дальше — последний (key)


def test_eat_only_on_tile():
    f = Fruit()
    f.spawn(1, now=0)
    assert f.eat((0, 0)) == 0                 # не на клетке фрукта
    assert f.active
    pts = f.eat(c.FRUIT_TILE)
    assert pts == c.FRUITS[0][1]              # 100 за вишню
    assert not f.active


def test_timeout():
    f = Fruit()
    f.spawn(1, now=1000)
    f.update(1000 + c.FRUIT_MS - 1)
    assert f.active
    f.update(1000 + c.FRUIT_MS)
    assert not f.active


def test_eat_after_timeout_gives_nothing():
    f = Fruit()
    f.spawn(1, now=0)
    f.update(c.FRUIT_MS)
    assert f.eat(c.FRUIT_TILE) == 0
