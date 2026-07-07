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


# --- Детонатор (remote) ---

def test_remote_bomb_ignores_fuse():
    b = Bomb(1, 1, now=0, remote=True)
    assert b.update(c.FUSE_MS + 5000) is False        # не рвётся по фитилю
    assert b.exploded is False


def test_remote_bomb_detonates_on_command():
    b = Bomb(1, 1, now=0, remote=True)
    b.update(c.FUSE_MS + 1000)
    b.detonate()
    assert b.exploded is True


# --- Пинок (скольжение) ---

class _KickArena:
    """Пустая арена с рамкой: всё внутри проходимо, край — стена."""

    def in_bounds(self, col, row):
        return 0 <= col < c.COLS and 0 <= row < c.ROWS

    def is_solid(self, col, row):
        return not self.in_bounds(col, row) or (col, row) in getattr(self, "solid", set())


def test_kick_sets_velocity_once():
    b = Bomb(3, 3, now=0)
    assert b.moving is False
    b.kick(c.RIGHT)
    assert b.moving is True and b.vel == c.RIGHT
    b.kick(c.LEFT)                                     # уже едет — не меняем
    assert b.vel == c.RIGHT


def test_kicked_bomb_slides_across_cells():
    a = _KickArena()
    b = Bomb(3, 3, now=0)
    b.kick(c.RIGHT)
    for _ in range(c.TILE // c.KICK_SPEED + 2):
        b.update_motion(a, [b], set())
    assert b.col == 4 and b.moving                     # переехала на клетку и едет


def test_kicked_bomb_stops_before_wall():
    a = _KickArena()
    a.solid = {(6, 3)}                                 # стена на пути
    b = Bomb(4, 3, now=0)
    b.kick(c.RIGHT)
    for _ in range(c.TILE * 4 // c.KICK_SPEED):
        b.update_motion(a, [b], set())
    assert b.cell == (5, 3) and b.moving is False      # встала вплотную к стене
