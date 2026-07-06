"""Валидатор карт и загрузчик уровней — без pygame (чистая логика)."""

import pytest

from src import config as c
from src.world import levels


def good_map():
    """Корректная карта 13×13: рамка стали, база снизу, три точки врага."""
    grid = [["." for _ in range(c.COLS)] for _ in range(c.ROWS)]
    mid = c.COLS // 2
    grid[c.ROWS - 1][mid] = "A"
    grid[c.ROWS - 2][mid] = "P"
    for col in (1, mid, c.COLS - 2):
        grid[0][col] = "E"
    return ["".join(r) for r in grid]


def test_all_shipped_levels_valid():
    assert levels.level_count() == 20
    for i in range(levels.level_count()):
        levels.load_level(i)          # бросит ValueError на битой карте


def test_load_level_index_clamped():
    first = levels.load_level(0)
    assert levels.load_level(-5) == first
    last = levels.load_level(levels.level_count() - 1)
    assert levels.load_level(999) == last


def test_good_map_passes():
    levels.validate(good_map(), "good")


def test_wrong_row_count():
    rows = good_map()[:-1]            # 12 строк вместо 13
    with pytest.raises(ValueError):
        levels.validate(rows, "short")


def test_wrong_col_length():
    rows = good_map()
    rows[0] = rows[0][:-1]            # 12 символов в строке
    with pytest.raises(ValueError):
        levels.validate(rows, "narrow")


def test_bad_char():
    rows = good_map()
    rows[5] = "X" + rows[5][1:]
    with pytest.raises(ValueError):
        levels.validate(rows, "badchar")


def test_missing_base():
    rows = good_map()
    rows[c.ROWS - 1] = rows[c.ROWS - 1].replace("A", ".")
    with pytest.raises(ValueError):
        levels.validate(rows, "nobase")


def test_two_bases():
    rows = good_map()
    grid = [list(r) for r in rows]
    grid[0][0] = "A"                 # вторая база
    with pytest.raises(ValueError):
        levels.validate(["".join(r) for r in grid], "twobase")


def test_missing_player():
    rows = good_map()
    rows[c.ROWS - 2] = rows[c.ROWS - 2].replace("P", ".")
    with pytest.raises(ValueError):
        levels.validate(rows, "noplayer")


def test_missing_enemy():
    grid = [list(r) for r in good_map()]
    for r in range(c.ROWS):
        for col in range(c.COLS):
            if grid[r][col] == "E":
                grid[r][col] = "."
    with pytest.raises(ValueError):
        levels.validate(["".join(r) for r in grid], "noenemy")
