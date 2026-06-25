"""Уровень: карта поля, стены, база (орёл).

Карта задаётся текстом, один символ — одна клетка:
    '.' — пусто
    'B' — кирпич (разрушается пулями)
    'S' — сталь (пули не пробивают)
    'A' — база/орёл (защищаем; разрушение = поражение)
    'P' — точка появления игрока
    'E' — точка появления врага
"""

import pygame

import config as c

LEVEL = [
    "E.....E.....E",
    ".............",
    ".BB.BBBBB.BB.",
    ".B...B.B...B.",
    ".B.B.....B.B.",
    "...B.SSS.B...",
    ".BB.S...S.BB.",
    "...B.SSS.B...",
    ".B.B.....B.B.",
    ".B...B.B...B.",
    ".BB.BBBBB.BB.",
    ".....BBB.....",
    "...P.BAB.....",
]


def tile_rect(col, row):
    return pygame.Rect(col * c.TILE, row * c.TILE, c.TILE, c.TILE)


class Level:
    def __init__(self):
        self.bricks = set()       # клетки-кирпичи {(col, row)}
        self.steels = set()       # клетки-сталь
        self.enemy_spawns = []     # [(col, row), ...]
        self.player_spawn = (6, 12)
        self.base_cell = (6, 12)
        self.base_alive = True

        for row, line in enumerate(LEVEL):
            for col, ch in enumerate(line):
                if ch == "B":
                    self.bricks.add((col, row))
                elif ch == "S":
                    self.steels.add((col, row))
                elif ch == "E":
                    self.enemy_spawns.append((col, row))
                elif ch == "P":
                    self.player_spawn = (col, row)
                elif ch == "A":
                    self.base_cell = (col, row)

    # --- Препятствия ---
    def solid_rects(self):
        """Прямоугольники, сквозь которые нельзя проехать."""
        rects = [tile_rect(col, row) for col, row in self.bricks]
        rects += [tile_rect(col, row) for col, row in self.steels]
        if self.base_alive:
            rects.append(self.base_rect())
        return rects

    def base_rect(self):
        return tile_rect(*self.base_cell)

    def cell_at(self, px, py):
        return (px // c.TILE, py // c.TILE)

    def hit(self, rect):
        """Реакция на попадание пули в прямоугольник rect.

        Возвращает: 'brick' (кирпич разрушен), 'steel' (сталь, пуля гаснет),
        'base' (база разрушена) или None (попадания нет).
        """
        # База
        if self.base_alive and rect.colliderect(self.base_rect()):
            self.base_alive = False
            return "base"
        # Сталь
        for cell in list(self.steels):
            if rect.colliderect(tile_rect(*cell)):
                return "steel"
        # Кирпич
        for cell in list(self.bricks):
            if rect.colliderect(tile_rect(*cell)):
                self.bricks.discard(cell)
                return "brick"
        return None

    # --- Отрисовка ---
    def draw(self, screen):
        for col, row in self.bricks:
            self._draw_brick(screen, col, row)
        for col, row in self.steels:
            self._draw_steel(screen, col, row)
        if self.base_alive:
            self._draw_base(screen)

    def _draw_brick(self, screen, col, row):
        r = tile_rect(col, row)
        pygame.draw.rect(screen, c.BRICK_DARK, r)
        # Кирпичная кладка: четыре блока
        h = c.TILE // 2
        for i in (0, 1):
            for j in (0, 1):
                bx = r.x + j * h + 1 + (2 if i else 0)
                by = r.y + i * h + 1
                pygame.draw.rect(
                    screen, c.BRICK_COLOR, (bx, by, h - 3, h - 2)
                )

    def _draw_steel(self, screen, col, row):
        r = tile_rect(col, row)
        pygame.draw.rect(screen, c.STEEL_DARK, r)
        pygame.draw.rect(screen, c.STEEL_COLOR, r.inflate(-6, -6))
        pygame.draw.rect(screen, c.STEEL_DARK, r.inflate(-6, -6), 2)

    def _draw_base(self, screen):
        r = self.base_rect()
        pygame.draw.rect(screen, c.BASE_DARK, r)
        # Простой «орёл»: основание + тело
        cx = r.centerx
        pygame.draw.rect(screen, c.BASE_COLOR, (r.x + 8, r.y + 22, r.width - 16, 12))
        pygame.draw.polygon(screen, c.BASE_COLOR, [
            (cx, r.y + 6), (r.x + 10, r.y + 24), (r.right - 10, r.y + 24),
        ])
