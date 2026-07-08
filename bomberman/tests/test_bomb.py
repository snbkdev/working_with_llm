"""Бомба: фитиль, подрыв, правило установки (без pygame)."""

from src import config as c
from src.entities.bomb import Bomb, can_place, flight_target


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


def test_custom_short_fuse_explodes_early():
    b = Bomb(1, 1, now=0, fuse=c.SHORTFUSE_MS)
    assert b.update(c.SHORTFUSE_MS - 1) is False
    assert b.update(c.SHORTFUSE_MS) is True             # короткий фитиль


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


# --- Бросок (перчатка) ---

def test_flight_target_flies_n_tiles():
    a = _KickArena()
    cell = flight_target(a, set(), 3, 3, c.RIGHT)
    assert cell == (3 + c.THROW_TILES, 3)


def test_flight_target_wraps_around_edge():
    a = _KickArena()
    # у правого края — обёртка на левую сторону поля
    cell = flight_target(a, set(), c.COLS - 3, 3, c.RIGHT, tiles=3)
    assert cell[0] < c.COLS - 3                        # перекинуло влево
    assert 1 <= cell[0] <= c.COLS - 2


def test_flight_target_skips_solid_and_occupied():
    a = _KickArena()
    a.solid = {(3 + c.THROW_TILES, 3)}                 # штатная цель — стена
    occ = {(3 + c.THROW_TILES + 1, 3)}                 # и следующая занята
    cell = flight_target(a, occ, 3, 3, c.RIGHT)
    assert cell == (3 + c.THROW_TILES + 2, 3)          # приземлилась дальше


def test_throw_sets_airborne_and_lands():
    a = _KickArena()
    b = Bomb(3, 3, now=0)
    b.throw(c.RIGHT, a, set(), now=0)
    assert b.airborne is True
    b.update_flight(c.THROW_MS)                        # долетела
    assert b.airborne is False
    assert b.cell == (3 + c.THROW_TILES, 3)


def test_airborne_bomb_does_not_explode():
    b = Bomb(1, 1, now=0)
    b.throw(c.RIGHT, _KickArena(), set(), now=0)
    assert b.update(c.FUSE_MS + 9999) is False         # в полёте фитиль на паузе
    assert b.exploded is False


def test_throw_preserves_remaining_fuse():
    b = Bomb(1, 1, now=1000)                            # 1 с фитиля уже прошла
    left_before = b.time_left(1000)
    b.throw(c.RIGHT, _KickArena(), set(), now=1000)
    b.update_flight(1000 + c.THROW_MS)                  # приземлилась
    assert b.time_left(1000 + c.THROW_MS) == left_before
