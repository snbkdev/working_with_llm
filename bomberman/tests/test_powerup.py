"""Бонусы и проклятия: сокрытие под блоками, подбор, эффекты, болезни."""

import random

from src import config as c
from src.entities.player import Player
from src.entities.powerup import PowerUp, pickup
from src.world.arena import Arena


# --- Сокрытие бонусов под ящиками ---

def test_hidden_only_under_blocks():
    a = Arena(seed=2)
    blocks = set(a.block_cells())
    assert a.hidden                                  # что-то спрятано
    assert set(a.hidden) <= blocks                   # только под ящиками
    assert all(k in c.POWERUP_KINDS for k in a.hidden.values())


def test_pop_hidden_is_one_shot():
    a = Arena(seed=2)
    cell = next(iter(a.hidden))
    kind = a.hidden[cell]
    assert a.pop_hidden(*cell) == kind
    assert a.pop_hidden(*cell) is None               # второй раз пусто


def test_pop_hidden_absent():
    a = Arena(seed=2, density=0.0)                    # ящиков нет
    assert a.hidden == {}
    assert a.pop_hidden(3, 3) is None


# --- Подбор ---

def test_pickup_marks_and_returns():
    p = PowerUp(4, 4, c.POW_FIRE)
    got = pickup([p], (4, 4))
    assert got is p and p.taken is True
    assert pickup([p], (4, 4)) is None               # уже забран


def test_pickup_misses_other_cell():
    p = PowerUp(4, 4, c.POW_BOMB)
    assert pickup([p], (5, 5)) is None


# --- Эффекты бонусов ---

def test_bomb_and_fire_and_speed_increment_with_caps():
    p = Player(1, 1)
    for _ in range(20):
        p.apply_powerup(c.POW_BOMB)
        p.apply_powerup(c.POW_FIRE)
        p.apply_powerup(c.POW_SPEED)
    assert p.max_bombs == c.MAX_BOMBS
    assert p.fire == c.MAX_FIRE
    assert p.speed_level == c.MAX_SPEED_LVL


def test_kick_and_detonator_flags():
    p = Player(1, 1)
    assert p.kick is False and p.detonator is False
    p.apply_powerup(c.POW_KICK)
    p.apply_powerup(c.POW_DETON)
    assert p.kick is True and p.detonator is True


def test_fullfire_maxes_fire():
    p = Player(1, 1)
    p.apply_powerup(c.POW_FULLFIRE)
    assert p.fire == c.MAX_FIRE


def test_speed_grows_with_level():
    p = Player(1, 1)
    base = p.speed
    p.apply_powerup(c.POW_SPEED)
    assert p.speed == base + 1


# --- Проклятия-черепа ---

def test_skull_sets_timed_curse():
    p = Player(1, 1)
    p.apply_powerup(c.POW_SKULL, now=1000, rng=random.Random(0))
    assert p.curse in c.CURSES
    assert p.curse_until == 1000 + c.CURSE_MS


def test_curse_expires():
    p = Player(1, 1)
    p.apply_powerup(c.POW_SKULL, now=0, rng=random.Random(1))
    p.update_curse(c.CURSE_MS - 1)
    assert p.curse is not None
    p.update_curse(c.CURSE_MS)
    assert p.curse is None


def test_curse_reverse_flips_input():
    p = Player(1, 1)
    p.curse = c.CURSE_REVERSE
    assert p.input_dir(c.LEFT) == c.RIGHT
    assert p.input_dir(c.UP) == c.DOWN
    assert p.input_dir(None) is None


def test_curse_speed_overrides():
    p = Player(1, 1)
    p.apply_powerup(c.POW_SPEED)                      # быстрее базовой
    p.curse = c.CURSE_SLOW
    assert p.speed == c.CURSE_SPEED_SLOW
    p.curse = c.CURSE_FAST
    assert p.speed == c.CURSE_SPEED_FAST


def test_curse_mini_shrinks_flame():
    p = Player(1, 1)
    p.fire = 5
    p.curse = c.CURSE_MINI
    assert p.flame == 1
    p.curse = None
    assert p.flame == 5


def test_curse_nobomb_and_autobomb():
    p = Player(1, 1)
    p.curse = c.CURSE_NOBOMB
    assert p.can_bomb is False and p.auto_bomb is False
    p.curse = c.CURSE_AUTOBOMB
    assert p.can_bomb is True and p.auto_bomb is True
