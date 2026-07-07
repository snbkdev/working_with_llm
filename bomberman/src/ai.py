"""ИИ-помощники: поиск пути по сетке и карта опасности от бомб/пламени.

Всё здесь — чистая логика на клетках (без pygame), поэтому поведение ботов
тестируется headless. Бот (`entities/bot.py`) собирает из этих кирпичей свои
решения: куда идти, когда ставить бомбу и куда убегать от взрыва.
"""

from collections import deque

from . import config as c
from .entities.explosion import flame_cells

_DIRS = (c.UP, c.DOWN, c.LEFT, c.RIGHT)


def neighbors(cell):
    col, row = cell
    return [(col + dx, row + dy) for dx, dy in _DIRS]


def direction_to(a, b):
    """Единичное направление от клетки a к соседней b (или None)."""
    if abs(b[0] - a[0]) + abs(b[1] - a[1]) != 1:
        return None                              # только для смежных клеток
    return (b[0] - a[0], b[1] - a[1])


def _walkable(arena, cell, bomb_cells, start):
    """Проходима ли клетка для поиска пути (пол, не бомба; старт всегда можно)."""
    if cell == start:
        return True
    col, row = cell
    if not arena.is_floor(col, row):
        return False
    return cell not in bomb_cells


def bfs(arena, start, bomb_cells=frozenset(), blocked=frozenset()):
    """Волновой обход от start по проходимым клеткам. Возвращает (dist, prev)."""
    dist = {start: 0}
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nb in neighbors(cur):
            if nb in dist or nb in blocked:
                continue
            if not _walkable(arena, nb, bomb_cells, start):
                continue
            dist[nb] = dist[cur] + 1
            prev[nb] = cur
            q.append(nb)
    return dist, prev


def reconstruct(prev, target):
    """Путь [start..target] по словарю предков (пусто, если недостижимо)."""
    if target not in prev:
        return []
    path = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def first_step(prev, start, target):
    """Направление первого шага пути start→target (или None)."""
    path = reconstruct(prev, target)
    if len(path) < 2 or path[0] != start:
        return None
    return direction_to(path[0], path[1])


def danger_map(arena, bombs, explosions, now):
    """Клетка → мс до того, как её накроет пламя (0 = горит прямо сейчас).

    Учитывает активные взрывы (0) и будущие взрывы бомб (их time_left).
    Дистанционные (remote) бомбы считаем «отложенной» угрозой (полный фитиль).
    Клетки вне карты — безопасны.
    """
    danger = {}
    for ex in explosions:
        for cell in ex.cells:
            danger[cell] = 0
    for b in bombs:
        t = c.FUSE_MS if getattr(b, "remote", False) else b.time_left(now)
        cells, _ = flame_cells(arena, b.col, b.row, b.fire)
        for cell in cells:
            if cell not in danger or t < danger[cell]:
                danger[cell] = t
    return danger


def is_safe(cell, danger):
    """Клетка не под будущим/текущим взрывом."""
    return cell not in danger


def flee_step(arena, start, danger, bomb_cells=frozenset(), max_dist=10):
    """Направление к ближайшей безопасной клетке (или None, если уже безопасно).

    Через горящие сейчас клетки (danger==0) не ходим. Если полностью безопасной
    клетки рядом нет — идём туда, где до взрыва больше всего времени.
    """
    if is_safe(start, danger):
        return None
    burning = {cell for cell, t in danger.items() if t == 0 and cell != start}
    dist, prev = bfs(arena, start, bomb_cells, blocked=burning)
    best = None
    best_key = None
    for cell, d in dist.items():
        if cell == start or d > max_dist:
            continue
        # Предпочитаем безопасные и близкие; иначе — с наибольшим запасом времени
        safe = is_safe(cell, danger)
        key = (safe, danger.get(cell, c.FUSE_MS * 2) - d, -d)
        if best_key is None or key > best_key:
            best_key, best = key, cell
    if best is None:
        return None
    return first_step(prev, start, best)


def nearest(arena, start, goals, bomb_cells=frozenset()):
    """Ближайшая достижимая клетка из набора goals и шаг к ней (cell, dir)."""
    if not goals:
        return None, None
    dist, prev = bfs(arena, start, bomb_cells)
    reachable = [(dist[g], g) for g in goals if g in dist]
    if not reachable:
        return None, None
    reachable.sort()
    goal = reachable[0][1]
    return goal, first_step(prev, start, goal)


def step_towards(arena, start, goal, bomb_cells=frozenset()):
    """Направление первого шага к цели по кратчайшему пути (или None)."""
    dist, prev = bfs(arena, start, bomb_cells)
    if goal not in dist:
        return None
    return first_step(prev, start, goal)


def block_targets(arena, cell):
    """Проходимые клетки, соседние с разрушаемым ящиком (где встать, чтобы ломать)."""
    goals = set()
    for row in range(c.ROWS):
        for col in range(c.COLS):
            if arena.is_block(col, row):
                for nb in neighbors((col, row)):
                    ncol, nrow = nb
                    if arena.in_bounds(ncol, nrow) and arena.is_floor(ncol, nrow):
                        goals.add(nb)
    return goals


def hits_from(arena, cell, fire, targets):
    """Есть ли среди targets клетка, попадающая под пламя бомбы из cell."""
    cells, _ = flame_cells(arena, cell[0], cell[1], fire)
    return any(t in cells for t in targets)


def escape_exists(arena, start, bombs, explosions, now, max_dist=8):
    """Найдётся ли достижимая безопасная клетка (учёт всех бомб, включая новую).

    Нужен боту, чтобы не ставить бомбу, из-под которой не убежать.
    """
    danger = danger_map(arena, bombs, explosions, now)
    bomb_cells = {b.cell for b in bombs}
    burning = {cell for cell, t in danger.items() if t == 0 and cell != start}
    dist, _ = bfs(arena, start, bomb_cells, blocked=burning)
    for cell, d in dist.items():
        if cell != start and d <= max_dist and is_safe(cell, danger):
            return True
    return False
