"""Проверки лабиринта: размеры, энергайзеры, связность, тоннель."""

from collections import deque

from src import config as c
from src.world import maze as m


def test_dimensions():
    assert len(m.LAYOUT) == c.ROWS
    assert all(len(line) == c.COLS for line in m.LAYOUT)


def test_four_energizers():
    grid = m.Maze()
    n = sum(row.count(m.ENERGIZER) for row in grid.grid)
    assert n == 4


def test_dot_count_matches():
    grid = m.Maze()
    counted = sum(1 for r in range(c.ROWS) for col in range(c.COLS)
                  if grid.grid[r][col] in (m.DOT, m.ENERGIZER))
    assert grid.dots_left == counted
    assert grid.dots_left > 200          # полноценный лабиринт


def test_spawn_is_open():
    grid = m.Maze()
    assert not grid.blocked(13, 23)


def test_tunnel_open_at_edges():
    grid = m.Maze()
    assert not grid.blocked(-1, c.TUNNEL_ROW)
    assert not grid.blocked(c.COLS, c.TUNNEL_ROW)
    # вне тоннеля край закрыт
    assert grid.blocked(-1, 5)


def _reachable(grid):
    start = (13, 23)
    seen = {start}
    q = deque([start])
    while q:
        col, row = q.popleft()
        for dx, dy in (c.UP, c.DOWN, c.LEFT, c.RIGHT):
            ncol, nrow = col + dx, row + dy
            if nrow == c.TUNNEL_ROW:            # обёртка тоннеля
                ncol %= c.COLS
            if (ncol, nrow) in seen:
                continue
            if not grid.blocked(ncol, nrow):
                seen.add((ncol, nrow))
                q.append((ncol, nrow))
    return seen


def test_all_dots_reachable_from_spawn():
    """Флуд-фолл из старта должен накрыть все точки — уровень проходим."""
    grid = m.Maze()
    seen = _reachable(grid)
    dots = {(col, row) for row in range(c.ROWS) for col in range(c.COLS)
            if grid.grid[row][col] in (m.DOT, m.ENERGIZER)}
    assert dots <= seen


def test_all_layouts_valid_and_connected():
    """Каждая схема: 28×31, 4 энергайзера, все точки достижимы, дом на месте."""
    for idx in range(len(m.LAYOUTS)):
        layout = m.LAYOUTS[idx]
        assert len(layout) == c.ROWS
        assert all(len(line) == c.COLS for line in layout)
        grid = m.Maze(idx)
        assert sum(row.count(m.ENERGIZER) for row in grid.grid) == 4
        assert not grid.blocked(*(13, 23))
        assert not grid.blocked_ghost(13, 11, gate_ok=True)
        seen = _reachable(grid)
        dots = {(col, row) for row in range(c.ROWS) for col in range(c.COLS)
                if grid.grid[row][col] in (m.DOT, m.ENERGIZER)}
        assert dots <= seen, f"схема {idx}: недостижимые точки {sorted(dots - seen)}"
