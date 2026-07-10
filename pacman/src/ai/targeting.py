"""Цели призраков и выбор направления — чистая логика (тестируется headless).

Каждый призрак стремится к своей **целевой клетке**; на развилке выбирает
соседа, ближайшего к цели по прямой (евклидово), не разворачиваясь назад —
классическое правило Pac-Man. У каждого своя цель:

    Blinky — клетка Пакмана;
    Pinky  — 4 клетки перед Пакманом (с «багом» взгляда вверх);
    Inky   — вектор от Blinky через точку в 2 клетках перед Пакманом, ×2;
    Clyde  — Пакман, если дальше 8 клеток, иначе свой угол (робеет вблизи).

В режиме scatter цель — угол-«дом», в frightened — случайный поворот.
"""

from .. import config as c

# Порядок перебора для разрешения ничьих (классический приоритет)
_ORDER = (c.UP, c.LEFT, c.DOWN, c.RIGHT)


def ahead(col, row, direction, n):
    """Клетка на `n` вперёд по направлению. Взгляд вверх — с историческим
    «багом»: цель уходит ещё и на `n` влево."""
    if direction == c.UP:
        return (col - n, row - n)
    return (col + direction[0] * n, row + direction[1] * n)


def target_blinky(pac_col, pac_row, pac_dir):
    return (pac_col, pac_row)


def target_pinky(pac_col, pac_row, pac_dir):
    return ahead(pac_col, pac_row, pac_dir, 4)


def target_inky(pac_col, pac_row, pac_dir, blinky_col, blinky_row):
    px, py = ahead(pac_col, pac_row, pac_dir, 2)
    return (2 * px - blinky_col, 2 * py - blinky_row)


def target_clyde(pac_col, pac_row, pac_dir, clyde_col, clyde_row):
    d2 = (clyde_col - pac_col) ** 2 + (clyde_row - pac_row) ** 2
    if d2 > 64:                       # дальше 8 клеток — гонит
        return (pac_col, pac_row)
    return c.SCATTER_TARGETS[c.CLYDE]  # близко — уходит в угол


def chase_target(name, pac_tile, pac_dir, blinky_tile, self_tile):
    """Цель призрака `name` в режиме chase."""
    if name == c.BLINKY:
        return target_blinky(*pac_tile, pac_dir)
    if name == c.PINKY:
        return target_pinky(*pac_tile, pac_dir)
    if name == c.INKY:
        return target_inky(*pac_tile, pac_dir, *blinky_tile)
    return target_clyde(*pac_tile, pac_dir, *self_tile)


def best_dir(maze, col, row, cur_dir, target, gate_ok=False):
    """Направление к цели: минимум расстояния соседа, без разворота."""
    best, best_d = None, None
    rev = (-cur_dir[0], -cur_dir[1])
    for d in _ORDER:
        if d == rev:
            continue
        nc, nr = col + d[0], row + d[1]
        if maze.blocked_ghost(nc, nr, gate_ok):
            continue
        dist = (nc - target[0]) ** 2 + (nr - target[1]) ** 2
        if best_d is None or dist < best_d:
            best, best_d = d, dist
    if best is None:                  # тупик — разрешаем развернуться
        return rev
    return best


def frightened_dir(maze, col, row, cur_dir, rng, gate_ok=False):
    """Случайный допустимый поворот (без разворота), как в испуге."""
    rev = (-cur_dir[0], -cur_dir[1])
    opts = []
    for d in _ORDER:
        if d == rev:
            continue
        if not maze.blocked_ghost(col + d[0], row + d[1], gate_ok):
            opts.append(d)
    if not opts:
        return rev
    return rng.choice(opts)
