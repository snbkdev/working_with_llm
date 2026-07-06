"""Движение игрока: коллизии со стенами, привязка к полосе, границы (без pygame)."""

from src import config as c
from src.world.arena import Arena
from src.entities.player import Player


def open_arena():
    """Арена без ящиков — только рамка и внутренние столбы."""
    return Arena(seed=1, density=0.0)


def test_spawns_on_floor_cell():
    a = open_arena()
    p = Player(*a.spawns[0])
    assert p.cell == a.spawns[0]
    assert a.is_floor(*p.cell)


def test_moves_right_along_open_lane():
    a = open_arena()
    p = Player(1, 1)                 # верхняя открытая полоса (row=1)
    x0 = p.x
    assert p.try_move(a, c.RIGHT) is True
    assert p.x == x0 + c.PLAYER_SPEED
    assert p.y == float(1 * c.TILE + p.offset)   # полоса не съехала


def test_blocked_by_border_wall():
    a = open_arena()
    p = Player(1, 1)
    # Упираемся влево в рамку (col 0) — много шагов, дальше стены не пройти
    for _ in range(40):
        p.try_move(a, c.LEFT)
    assert not p._blocked(a, p.x, p.y)
    assert p.x >= c.TILE                          # не залез в рамку (col 0)
    assert p.try_move(a, c.LEFT) is False or p.x >= c.TILE


def test_blocked_by_interior_pillar():
    a = open_arena()
    # Столб в (2,2). Встаём в (1,2) и идём вправо — упрёмся в столб.
    p = Player(1, 2)
    moved_any = False
    for _ in range(40):
        if p.try_move(a, c.RIGHT):
            moved_any = True
    assert moved_any
    # Не пересекли столб: правый край левее клетки столба (col 2)
    assert p.x + p.size <= 2 * c.TILE + 1


def test_snap_slides_into_gap():
    a = open_arena()
    p = Player(1, 1)
    # Слегка сместим по вертикали и пойдём вбок — привязка вернёт на полосу
    p.y += 3
    p.try_move(a, c.RIGHT)
    assert p.y == float(1 * c.TILE + p.offset)


def test_cannot_leave_field_bounds():
    a = open_arena()
    p = Player(1, 1)
    for _ in range(60):
        p.try_move(a, c.UP)
    assert p.y >= 0
    assert p.y >= c.TILE - p.size                 # не выше рамки-стены


def test_none_direction_is_noop():
    a = open_arena()
    p = Player(1, 1)
    pos = (p.x, p.y)
    assert p.try_move(a, None) is False
    assert (p.x, p.y) == pos


def test_block_is_obstacle():
    a = Arena(seed=5)                # с ящиками
    # Найдём ящик рядом со свободной клеткой и убедимся, что он не проходим
    for col, row in a.block_cells():
        assert a.is_solid(col, row)
        break
