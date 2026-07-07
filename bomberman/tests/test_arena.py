"""Генерация арены: рамка/столбы, безопасные углы, разрушение (без pygame)."""

from src import config as c
from src.world import arena as arena_mod
from src.world.arena import Arena, spiral_order


def test_spiral_covers_all_cells_once():
    cells = spiral_order(1, 1, c.COLS - 2, c.ROWS - 2)
    expected = (c.COLS - 2) * (c.ROWS - 2)
    assert len(cells) == expected
    assert len(set(cells)) == expected                 # без повторов
    # все внутри внутреннего прямоугольника
    assert all(1 <= x <= c.COLS - 2 and 1 <= y <= c.ROWS - 2 for x, y in cells)


def test_spiral_starts_outer_ends_inside():
    cells = spiral_order(1, 1, c.COLS - 2, c.ROWS - 2)
    assert cells[0] == (1, 1)                           # с внешнего угла
    # заканчивается глубоко внутри (не на внешнем кольце)
    lx, ly = cells[-1]
    assert 3 <= lx <= c.COLS - 4 and 3 <= ly <= c.ROWS - 4


def test_drop_wall_turns_cell_to_wall():
    a = Arena(seed=1, density=0.0)
    # найдём проходимую клетку и уроним стену
    assert a.is_floor(1, 1)
    assert a.drop_wall(1, 1) is True
    assert a.is_wall(1, 1)
    assert a.drop_wall(1, 1) is False                   # уже стена


def test_grid_dimensions():
    a = Arena(seed=1)
    assert len(a.grid) == c.ROWS
    assert all(len(row) == c.COLS for row in a.grid)


def test_border_is_wall():
    a = Arena(seed=1)
    for col in range(c.COLS):
        assert a.is_wall(col, 0)
        assert a.is_wall(col, c.ROWS - 1)
    for row in range(c.ROWS):
        assert a.is_wall(0, row)
        assert a.is_wall(c.COLS - 1, row)


def test_interior_pillars_on_even_cells():
    a = Arena(seed=1)
    for row in range(2, c.ROWS - 1, 2):
        for col in range(2, c.COLS - 1, 2):
            assert a.is_wall(col, row), f"нет столба в {(col, row)}"


def test_safe_corners_are_floor():
    a = Arena(seed=42)
    for col, row in arena_mod.safe_cells():
        assert a.is_floor(col, row), f"угол-выход занят в {(col, row)}"


def test_spawn_cells_floor_for_many_seeds():
    for seed in range(50):
        a = Arena(seed=seed)
        for col, row in a.spawns:
            assert a.is_floor(col, row)


def test_out_of_bounds_reads_as_wall():
    a = Arena(seed=1)
    assert a.is_wall(-1, 0)
    assert a.is_wall(0, c.ROWS)
    assert a.tile(999, 999) == c.WALL


def test_destroy_block():
    a = Arena(seed=3)
    blocks = a.block_cells()
    assert blocks, "ожидались ящики при плотности по умолчанию"
    col, row = blocks[0]
    assert a.destroy_block(col, row) is True
    assert a.is_floor(col, row)
    assert a.destroy_block(col, row) is False   # уже разрушен


def test_no_blocks_on_walls_or_safe():
    a = Arena(seed=7)
    safe = arena_mod.safe_cells()
    for col, row in a.block_cells():
        assert not arena_mod.is_border_or_pillar(col, row)
        assert (col, row) not in safe


def test_seed_is_reproducible():
    assert Arena(seed=99).grid == Arena(seed=99).grid
    assert Arena(seed=1).grid != Arena(seed=2).grid


def test_density_zero_has_no_blocks():
    a = Arena(seed=1, density=0.0)
    assert a.block_cells() == []
