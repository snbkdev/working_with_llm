"""Цели призраков и выбор направления (чистая логика)."""

from src import config as c
from src.ai import targeting as ai
from src.world.maze import Maze


def test_blinky_targets_pacman():
    assert ai.target_blinky(10, 5, c.RIGHT) == (10, 5)


def test_pinky_four_ahead():
    assert ai.target_pinky(10, 5, c.RIGHT) == (14, 5)
    assert ai.target_pinky(10, 5, c.LEFT) == (6, 5)


def test_pinky_up_bug():
    # Взгляд вверх: цель уходит вверх И влево (исторический баг)
    assert ai.target_pinky(10, 5, c.UP) == (6, 1)


def test_inky_doubles_vector_through_blinky():
    # Пакман (10,5) вправо → точка перед ним (12,5); Blinky (8,5)
    # вектор Blinky→точка = (4,0), удваиваем от точки → (16,5)
    assert ai.target_inky(10, 5, c.RIGHT, 8, 5) == (16, 5)


def test_clyde_far_chases_close_scatters():
    # Далеко (>8) — гонит Пакмана
    assert ai.target_clyde(10, 5, c.RIGHT, 25, 25) == (10, 5)
    # Вплотную — уходит в свой угол
    assert ai.target_clyde(10, 5, c.RIGHT, 10, 6) == c.SCATTER_TARGETS[c.CLYDE]


def test_best_dir_no_reverse_and_towards_target():
    maze = Maze()
    # На открытом ряду 5 идём вправо к цели справа — не разворачиваемся
    d = ai.best_dir(maze, 10, 5, c.RIGHT, (26, 5))
    assert d == c.RIGHT


def test_best_dir_avoids_walls():
    maze = Maze()
    # из (13,23) вверх стена — не должен выбрать UP
    d = ai.best_dir(maze, 13, 23, c.LEFT, (13, 0))
    assert d != c.UP
    assert not maze.blocked_ghost(13 + d[0], 23 + d[1])
