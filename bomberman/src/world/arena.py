"""Арена: сетка пола, несокрушимых столбов и разрушаемых ящиков.

Классическая раскладка Bomberman: по краю — сплошная рамка-стена, внутри —
столбы в клетках, где и колонка, и ряд чётные. Остальное — пол, который
процедурно засыпается ящиками, кроме «безопасных» углов, чтобы игроков не
замуровало на старте.

pygame используется только в отрисовке (импорт внутри `draw`), поэтому
генерацию и запросы к сетке можно тестировать без окна.
"""

import random

from .. import config as c
from .schemes import CLASSIC


def is_border(col, row):
    """Клетка на несокрушимой рамке по краю поля."""
    return col == 0 or row == 0 or col == c.COLS - 1 or row == c.ROWS - 1


def is_border_or_pillar(col, row):
    """Несокрушимая клетка: рамка по краю или внутренний столб (чёт/чёт)."""
    if col == 0 or row == 0 or col == c.COLS - 1 or row == c.ROWS - 1:
        return True
    return col % 2 == 0 and row % 2 == 0


def spiral_order(c0, r0, c1, r1):
    """Клетки прямоугольника [c0..c1]×[r0..r1] по спирали снаружи внутрь.

    Порядок обхода — по часовой стрелке, начиная с левого-верхнего угла внешнего
    кольца. Используется для «схлопывания» арены в режиме sudden death.
    """
    cells = []
    while c0 <= c1 and r0 <= r1:
        for col in range(c0, c1 + 1):
            cells.append((col, r0))
        for row in range(r0 + 1, r1 + 1):
            cells.append((c1, row))
        if r0 < r1:
            for col in range(c1 - 1, c0 - 1, -1):
                cells.append((col, r1))
        if c0 < c1:
            for row in range(r1 - 1, r0, -1):
                cells.append((c0, row))
        c0 += 1
        r0 += 1
        c1 -= 1
        r1 -= 1
    return cells


def safe_cells():
    """Клетки, которые всегда остаются полом: углы спавна + по два соседа.

    Даёт каждому игроку «г-образный» выход из угла (сам угол и две смежные
    проходимые клетки по осям).
    """
    safe = set()
    for col, row in c.SPAWN_CELLS:
        safe.add((col, row))
        # соседи внутрь поля (к центру), они гарантированно не столбы
        dx = 1 if col < c.COLS // 2 else -1
        dy = 1 if row < c.ROWS // 2 else -1
        safe.add((col + dx, row))
        safe.add((col, row + dy))
    return safe


