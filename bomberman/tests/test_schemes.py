"""Схемы карт: узоры стен, плотность, связность поля (без pygame)."""

from src import config as c
from src.world import schemes
from src.world.arena import Arena, safe_cells, is_border


def _reachable_from(a, start):
    """Множество клеток, достижимых от start по НЕ-стенам (пол+ящики)."""
    seen = {start}
    stack = [start]
    while stack:
        col, row = stack.pop()
        for dc, dr in (c.UP, c.DOWN, c.LEFT, c.RIGHT):
            nc, nr = col + dc, row + dr
            if (nc, nr) in seen:
                continue
            if a.in_bounds(nc, nr) and not a.is_wall(nc, nr):
                seen.add((nc, nr))
                stack.append((nc, nr))
    return seen


def test_have_twenty_levels():
    assert schemes.LEVELS == 20
    assert len(schemes.SCHEMES) == 20


def test_density_ramps_up():
    ds = [s.density for s in schemes.SCHEMES]
    assert ds[0] < ds[-1]
    assert all(0.0 <= d <= 1.0 for d in ds)


def test_scheme_for_wraps():
    assert schemes.scheme_for(1) is schemes.SCHEMES[0]
    assert schemes.scheme_for(20) is schemes.SCHEMES[19]
    assert schemes.scheme_for(21) is schemes.SCHEMES[0]   # по кругу


def test_all_schemes_keep_spawns_connected():
    """Ни один узор стен не должен изолировать угол-спавн."""
    for level in range(1, schemes.LEVELS + 1):
        scheme = schemes.scheme_for(level)
        for seed in range(6):
            a = Arena(seed=seed, scheme=scheme)
            reach = _reachable_from(a, a.spawns[0])
            for sp in a.spawns:
                assert sp in reach, f"{scheme.name}: спавн {sp} отрезан (seed={seed})"


def test_walls_never_on_safe_cells():
    safe = safe_cells()
    for level in range(1, schemes.LEVELS + 1):
        a = Arena(seed=0, scheme=schemes.scheme_for(level))
        for col, row in safe:
            assert a.is_floor(col, row)


def test_border_always_wall_every_scheme():
    for level in range(1, schemes.LEVELS + 1):
        a = Arena(seed=1, scheme=schemes.scheme_for(level))
        for col in range(c.COLS):
            for row in range(c.ROWS):
                if is_border(col, row):
                    assert a.is_wall(col, row)


def test_open_scheme_has_no_interior_walls():
    # «Открытая» — уровень 2 в цикле
    a = Arena(seed=3, scheme=schemes.SCHEMES[1])
    for row in range(1, c.ROWS - 1):
        for col in range(1, c.COLS - 1):
            assert not a.is_wall(col, row)


def test_default_arena_is_classic():
    a = Arena(seed=1)
    assert a.scheme is schemes.CLASSIC
    # классические столбы на месте
    for row in range(2, c.ROWS - 1, 2):
        for col in range(2, c.COLS - 1, 2):
            assert a.is_wall(col, row)


# --- Спец-тайлы ---

def _open_scheme():
    return next(s for s in schemes.SCHEMES if s.specials is not None)


def test_specials_present_on_open_scheme():
    a = Arena(seed=1, scheme=_open_scheme())
    assert a.specials                                 # что-то расставлено
    kinds = {kind for kind, _d in a.specials.values()}
    assert c.SPEC_TELEPORT in kinds
    assert c.SPEC_CONVEYOR in kinds
    assert c.SPEC_TRAMPOLINE in kinds


def test_specials_are_on_floor_not_safe():
    from src.world.arena import safe_cells, is_border
    a = Arena(seed=2, scheme=_open_scheme())
    safe = safe_cells()
    for col, row in a.specials:
        assert a.is_floor(col, row)                    # всегда пол
        assert not is_border(col, row)
        assert (col, row) not in safe


def test_teleport_cells_pair():
    a = Arena(seed=1, scheme=_open_scheme())
    assert len(a.teleport_cells()) == 2


def test_normal_scheme_has_no_specials():
    a = Arena(seed=1, scheme=schemes.SCHEMES[0])       # «Классика» — без спец-тайлов
    assert a.specials == {}
    assert a.special_at(3, 3) is None


def test_drop_wall_removes_special():
    a = Arena(seed=1, scheme=_open_scheme())
    cell = next(iter(a.specials))
    assert a.drop_wall(*cell) is True
    assert a.special_at(*cell) is None                 # спец-тайл снесён стеной
