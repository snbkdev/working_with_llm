"""Хранилище карт и загрузка своей карты в арену (без pygame)."""

import tempfile

from src import config as c
from src import storage
from src.world.arena import Arena


def test_blank_map_has_border_and_spawns():
    data = storage.blank_map()
    assert storage.valid(data)
    assert len(data["spawns"]) == len(c.SPAWN_CELLS)
    for col in range(c.COLS):                          # рамка по краю
        assert data["grid"][0][col] == c.WALL
        assert data["grid"][c.ROWS - 1][col] == c.WALL


def test_save_and_load_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        data = storage.blank_map()
        data["grid"][3][3] = c.BLOCK
        data["specials"]["5,5"] = [c.SPEC_TELEPORT, None]
        storage.save_map(data, "m1", directory=d)
        assert storage.map_path("m1", directory=d).exists()
        loaded = storage.load_map("m1", directory=d)
        assert loaded["grid"][3][3] == c.BLOCK
        assert loaded["specials"]["5,5"][0] == c.SPEC_TELEPORT


def test_list_maps_sorted():
    with tempfile.TemporaryDirectory() as d:
        storage.save_map(storage.blank_map(), "b", directory=d)
        storage.save_map(storage.blank_map(), "a", directory=d)
        names = [p.stem for p in storage.list_maps(directory=d)]
        assert names == ["a", "b"]


def test_load_missing_returns_none():
    with tempfile.TemporaryDirectory() as d:
        assert storage.load_map("nope", directory=d) is None


def test_valid_rejects_wrong_dimensions():
    assert storage.valid({"cols": 3, "rows": 3, "grid": []}) is False
    assert storage.valid("not a dict") is False


def test_arena_load_custom_applies_grid_specials_spawns():
    data = storage.blank_map()
    data["grid"][3][3] = c.BLOCK
    data["specials"] = {"7,5": [c.SPEC_CONVEYOR, list(c.RIGHT)]}
    data["spawns"] = [[1, 1], [c.COLS - 2, c.ROWS - 2]]
    a = Arena(seed=1)
    a.load_custom(data, seed=1)
    assert a.is_block(3, 3)
    assert a.special_at(7, 5) == (c.SPEC_CONVEYOR, c.RIGHT)
    assert (1, 1) in a.spawns and len(a.spawns) == len(c.SPAWN_CELLS)  # добито до 4
    # рамка форсится в стену
    assert a.is_wall(0, 0) and a.is_wall(c.COLS - 1, c.ROWS - 1)


def test_load_custom_clears_floor_under_spawns():
    data = storage.blank_map()
    data["grid"][1][1] = c.BLOCK          # заложим спавн-угол ящиком
    data["spawns"] = [[1, 1]]
    a = Arena(seed=2)
    a.load_custom(data, seed=2)
    assert a.is_floor(1, 1)               # под спавном всегда пол
