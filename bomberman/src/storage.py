"""Хранилище пользовательских карт (JSON, без pygame).

Карта — это словарь: размеры, сетка тайлов (пол/стена/ящик), спец-тайлы и точки
спавна. Функции чистые (json + файловая система), поэтому легко тестируются с
временным каталогом. Формат:

    {
      "cols": 15, "rows": 11,
      "grid": [[t, ...], ...],                 # c.FLOOR / c.WALL / c.BLOCK
      "specials": {"c,r": [kind, [dx, dy] | null]},
      "spawns": [[c, r], ...]                   # 1..4 угла-старта
    }
"""

import json
from pathlib import Path

from . import config as c

MAPS_DIR = Path(__file__).resolve().parent.parent / "maps"


def maps_dir(directory=None):
    d = Path(directory) if directory else MAPS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def map_path(name, directory=None):
    fname = name if str(name).endswith(".json") else f"{name}.json"
    return maps_dir(directory) / fname


def list_maps(directory=None):
    """Пути ко всем сохранённым картам (отсортированы по имени)."""
    return sorted(maps_dir(directory).glob("*.json"))


def blank_map():
    """Пустая карта: несокрушимая рамка, столбы чёт/чёт, 4 угла-спавна."""
    grid = [[c.FLOOR] * c.COLS for _ in range(c.ROWS)]
    for col in range(c.COLS):
        grid[0][col] = grid[c.ROWS - 1][col] = c.WALL
    for row in range(c.ROWS):
        grid[row][0] = grid[row][c.COLS - 1] = c.WALL
    for row in range(2, c.ROWS - 1, 2):
        for col in range(2, c.COLS - 1, 2):
            grid[row][col] = c.WALL
    return {
        "cols": c.COLS, "rows": c.ROWS,
        "grid": grid, "specials": {}, "spawns": [list(s) for s in c.SPAWN_CELLS],
    }


def valid(data):
    """Поверхностная проверка формата и размеров карты."""
    if not isinstance(data, dict):
        return False
    if data.get("cols") != c.COLS or data.get("rows") != c.ROWS:
        return False
    grid = data.get("grid")
    if not isinstance(grid, list) or len(grid) != c.ROWS:
        return False
    return all(isinstance(r, list) and len(r) == c.COLS for r in grid)


def save_map(data, name, directory=None):
    """Сохраняет карту в JSON. Возвращает путь к файлу."""
    p = map_path(name, directory)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def load_map(name, directory=None):
    """Загружает карту по имени/пути. None, если файла нет или формат битый."""
    p = Path(name) if Path(name).suffix == ".json" and Path(name).exists() \
        else map_path(name, directory)
    try:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if valid(data) else None
