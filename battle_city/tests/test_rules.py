"""Правила пуль и применение бонусов (нужен pygame).

Логику, «висящую» на Game, дёргаем несвязанными методами с лёгким
объектом-заглушкой (types.SimpleNamespace) — без создания окна.
"""

import types

import pytest

pygame = pytest.importorskip("pygame")

from src import config as c              # noqa: E402
from src.entities.bullet import Bullet   # noqa: E402
from src.entities.tank import Tank       # noqa: E402
from src.world.level import Level        # noqa: E402
from src.game import Game                # noqa: E402


# --- Пуля ---
def test_bullet_moves_by_speed(pg):
    b = Bullet(100, 100, c.UP)
    b.update()
    assert b.x == 100 and b.y == 100 - c.BULLET_SPEED


def test_bullet_power_flag(pg):
    assert Bullet(0, 0, c.UP, power=True).power is True
    assert Bullet(0, 0, c.UP).power is False


def test_bullet_rect_centered(pg):
    r = Bullet(100, 100, c.UP).rect
    assert r.centerx in (99, 100) and r.centery in (99, 100)


# --- Встречные пули гасят друг друга ---
def test_bullets_cancel_on_overlap(pg):
    pb = Bullet(100, 100, c.UP, owner="player")
    eb = Bullet(100, 100, c.DOWN, owner="enemy")
    ns = types.SimpleNamespace(bullets=[pb, eb])
    Game._bullets_cancel(ns)
    assert not pb.alive and not eb.alive


def test_bullets_dont_cancel_when_apart(pg):
    pb = Bullet(40, 40, c.UP, owner="player")
    eb = Bullet(400, 400, c.DOWN, owner="enemy")
    ns = types.SimpleNamespace(bullets=[pb, eb])
    Game._bullets_cancel(ns)
    assert pb.alive and eb.alive


def test_same_owner_bullets_dont_cancel(pg):
    a = Bullet(100, 100, c.UP, owner="player")
    b = Bullet(100, 100, c.DOWN, owner="player")
    ns = types.SimpleNamespace(bullets=[a, b])
    Game._bullets_cancel(ns)
    assert a.alive and b.alive


# --- Применение бонусов ---
def test_apply_star_upgrades(pg):
    ns = types.SimpleNamespace(player=Tank(6, 6))
    ns.player.level = 0
    Game.apply_powerup(ns, "star")
    assert ns.player.level == 1


def test_apply_star_capped(pg):
    ns = types.SimpleNamespace(player=Tank(6, 6))
    ns.player.level = c.PLAYER_MAX_LEVEL
    Game.apply_powerup(ns, "star")
    assert ns.player.level == c.PLAYER_MAX_LEVEL


def test_apply_life_increments_and_caps(pg):
    ns = types.SimpleNamespace(lives=1)
    Game.apply_powerup(ns, "life")
    assert ns.lives == 2
    full = types.SimpleNamespace(lives=c.PLAYER_MAX_LIVES)
    Game.apply_powerup(full, "life")
    assert full.lives == c.PLAYER_MAX_LIVES


def test_apply_clock_sets_freeze(pg):
    ns = types.SimpleNamespace()
    Game.apply_powerup(ns, "clock")
    assert ns.freeze_until > 0


def test_apply_steel_armors_base(pg):
    ns = types.SimpleNamespace(level=Level())
    Game.apply_powerup(ns, "steel")
    assert ns.steel_until > 0
    assert all(cell in ns.level.steels for cell in ns.level.base_wall)
