"""Клеточные коллизии Level.hit / solids_near (нужен pygame для Rect/Level)."""

import pytest

pygame = pytest.importorskip("pygame")

from src import config as c            # noqa: E402
from src.world.level import Level      # noqa: E402


def sample_map():
    grid = [["." for _ in range(c.COLS)] for _ in range(c.ROWS)]
    grid[6][6] = "B"                   # кирпич в клетке (col=6, row=6)
    grid[6][8] = "S"                   # сталь в (8, 6)
    grid[c.ROWS - 1][6] = "A"          # база снизу
    grid[c.ROWS - 2][6] = "P"
    grid[0][0] = "E"
    return ["".join(r) for r in grid]


def bullet_rect(col, row):
    """Маленький прямоугольник в центре клетки."""
    return pygame.Rect(col * c.TILE + c.TILE // 2, row * c.TILE + c.TILE // 2, 6, 6)


def test_hit_brick_destroys(pg):
    lv = Level(sample_map())
    assert lv.hit(bullet_rect(6, 6)) == "brick"
    assert (6, 6) not in lv.bricks


def test_hit_steel_blocks_without_pierce(pg):
    lv = Level(sample_map())
    assert lv.hit(bullet_rect(8, 6)) == "steel"
    assert (8, 6) in lv.steels         # не пробита


def test_hit_steel_pierced(pg):
    lv = Level(sample_map())
    assert lv.hit(bullet_rect(8, 6), pierce_steel=True) == "steel"
    assert (8, 6) not in lv.steels     # пробита насквозь


def test_hit_base(pg):
    lv = Level(sample_map())
    assert lv.hit(lv.base_rect().inflate(-10, -10)) == "base"
    assert not lv.base_alive


def test_hit_empty_none(pg):
    lv = Level(sample_map())
    assert lv.hit(bullet_rect(3, 3)) is None


def test_solids_near_is_local(pg):
    lv = Level(sample_map())
    full = {(r.x, r.y) for r in lv.solid_rects()}
    near = {(r.x, r.y) for r in lv.solids_near(bullet_rect(6, 6))}
    assert near <= full                                    # подмножество
    assert (6 * c.TILE, 6 * c.TILE) in near                # соседний кирпич попал
    far = {(r.x, r.y) for r in lv.solids_near(bullet_rect(1, 1))}
    assert (6 * c.TILE, 6 * c.TILE) not in far             # далёкий кирпич — нет


def test_solids_near_full_field_matches_all(pg):
    lv = Level(sample_map())
    whole = pygame.Rect(0, 0, c.FIELD_W, c.FIELD_H)
    near = {(r.x, r.y) for r in lv.solids_near(whole)}
    full = {(r.x, r.y) for r in lv.solid_rects()}
    assert near == full


def test_cell_bounds_matches_colliderect(pg):
    """Клеточная математика эквивалентна перебору colliderect по всем клеткам."""
    import random
    lv = Level(sample_map())
    random.seed(7)
    for _ in range(3000):
        w, h = random.randint(1, 14), random.randint(1, 14)
        x = random.randint(-6, c.FIELD_W)
        y = random.randint(-6, c.FIELD_H)
        rect = pygame.Rect(x, y, w, h)
        c0, c1, r0, r1 = lv._cell_bounds(rect)
        via = {(col, row) for col in range(c0, c1 + 1) for row in range(r0, r1 + 1)}
        brute = set()
        for col in range(c.COLS):
            for row in range(c.ROWS):
                if rect.colliderect(pygame.Rect(col * c.TILE, row * c.TILE,
                                                c.TILE, c.TILE)):
                    brute.add((col, row))
        assert via == brute
