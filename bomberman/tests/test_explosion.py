"""Крестообразный взрыв: геометрия лучей, разрушение блоков, жизнь пламени."""

from src import config as c
from src.entities.bomb import Bomb
from src.entities.explosion import Explosion, detonate_chain, flame_cells
from src.world.arena import Arena


class FakeArena:
    """Пустая арена нужного размера с точечными стенами/ящиками для геометрии."""

    def __init__(self, walls=(), blocks=()):
        self.walls = set(walls)
        self.blocks = set(blocks)

    def in_bounds(self, col, row):
        return 0 <= col < c.COLS and 0 <= row < c.ROWS

    def is_wall(self, col, row):
        return not self.in_bounds(col, row) or (col, row) in self.walls

    def is_block(self, col, row):
        return (col, row) in self.blocks

    def destroy_block(self, col, row):
        if (col, row) in self.blocks:
            self.blocks.discard((col, row))
            return True
        return False


def test_center_always_present():
    cells, blocks = flame_cells(FakeArena(), 5, 5, 1)
    assert (5, 5) in cells
    assert blocks == []


def test_ray_length_equals_fire():
    cells, _ = flame_cells(FakeArena(), 5, 5, 2)
    # центр + по 2 клетки в 4 стороны
    assert (5, 3) in cells and (5, 4) in cells
    assert (5, 6) in cells and (5, 7) in cells
    assert (3, 5) in cells and (4, 5) in cells
    assert (6, 5) in cells and (7, 5) in cells
    assert (5, 2) not in cells and (8, 5) not in cells
    assert len(cells) == 1 + 4 * 2


def test_wall_stops_ray_and_is_excluded():
    a = FakeArena(walls={(7, 5)})            # стена на 2-й клетке правого луча
    cells, _ = flame_cells(a, 5, 5, 3)
    assert (6, 5) in cells                    # до стены — есть
    assert (7, 5) not in cells                # сама стена — нет
    assert (8, 5) not in cells                # за стеной — нет


def test_block_included_then_stops():
    a = FakeArena(blocks={(7, 5)})
    cells, blocks = flame_cells(a, 5, 5, 3)
    assert (6, 5) in cells
    assert (7, 5) in cells                    # ящик накрыт пламенем
    assert (8, 5) not in cells                # но луч дальше не идёт
    assert (7, 5) in blocks


def test_only_one_block_per_ray():
    a = FakeArena(blocks={(6, 5), (7, 5)})
    cells, blocks = flame_cells(a, 5, 5, 3)
    assert (6, 5) in cells and (6, 5) in blocks
    assert (7, 5) not in cells                # второй ящик за первым не задет
    assert blocks == [(6, 5)]


def test_explosion_destroys_blocks_once():
    a = FakeArena(blocks={(6, 5), (5, 6)})
    ex = Explosion(a, 5, 5, fire=1, now=0)
    assert (6, 5) not in a.blocks and (5, 6) not in a.blocks
    assert set(ex.destroyed) == {(6, 5), (5, 6)}


def test_contains_reports_flame_cells():
    ex = Explosion(FakeArena(), 5, 5, fire=1, now=0)
    assert ex.contains((5, 5)) is True
    assert ex.contains((6, 5)) is True
    assert ex.contains((9, 9)) is False


def test_life_expires_after_flame_ms():
    ex = Explosion(FakeArena(), 5, 5, fire=1, now=1000)
    assert ex.update(1000) is False
    assert ex.update(1000 + c.FLAME_MS - 1) is False
    assert ex.update(1000 + c.FLAME_MS) is True
    assert ex.done is True


def test_real_arena_border_stops_flame():
    a = Arena(seed=1)
    # взрыв в углу спавна (1,1): рамка на 0 гасит лучи вверх и влево
    cells, _ = flame_cells(a, 1, 1, 5)
    assert (0, 1) not in cells
    assert (1, 0) not in cells
    assert (1, 1) in cells


# --- Цепные детонации ---

def test_chain_detonates_bomb_in_flame():
    a = FakeArena()
    b1 = Bomb(5, 5, owner=0, fire=2, now=0)
    b2 = Bomb(7, 5, owner=0, fire=1, now=0)      # в 2 клетках — в пределах огня b1
    b1.detonate()                                 # b1 «догорела»
    explosions = []
    fresh = detonate_chain(a, [b1, b2], explosions, now=100)
    assert b2.exploded is True                    # цепь достала b2
    assert len(fresh) == 2                         # обе дали вспышку


def test_chain_skips_bomb_out_of_range():
    a = FakeArena()
    b1 = Bomb(5, 5, owner=0, fire=1, now=0)
    b2 = Bomb(9, 5, owner=0, fire=1, now=0)       # далеко — не в пламени
    b1.detonate()
    detonate_chain(a, [b1, b2], [], now=0)
    assert b2.exploded is False


def test_chain_is_transitive():
    a = FakeArena()
    # цепочка через одну клетку: 3→5→7, у каждой fire=2
    b1 = Bomb(3, 5, owner=0, fire=2, now=0)
    b2 = Bomb(5, 5, owner=0, fire=2, now=0)
    b3 = Bomb(7, 5, owner=0, fire=2, now=0)
    b1.detonate()
    detonate_chain(a, [b1, b2, b3], [], now=0)
    assert b2.exploded and b3.exploded            # взрыв прокатился до конца


def test_chain_ignores_unexploded():
    a = FakeArena()
    b = Bomb(5, 5, owner=0, fire=1, now=0)        # фитиль ещё горит
    explosions = []
    fresh = detonate_chain(a, [b], explosions, now=0)
    assert fresh == [] and b.exploded is False
