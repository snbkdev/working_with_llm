"""Проверки движения Пакмана: ходьба, стены, буфер поворота, тоннель, еда."""

from src import config as c
from src.world.maze import Maze
from src.entities.pacman import Pacman


def run(pac, maze, frames):
    total = 0
    for _ in range(frames):
        total += pac.update(maze)
    return total


def test_moves_left_along_corridor():
    maze = Maze()
    pac = Pacman(13, 23)              # ряд-коридор с точками
    pac.want_dir = c.LEFT
    run(pac, maze, c.TILE // c.PACMAN_SPEED)   # ровно одна клетка
    assert (pac.col, pac.row) == (12, 23)
    assert pac.dir == c.LEFT


def test_blocked_turn_keeps_idle():
    maze = Maze()
    pac = Pacman(13, 23)
    pac.want_dir = c.UP              # прямо над стартом — стена (##)
    run(pac, maze, 30)
    assert (pac.col, pac.row) == (13, 23)   # не сдвинулся
    assert pac.dir == c.NONE                # поворот не применился


def test_stops_at_wall():
    maze = Maze()
    pac = Pacman(13, 23)
    pac.want_dir = c.LEFT           # едет влево до стены на col5
    run(pac, maze, 200)
    assert (pac.col, pac.row) == (6, 23)    # уперся, col5 — стена
    assert pac.moving is False
    assert pac.dir == c.LEFT


def test_turn_buffer_applies_at_junction():
    """Заранее нажатый поворот срабатывает, как откроется проход."""
    maze = Maze()
    pac = Pacman(6, 23)             # вертикальный коридор на col6
    pac.want_dir = c.UP
    run(pac, maze, c.TILE // c.PACMAN_SPEED)
    assert (pac.col, pac.row) == (6, 22)
    assert pac.dir == c.UP


def test_tunnel_wraps_around():
    maze = Maze()
    pac = Pacman(1, c.TUNNEL_ROW)   # ряд тоннеля, у левого края
    pac.want_dir = c.LEFT
    run(pac, maze, c.TILE // c.PACMAN_SPEED * 3)
    assert pac.col >= c.COLS - 3    # появился у правого края


def test_eating_scores_and_decrements():
    maze = Maze()
    before = maze.dots_left
    pac = Pacman(13, 23)
    pac.want_dir = c.LEFT
    gained = run(pac, maze, c.TILE // c.PACMAN_SPEED * 3)
    assert gained > 0
    assert maze.dots_left < before


def test_stops_when_key_released():
    """Отпустил клавишу — Пакман докатывается до центра клетки и стоит."""
    maze = Maze()
    pac = Pacman(13, 23)
    pac.want_dir = c.LEFT
    run(pac, maze, 3)               # тронулся, между клетками
    pac.want_dir = None             # клавишу отпустили
    run(pac, maze, c.TILE)          # даём доехать до центра
    assert pac.moving is False
    assert pac._aligned()           # остановка строго в центре клетки
    assert (pac.col, pac.row) == (12, 23)


def test_reverse_is_immediate():
    maze = Maze()
    pac = Pacman(13, 23)
    pac.want_dir = c.LEFT
    run(pac, maze, 3)               # тронулся влево, ещё не в центре
    pac.want_dir = c.RIGHT
    pac.update(maze)
    assert pac.dir == c.RIGHT
