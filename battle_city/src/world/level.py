"""Уровень: карта поля, стены, база (орёл).

Карта задаётся текстом, один символ — одна клетка:
    '.' — пусто
    'B' — кирпич (разрушается пулями)
    'S' — сталь (пули не пробивают)
    'W' — вода (танк не проедет, пули летят над ней)
    'F' — лес (все проходят, но танк скрыт под листвой)
    'I' — лёд (скольжение при движении)
    'A' — база/орёл (защищаем; разрушение = поражение)
    'P' — точка появления игрока
    'E' — точка появления врага

Сами карты хранятся в `battle_city/levels/*.txt` и грузятся через
`world.levels` (см. `Level(rows=...)`).
"""

import pygame

from .. import config as c
from . import levels


def tile_rect(col, row):
    return pygame.Rect(col * c.TILE, row * c.TILE, c.TILE, c.TILE)


class Level:
    def __init__(self, rows=None):
        """rows — карта (список строк). Если None, грузится первый уровень."""
        if rows is None:
            rows = levels.load_level(0)
        self.bricks = set()       # клетки-кирпичи {(col, row)}
        self.steels = set()       # клетки-сталь
        self.water = set()        # клетки-вода (блокируют танки, не пули)
        self.forest = set()       # клетки-лес (рисуются поверх танков)
        self.ice = set()          # клетки-лёд (скольжение)
        self.enemy_spawns = []     # [(col, row), ...]
        self.player_spawn = (6, 12)
        self.base_cell = (6, 12)
        self.base_alive = True

        for row, line in enumerate(rows):
            for col, ch in enumerate(line):
                if ch == "B":
                    self.bricks.add((col, row))
                elif ch == "S":
                    self.steels.add((col, row))
                elif ch == "W":
                    self.water.add((col, row))
                elif ch == "F":
                    self.forest.add((col, row))
                elif ch == "I":
                    self.ice.add((col, row))
                elif ch == "E":
                    self.enemy_spawns.append((col, row))
                elif ch == "P":
                    self.player_spawn = (col, row)
                elif ch == "A":
                    self.base_cell = (col, row)

        # Клетки защитной рамки вокруг базы (для бонуса «лопата»)
        bc, br = self.base_cell
        self.base_wall = [
            (bc + dx, br + dy)
            for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            if (dx, dy) != (0, 0)
            and 0 <= bc + dx < c.COLS and 0 <= br + dy < c.ROWS
        ]

    # --- Препятствия ---
    def solid_rects(self):
        """Прямоугольники, сквозь которые нельзя проехать (стены, вода, база)."""
        rects = [tile_rect(col, row) for col, row in self.bricks]
        rects += [tile_rect(col, row) for col, row in self.steels]
        rects += [tile_rect(col, row) for col, row in self.water]
        if self.base_alive:
            rects.append(self.base_rect())
        return rects

    def base_rect(self):
        return tile_rect(*self.base_cell)

    def cell_at(self, px, py):
        return (px // c.TILE, py // c.TILE)

    def is_ice(self, pos):
        """Стоит ли танк (по его центру) на клетке льда."""
        return self.cell_at(pos[0], pos[1]) in self.ice

    def set_base_walls(self, material):
        """Материал защитной рамки базы: 'steel' (лопата) или 'brick' (возврат).

        Заполняет все клетки рамки целиком — даже разрушенные, так что лопата
        ещё и восстанавливает пробитую стену.
        """
        for cell in self.base_wall:
            self.bricks.discard(cell)
            self.steels.discard(cell)
            (self.steels if material == "steel" else self.bricks).add(cell)

    def hit(self, rect, pierce_steel=False):
        """Реакция на попадание пули в прямоугольник rect.

        pierce_steel — пуля прокачанного танка разрушает сталь.
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
                if pierce_steel:
                    self.steels.discard(cell)
                return "steel"
        # Кирпич
        for cell in list(self.bricks):
            if rect.colliderect(tile_rect(*cell)):
                self.bricks.discard(cell)
                return "brick"
        return None

    # --- Отрисовка ---
    def draw(self, screen):
        """Земля и препятствия (под танками). Лес рисуется отдельно — draw_forest."""
        now = pygame.time.get_ticks()
        for col, row in self.ice:
            self._draw_ice(screen, col, row)
        for col, row in self.water:
            self._draw_water(screen, col, row, now)
        for col, row in self.bricks:
            self._draw_brick(screen, col, row)
        for col, row in self.steels:
            self._draw_steel(screen, col, row)
        if self.base_alive:
            self._draw_base(screen)

    def draw_forest(self, screen):
        """Листва — поверх танков и пуль (скрывает то, что под ней)."""
        for col, row in self.forest:
            self._draw_forest(screen, col, row)

    def _draw_water(self, screen, col, row, now):
        r = tile_rect(col, row)
        pygame.draw.rect(screen, c.WATER_COLOR, r)
        # Две бегущие волны — сдвиг фазы во времени
        for i in range(2):
            y = r.y + 10 + i * 16
            phase = (now // 220 + i) % 2
            x0 = r.x + (6 if phase else 2)
            pygame.draw.line(screen, c.WATER_DARK, (r.x + 2, y), (r.right - 2, y), 2)
            pygame.draw.line(screen, c.WATER_FOAM, (x0, y - 3),
                             (min(x0 + 12, r.right - 3), y - 3), 2)

    def _draw_ice(self, screen, col, row):
        r = tile_rect(col, row)
        pygame.draw.rect(screen, c.ICE_COLOR, r)
        pygame.draw.rect(screen, c.ICE_EDGE, r, 1)
        # Блики-трещинки
        pygame.draw.line(screen, c.ICE_SHINE, (r.x + 6, r.y + 8), (r.x + 16, r.y + 5), 2)
        pygame.draw.line(screen, c.ICE_SHINE,
                         (r.right - 8, r.bottom - 7), (r.right - 20, r.bottom - 10), 2)

    def _draw_forest(self, screen, col, row):
        r = tile_rect(col, row)
        pygame.draw.rect(screen, c.FOREST_DARK, r)
        # Кусты — кружки-кроны в шахматном порядке
        for i, (dx, dy) in enumerate(((10, 10), (28, 12), (18, 26), (32, 30), (6, 30))):
            col2 = c.FOREST_LIGHT if i % 2 else c.FOREST_COLOR
            pygame.draw.circle(screen, col2, (r.x + dx, r.y + dy), 7)

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
