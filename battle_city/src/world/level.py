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

from .. import config as c

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
        pygame.draw.rect(screen, c.BRICK_DARK, r)  # «раствор» — фон
        bh = (c.TILE - 2) // 4                       # 4 ряда кладки
        bw = c.TILE // 2                             # ширина кирпича
        for i in range(4):
            y = r.y + 1 + i * bh
            shift = 0 if i % 2 == 0 else c.TILE // 4  # смещение через ряд
            x = r.x + 1 - shift
            while x < r.right - 1:
                bx0 = max(r.x + 1, x)
                bx1 = min(r.right - 1, x + bw - 1)
                if bx1 - bx0 > 1:
                    pygame.draw.rect(
                        screen, c.BRICK_COLOR, (bx0, y, bx1 - bx0, bh - 1)
                    )
                x += bw

    def _draw_steel(self, screen, col, row):
        r = tile_rect(col, row)
        pygame.draw.rect(screen, c.STEEL_DARK, r)
        plate = r.inflate(-4, -4)
        pygame.draw.rect(screen, c.STEEL_COLOR, plate)
        pygame.draw.rect(screen, c.STEEL_DARK, plate, 2)
        # Заклёпки по углам
        for bx, by in (
            (plate.x + 4, plate.y + 4), (plate.right - 4, plate.y + 4),
            (plate.x + 4, plate.bottom - 4), (plate.right - 4, plate.bottom - 4),
        ):
            pygame.draw.circle(screen, c.STEEL_DARK, (bx, by), 2)

    def _draw_base(self, screen):
        r = self.base_rect()
        cx = r.centerx
        pygame.draw.rect(screen, (40, 40, 40), r)
        # Подставка
        pygame.draw.rect(
            screen, c.BASE_GROUND, (r.x + 4, r.bottom - 9, r.width - 8, 7)
        )
        # Крылья
        pygame.draw.polygon(screen, c.BASE_DARK, [
            (cx - 11, r.y + 16), (cx - 18, r.y + 27), (cx - 10, r.bottom - 11)])
        pygame.draw.polygon(screen, c.BASE_DARK, [
            (cx + 11, r.y + 16), (cx + 18, r.y + 27), (cx + 10, r.bottom - 11)])
        # Тело орла
        pygame.draw.polygon(screen, c.BASE_COLOR, [
            (cx, r.y + 8), (cx - 10, r.y + 19),
            (cx - 9, r.bottom - 11), (cx + 9, r.bottom - 11),
            (cx + 10, r.y + 19)])
        # Голова
        pygame.draw.circle(screen, c.BASE_COLOR, (cx, r.y + 9), 4)
