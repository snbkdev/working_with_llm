"""Параметры уровня: скорости и тайминги растут с номером уровня.

Берём базу из выбранной **сложности** (`config.DIFFS`) и усиливаем её с каждым
уровнем — Пакман и призраки быстрее, испуг короче, chase длиннее (как в
оригинале, где к высоким уровням призраки почти не отвлекаются на scatter).
Чистые вычисления — тестируются headless.
"""

from .. import config as c


def params(level, difficulty):
    base = c.DIFFS[difficulty]
    lv = max(0, level - 1)
    return {
        "pac_speed": min(1.0, 0.80 + 0.02 * lv),
        "ghost_speed": min(0.98, base["ghost_speed"] + 0.015 * lv),
        "fright_ms": max(1000, base["fright_ms"] - 400 * lv),
        "scatter_ms": max(3000, base["scatter_ms"] - 250 * lv),
        "chase_ms": base["chase_ms"] + 500 * lv,
    }
