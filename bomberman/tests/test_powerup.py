"""Бонусы и проклятия: сокрытие под блоками, подбор, эффекты, болезни."""

import random

from src import config as c
from src.entities.player import Player, spread_curse
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


def test_punch_flag():
    p = Player(1, 1)
    assert p.punch is False
    p.apply_powerup(c.POW_PUNCH)
    assert p.punch is True


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


def test_curse_megafire_maxes_flame():
    p = Player(1, 1)
    p.fire = 2
    p.curse = c.CURSE_MEGAFIRE
    assert p.flame == c.MAX_FIRE
    p.curse = None
    assert p.flame == 2


def test_curse_shortfuse_shortens_bomb_fuse():
    p = Player(1, 1)
    assert p.bomb_fuse == c.FUSE_MS
    p.curse = c.CURSE_SHORTFUSE
    assert p.bomb_fuse == c.SHORTFUSE_MS
    assert c.SHORTFUSE_MS < c.FUSE_MS


# --- Заражение болезнью касанием ---

def test_touches_detects_overlap():
    a = Player(3, 3)
    b = Player(3, 3)
    assert a.touches(b) is True
    b.place_at_cell(6, 6)
    assert a.touches(b) is False


def test_spread_transfers_disease_and_cures_carrier():
    sick = Player(3, 3)
    sick.set_curse(c.CURSE_SLOW, now=0)
    well = Player(3, 3)                    # на той же клетке — касание
    assert spread_curse(sick, well, now=0) is True
    assert well.curse == c.CURSE_SLOW      # болезнь перескочила
    assert sick.curse is None             # носитель выздоровел


def test_spread_needs_exactly_one_sick():
    a = Player(3, 3); b = Player(3, 3)
    assert spread_curse(a, b, now=0) is False        # оба здоровы
    a.set_curse(c.CURSE_FAST, 0); b.set_curse(c.CURSE_MINI, 0)
    assert spread_curse(a, b, now=0) is False        # оба больны


def test_spread_requires_touch():
    sick = Player(3, 3); sick.set_curse(c.CURSE_NOBOMB, 0)
    far = Player(8, 8)
    assert spread_curse(sick, far, now=0) is False


def test_spread_cooldown_blocks_immediate_repeat():
    sick = Player(3, 3); sick.set_curse(c.CURSE_REVERSE, 0)
    well = Player(3, 3)
    assert spread_curse(sick, well, now=0) is True
    # теперь болен well; сразу обратно нельзя — кулдаун
    assert spread_curse(well, sick, now=100) is False
    assert spread_curse(well, sick, now=c.CONTAGION_CD_MS + 1) is True


def test_spread_skips_jumping():
    sick = Player(3, 3); sick.set_curse(c.CURSE_SLOW, 0)
    well = Player(3, 3); well.jumping = True
    assert spread_curse(sick, well, now=0) is False
