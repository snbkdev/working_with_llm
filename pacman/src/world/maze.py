"""Лабиринт: парсинг ASCII-схемы, точки/энергайзеры, стены, тоннель, дом.

Карта — классический Pac-Man 28×31. Легенда символов:
    #  стена            .  точка (10)          o  энергайзер (50)
    -  воротца дома      (пробел) пустой коридор / тоннель / дом призраков

Импорт pygame нужен только в `draw`, поэтому парсинг и логика поедания
тестируются headless (без окна).
"""

from .. import config as c

# Классический лабиринт 28×31. Все строки ровно COLS символов, строк — ROWS.
LAYOUT = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.#####.##.#####.######",
    "######.#####.##.#####.######",
    "######.##..........##.######",
    "######.##.###--###.##.######",
    "######.##.#      #.##.######",
    "          #      #          ",
    "######.##.#      #.##.######",
    "######.##.########.##.######",
    "######.##..........##.######",
    "######.#####.##.#####.######",
    "######.#####.##.#####.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#o..##................##..o#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
]

# Типы тайлов
EMPTY, WALL, DOT, ENERGIZER, GATE = range(5)

_CHAR = {
    "#": WALL, ".": DOT, "o": ENERGIZER, "-": GATE, " ": EMPTY,
}


class Maze:
    """Сетка лабиринта + учёт оставшихся точек."""

    def __init__(self, layout=LAYOUT):
        if len(layout) != c.ROWS:
            raise ValueError(f"ожидалось {c.ROWS} строк, а не {len(layout)}")
        self.grid = []
        self.dots_left = 0
        for r, line in enumerate(layout):
            if len(line) != c.COLS:
                raise ValueError(f"строка {r}: {len(line)} символов вместо {c.COLS}")
            row = [_CHAR[ch] for ch in line]
            self.dots_left += sum(1 for t in row if t in (DOT, ENERGIZER))
            self.grid.append(row)

    # --- Запросы -----------------------------------------------------------
    def tile(self, col, row):
        if 0 <= row < c.ROWS and 0 <= col < c.COLS:
            return self.grid[row][col]
        return EMPTY

    def blocked(self, col, row):
        """Твёрдо ли для Пакмана? Стена/воротца — да; выход в тоннель — нет."""
        if row == c.TUNNEL_ROW and (col < 0 or col >= c.COLS):
            return False                      # боковой тоннель открыт
        if not (0 <= row < c.ROWS and 0 <= col < c.COLS):
            return True
        return self.grid[row][col] in (WALL, GATE)

    def blocked_ghost(self, col, row, gate_ok=False):
        """Твёрдо ли для призрака? Воротца проходимы только при `gate_ok`."""
        if row == c.TUNNEL_ROW and (col < 0 or col >= c.COLS):
            return False
        if not (0 <= row < c.ROWS and 0 <= col < c.COLS):
            return True
        t = self.grid[row][col]
        if t == WALL:
            return True
        if t == GATE:
            return not gate_ok
        return False

    def eat(self, col, row):
        """Съесть точку/энергайзер на клетке; вернуть начисленные очки (0 — нет)."""
        t = self.tile(col, row)
        if t == DOT:
            self.grid[row][col] = EMPTY
            self.dots_left -= 1
            return c.PTS_DOT
        if t == ENERGIZER:
            self.grid[row][col] = EMPTY
            self.dots_left -= 1
            return c.PTS_ENERGIZER
        return 0

    def cleared(self):
        return self.dots_left == 0

    # --- Отрисовка (процедурная, только здесь нужен pygame) ----------------
    def draw(self, surface, oy, blink=True):
        import pygame

        t = c.TILE
        for r in range(c.ROWS):
            for col in range(c.COLS):
                cell = self.grid[r][col]
                x, y = col * t, r * t + oy
                if cell == WALL:
                    pygame.draw.rect(surface, c.WALL, (x + 2, y + 2, t - 4, t - 4),
                                     border_radius=6)
                    pygame.draw.rect(surface, c.WALL_EDGE, (x + 2, y + 2, t - 4, t - 4),
                                     width=2, border_radius=6)
                elif cell == GATE:
                    pygame.draw.rect(surface, c.GATE, (x, y + t // 2 - 2, t, 4))
                elif cell == DOT:
                    pygame.draw.circle(surface, c.DOT, (x + t // 2, y + t // 2), 3)
                elif cell == ENERGIZER and blink:
                    pygame.draw.circle(surface, c.ENERGIZER, (x + t // 2, y + t // 2), 7)
