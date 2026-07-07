"""Бомба: фитиль, подрыв, правило установки (без pygame)."""

from src import config as c
from src.entities.bomb import Bomb, can_place


def test_cell_and_center():
    b = Bomb(3, 4, now=0)
    assert b.cell == (3, 4)
    assert b.center() == (3 * c.TILE + c.TILE // 2, 4 * c.TILE + c.TILE // 2)


def test_fuse_not_exploded_before_time():
    b = Bomb(1, 1, now=0)
    assert b.update(0) is False
    assert b.update(c.FUSE_MS - 1) is False
    assert b.exploded is False


def test_fuse_explodes_at_time():
    b = Bomb(1, 1, now=0)
    assert b.update(c.FUSE_MS) is True
    assert b.exploded is True


def test_fuse_explodes_after_time():
    b = Bomb(1, 1, now=1000)
    assert b.update(1000 + c.FUSE_MS + 500) is True


def test_time_left_decreases_and_clamps():
    b = Bomb(1, 1, now=0)
    assert b.time_left(0) == c.FUSE_MS
    assert b.time_left(c.FUSE_MS // 2) == c.FUSE_MS - c.FUSE_MS // 2
    assert b.time_left(c.FUSE_MS + 999) == 0


def test_detonate_forces_explosion():
    b = Bomb(1, 1, now=0)
    b.detonate()
    assert b.exploded is True


def test_can_place_respects_limit():
    bombs = []
    assert can_place(bombs, (1, 1), owner=0, max_bombs=1) is True
    bombs.append(Bomb(1, 1, owner=0, now=0))
    # лимит 1 исчерпан
    assert can_place(bombs, (2, 1), owner=0, max_bombs=1) is False
    # с лимитом 2 — можно ещё одну на другую клетку
    assert can_place(bombs, (2, 1), owner=0, max_bombs=2) is True


def test_can_place_rejects_occupied_cell():
    bombs = [Bomb(3, 3, owner=0, now=0)]
    assert can_place(bombs, (3, 3), owner=0, max_bombs=5) is False


def test_exploded_bomb_frees_slot():
    b = Bomb(1, 1, owner=0, now=0)
    bombs = [b]
    assert can_place(bombs, (2, 2), owner=0, max_bombs=1) is False
    b.update(c.FUSE_MS)                     # взорвалась → слот освобождён
    assert can_place(bombs, (2, 2), owner=0, max_bombs=1) is True


def test_limits_are_per_owner():
    bombs = [Bomb(1, 1, owner=0, now=0)]
    # у другого игрока свой лимит
    assert can_place(bombs, (5, 5), owner=1, max_bombs=1) is True
