"""ИИ-помощники: BFS, карта опасности, шаги к цели, бегство, путь отхода."""

from src import ai
from src import config as c
from src.entities.bomb import Bomb
from src.world.arena import Arena


def open_arena():
    """Только рамка и столбы (чёт/чёт), остальное — пол."""
    return Arena(seed=1, density=0.0)


def set_block(a, col, row):
    a.grid[row][col] = c.BLOCK


def test_direction_to_orthogonal():
    assert ai.direction_to((3, 3), (4, 3)) == c.RIGHT
    assert ai.direction_to((3, 3), (3, 2)) == c.UP
    assert ai.direction_to((3, 3), (5, 3)) is None       # не соседи


def test_bfs_reaches_and_measures():
    a = open_arena()
    dist, prev = ai.bfs(a, (1, 1))
    assert dist[(1, 1)] == 0
    assert dist[(1, 3)] == 2                              # через (1,2)
    assert (0, 0) not in dist                             # стена недостижима


def test_bfs_blocked_by_bomb():
    a = open_arena()
    # коридор столбцом 1: перекроем (1,2) бомбой — (1,3) недостижим этим путём
    dist, _ = ai.bfs(a, (1, 1), bomb_cells={(1, 2)})
    # (1,3) можно обойти через (3,1)->(3,3)->... но не короче; проверим что (1,2) закрыт
    assert (1, 2) not in dist


def test_first_step_returns_direction():
    a = open_arena()
    _, prev = ai.bfs(a, (1, 1))
    assert ai.first_step(prev, (1, 1), (1, 3)) == c.DOWN


def test_danger_map_marks_bomb_line_and_flame():
    a = open_arena()
    b = Bomb(1, 1, fire=2, now=0)
    danger = ai.danger_map(a, [b], [], now=0)
    assert danger[(1, 1)] == c.FUSE_MS                   # центр — время до взрыва
    assert (1, 3) in danger                              # луч вниз достаёт
    assert (3, 1) in danger                              # луч вправо (кроме столба (2,1)? (2,1) пол)


def test_is_safe():
    danger = {(1, 1): 500}
    assert ai.is_safe((1, 1), danger) is False
    assert ai.is_safe((5, 5), danger) is True


def test_flee_step_moves_out_of_danger():
    a = open_arena()
    b = Bomb(1, 1, fire=1, now=0)
    danger = ai.danger_map(a, [b], [], now=0)
    # стоим в (1,1) под будущим взрывом — должны шагнуть к безопасной клетке
    d = ai.flee_step(a, (1, 1), danger)
    assert d in (c.DOWN, c.RIGHT)                         # прочь по коридору
    # уже безопасная клетка — бежать некуда
    assert ai.flee_step(a, (5, 5), danger) is None


def test_block_targets_finds_neighbors():
    a = open_arena()
    set_block(a, 3, 1)                                    # ящик у прохода
    goals = ai.block_targets(a, (1, 1))
    assert (3, 2) in goals or (1, 1) in goals or (3, 3) in goals
    assert all(a.is_floor(*g) for g in goals)


def test_hits_from_detects_target_in_line():
    a = open_arena()
    assert ai.hits_from(a, (1, 1), fire=3, targets={(1, 3)}) is True
    assert ai.hits_from(a, (1, 1), fire=1, targets={(1, 3)}) is False   # коротко


def test_nearest_picks_closest_reachable():
    a = open_arena()
    goal, step = ai.nearest(a, (1, 1), {(1, 5), (1, 3)})
    assert goal == (1, 3)                                 # ближе
    assert step == c.DOWN


def test_escape_exists_true_in_open_and_false_when_boxed():
    a = open_arena()
    b = Bomb(1, 1, fire=1, now=0)
    assert ai.escape_exists(a, (1, 1), [b], [], now=0) is True
    # Замуровываем угол (1,1): соседи (2,1) и (1,2) в стены/блоки
    a.grid[1][2] = c.BLOCK
    a.grid[2][1] = c.BLOCK
    assert ai.escape_exists(a, (1, 1), [b], [], now=0) is False
