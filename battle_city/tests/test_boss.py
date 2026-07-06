"""Босс: фазы, «веер» огня, урон (нужен pygame для time/rect)."""

import math

import pytest

pygame = pytest.importorskip("pygame")

from src import config as c              # noqa: E402
from src.entities.boss import Boss       # noqa: E402


def test_phase_thresholds(pg):
    b = Boss(0, 0)
    b.hp = b.max_hp
    assert b.phase() == 0
    b.hp = int(b.max_hp * 0.5)
    assert b.phase() == 1
    b.hp = 1
    assert b.phase() == 2


def test_fire_fans_out_with_phase(pg):
    b = Boss(0, 0)
    b.hp = b.max_hp
    assert len(b._fire()) == 1
    b.hp = int(b.max_hp * 0.5)
    assert len(b._fire()) == 3
    b.hp = 1
    assert len(b._fire()) == 5


def test_fire_bullets_normalized_enemy_owned(pg):
    b = Boss(0, 0)
    b.hp = 1
    for bullet in b._fire():
        assert bullet.owner == "enemy"
        assert abs(math.hypot(*bullet.dir) - 1.0) < 1e-6


def test_damage_kills_at_zero(pg):
    b = Boss(0, 0)
    for _ in range(b.max_hp - 1):
        assert b.damage() is False
    assert b.damage() is True


def test_score_is_boss_score(pg):
    assert Boss(0, 0).score == c.BOSS_SCORE
