"""Апгрейд и габарит танка: resize / set_level (нужен pygame для rect)."""

import pytest

pygame = pytest.importorskip("pygame")

from src import config as c              # noqa: E402
from src.entities.tank import Tank       # noqa: E402


def test_set_level_grows_size(pg):
    t = Tank(6, 6)
    for lvl in range(len(c.PLAYER_TANK_SIZES)):
        t.set_level(lvl)
        assert t.size == c.PLAYER_TANK_SIZES[lvl]


def test_set_level_index_clamped(pg):
    t = Tank(6, 6)
    t.set_level(99)
    assert t.size == c.PLAYER_TANK_SIZES[-1]


def test_resize_keeps_center(pg):
    t = Tank(6, 6)
    cx, cy = t.rect.center
    t.resize(38)
    assert abs(t.rect.centerx - cx) <= 1
    assert abs(t.rect.centery - cy) <= 1


def test_resize_clamped_into_field(pg):
    t = Tank(0, 0)
    t.resize(c.PLAYER_TANK_SIZES[-1])
    assert t.x >= 0 and t.y >= 0
    assert t.rect.right <= c.FIELD_W and t.rect.bottom <= c.FIELD_H