class Arena:
    def __init__(self, seed=None, density=None, scheme=CLASSIC):
        self.scheme = scheme
        # Явная плотность (в тестах) перекрывает плотность схемы
        self.density = scheme.density if density is None else density
        self.spawns = list(c.SPAWN_CELLS)
        self.generate(seed)

    def generate(self, seed=None, scheme=None):
        """Строит сетку. seed фиксирует раскладку; scheme задаёт узор стен.

        Узор берётся из схемы: несокрушимая стена там, где рамка или где предикат
        схемы вернул True. Безопасные углы всегда пол — узор их не замуровывает.
        """
        if scheme is not None:
            self.scheme = scheme
            self.density = scheme.density
        rng = random.Random(seed)
        safe = safe_cells()
        wall = self.scheme.wall
        self.grid = [[c.FLOOR] * c.COLS for _ in range(c.ROWS)]
        for row in range(c.ROWS):
            for col in range(c.COLS):
                if is_border(col, row):
                    self.grid[row][col] = c.WALL
                elif (col, row) in safe:
                    self.grid[row][col] = c.FLOOR
                elif wall(col, row):
                    self.grid[row][col] = c.WALL
                elif rng.random() < self.density:
                    self.grid[row][col] = c.BLOCK
                else:
                    self.grid[row][col] = c.FLOOR
        self._hide_powerups(rng)

    def _hide_powerups(self, rng):
        """Прячет бонусы под частью ящиков (взвешенный случайный тип)."""
        self.hidden = {}
        kinds = list(c.POWERUP_WEIGHTS)
        weights = [c.POWERUP_WEIGHTS[k] for k in kinds]
        for cell in self.block_cells():
            if rng.random() < c.POWERUP_DROP:
                self.hidden[cell] = rng.choices(kinds, weights=weights)[0]

    def pop_hidden(self, col, row):
        """Забирает спрятанный бонус клетки (или None). Одноразово."""
        return self.hidden.pop((col, row), None)

    # --- Запросы к сетке ---
    def in_bounds(self, col, row):
        return 0 <= col < c.COLS and 0 <= row < c.ROWS

    def tile(self, col, row):
        if not self.in_bounds(col, row):
            return c.WALL                    # за границей — как несокрушимая стена
        return self.grid[row][col]

    def is_wall(self, col, row):
        return self.tile(col, row) == c.WALL

    def is_block(self, col, row):
        return self.tile(col, row) == c.BLOCK

    def is_floor(self, col, row):
        return self.tile(col, row) == c.FLOOR

    def is_solid(self, col, row):
        """Непроходимо для движения/пламени (стена или ящик)."""
        return self.tile(col, row) in (c.WALL, c.BLOCK)

    def destroy_block(self, col, row):
        """Разрушает ящик, если он там есть. Возвращает True при разрушении."""
        if self.is_block(col, row):
            self.grid[row][col] = c.FLOOR
            return True
        return False

    def drop_wall(self, col, row):
        """Роняет несокрушимую стену на клетку (sudden death). True, если новая."""
        self.hidden.pop((col, row), None)
        if self.grid[row][col] != c.WALL:
            self.grid[row][col] = c.WALL
            return True
        return False

    def block_cells(self):
        return [(col, row) for row in range(c.ROWS) for col in range(c.COLS)
                if self.grid[row][col] == c.BLOCK]

    # --- Координаты ---
    def cell_to_px(self, col, row):
        """Левый-верхний угол клетки в пикселях."""
        return col * c.TILE, row * c.TILE

    def cell_center(self, col, row):
        return col * c.TILE + c.TILE // 2, row * c.TILE + c.TILE // 2

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen):
        import pygame

        pygame.draw.rect(screen, c.BG_COLOR, (0, 0, c.FIELD_W, c.FIELD_H))
        for row in range(c.ROWS):
            for col in range(c.COLS):
                x, y = self.cell_to_px(col, row)
                t = self.grid[row][col]
                if t == c.FLOOR:
                    self._draw_floor(pygame, screen, x, y, col, row)
                elif t == c.WALL:
                    self._draw_floor(pygame, screen, x, y, col, row)  # под фаской
                    self._draw_bevel(pygame, screen, x, y, c.WALL_COLOR,
                                     c.WALL_LIGHT, c.WALL_DARK, inset=0)
                else:  # BLOCK
                    self._draw_floor(pygame, screen, x, y, col, row)
                    self._draw_block(pygame, screen, x, y)

    def _draw_floor(self, pygame, screen, x, y, col, row):
        base = c.FLOOR_A if (col + row) % 2 == 0 else c.FLOOR_B
        pygame.draw.rect(screen, base, (x, y, c.TILE, c.TILE))
        pygame.draw.rect(screen, c.FLOOR_EDGE, (x, y, c.TILE, c.TILE), 1)

    def _draw_bevel(self, pygame, screen, x, y, base, light, dark, inset=3):
        """Плитка с объёмной фаской: светлые верх/лево, тёмные низ/право."""
        s = c.TILE
        r = pygame.Rect(x + inset, y + inset, s - inset * 2, s - inset * 2)
        pygame.draw.rect(screen, base, r)
        pygame.draw.line(screen, light, r.topleft, (r.right - 1, r.top), 2)
        pygame.draw.line(screen, light, r.topleft, (r.left, r.bottom - 1), 2)
        pygame.draw.line(screen, dark, (r.left, r.bottom - 1),
                         (r.right - 1, r.bottom - 1), 2)
        pygame.draw.line(screen, dark, (r.right - 1, r.top),
                         (r.right - 1, r.bottom - 1), 2)

    def _draw_block(self, pygame, screen, x, y):
        self._draw_bevel(pygame, screen, x, y, c.BLOCK_COLOR,
                         c.BLOCK_LIGHT, c.BLOCK_DARK, inset=3)
        # Доска-перемычка по центру — «дощатый ящик»
        s = c.TILE
        pygame.draw.line(screen, c.BLOCK_DARK,
                         (x + 5, y + s // 2), (x + s - 6, y + s // 2), 2)
