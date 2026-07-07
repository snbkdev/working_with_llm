"""Движение игрока: коллизии со стенами, привязка к полосе, границы (без pygame)."""

from src import config as c
from src.world.arena import Arena
from src.entities.player import Player
from src.entities.explosion import Explosion


class _FlatArena:
    """Пустая проходимая арена для проверки пламени по клеткам."""

    def in_bounds(self, col, row):
        return 0 <= col < c.COLS and 0 <= row < c.ROWS

    def is_wall(self, col, row):
        return not self.in_bounds(col, row)

    def is_block(self, col, row):
        return False

    def destroy_block(self, col, row):
        return False


def test_kill_sets_flags_and_is_idempotent():
    p = Player(5, 5)
    p.kill(now=100)
    assert p.alive is False and p.dead_at == 100
    p.kill(now=500)                      # повторная гибель не сдвигает время
    assert p.dead_at == 100


def test_respawn_revives_at_cell():
    p = Player(5, 5)
    p.kill(now=100)
    p.respawn(1, 1)
    assert p.alive is True and p.dead_at is None
    assert p.cell == (1, 1)


def test_in_flame_detects_overlap():
    p = Player(5, 5)
    ex = Explosion(_FlatArena(), 5, 5, fire=2, now=0)   # накрывает (5,5)
    assert p.in_flame([ex]) is True


def test_in_flame_false_when_clear():
    p = Player(1, 1)
    ex = Explosion(_FlatArena(), 8, 8, fire=1, now=0)
    assert p.in_flame([ex]) is False
    assert p.in_flame([]) is False


def open_arena():
    """Арена без ящиков — только рамка и внутренние столбы."""
    return Arena(seed=1, density=0.0)


def test_bomb_under_player_is_passable_then_blocks():
    a = open_arena()
    p = Player(1, 1)                         # угол спавна, вокруг пол
    here = p.cell
    # Бомба под игроком — можно уйти с клетки
    assert p.try_move(a, c.RIGHT, [here]) is True
    # Дошагиваем, пока полностью не сойдём с клетки бомбы
    for _ in range(c.TILE // c.PLAYER_SPEED + 2):
        p.try_move(a, c.RIGHT, [here])
        if here not in p._cells_at(p.x, p.y):
            break
    assert here not in p._cells_at(p.x, p.y)
    # Теперь бомба — препятствие: назад на её клетку не пускает
    blocked = True
    for _ in range(c.TILE // c.PLAYER_SPEED + 2):
        if p.try_move(a, c.LEFT, [here]) and here in p._cells_at(p.x, p.y):
            blocked = False
            break
    assert blocked is True


def test_other_bomb_blocks_immediately():
    a = open_arena()
    p = Player(1, 1)
    right = (2, 1)                           # соседняя клетка с чужой бомбой
    # столб? нет: (2,1) — не чёт/чёт, значит пол; ставим туда бомбу
    moved = p.try_move(a, c.RIGHT, [right])
    # не должен въехать в клетку с бомбой
    assert right not in p._cells_at(p.x, p.y)


def test_spawns_on_floor_cell():
    a = open_arena()
    p = Player(*a.spawns[0])
    assert p.cell == a.spawns[0]
    assert a.is_floor(*p.cell)


def test_moves_right_along_open_lane():
    a = open_arena()
    p = Player(1, 1)                 # верхняя открытая полоса (row=1)
    x0 = p.x
    assert p.try_move(a, c.RIGHT) is True
    assert p.x == x0 + c.PLAYER_SPEED
    assert p.y == float(1 * c.TILE + p.offset)   # полоса не съехала


def test_blocked_by_border_wall():
    a = open_arena()
    p = Player(1, 1)
    # Упираемся влево в рамку (col 0) — много шагов, дальше стены не пройти
    for _ in range(40):
        p.try_move(a, c.LEFT)
    assert not p._blocked(a, p.x, p.y)
    assert p.x >= c.TILE                          # не залез в рамку (col 0)
    assert p.try_move(a, c.LEFT) is False or p.x >= c.TILE


def test_blocked_by_interior_pillar():
    a = open_arena()
    # Столб в (2,2). Встаём в (1,2) и идём вправо — упрёмся в столб.
    p = Player(1, 2)
    moved_any = False
    for _ in range(40):
        if p.try_move(a, c.RIGHT):
            moved_any = True
    assert moved_any
    # Не пересекли столб: правый край левее клетки столба (col 2)
    assert p.x + p.size <= 2 * c.TILE + 1


def test_snap_slides_into_gap():
    a = open_arena()
    p = Player(1, 1)
    # Слегка сместим по вертикали и пойдём вбок — привязка вернёт на полосу
    p.y += 3
    p.try_move(a, c.RIGHT)
    assert p.y == float(1 * c.TILE + p.offset)


def test_cannot_leave_field_bounds():
    a = open_arena()
    p = Player(1, 1)
    for _ in range(60):
        p.try_move(a, c.UP)
    assert p.y >= 0
    assert p.y >= c.TILE - p.size                 # не выше рамки-стены


def test_none_direction_is_noop():
    a = open_arena()
    p = Player(1, 1)
    pos = (p.x, p.y)
    assert p.try_move(a, None) is False
    assert (p.x, p.y) == pos


def test_block_is_obstacle():
    a = Arena(seed=5)                # с ящиками
    # Найдём ящик рядом со свободной клеткой и убедимся, что он не проходим
    for col, row in a.block_cells():
        assert a.is_solid(col, row)
        break
