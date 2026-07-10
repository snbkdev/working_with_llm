"""Фрукт-бонус: появляется под домом на время, даёт очки по номеру уровня.

Логика (появление/таймаут/съедание) — чистая, тестируется headless. Иконки
рисуются процедурно функцией `draw_icon`, её же зовёт HUD для «собранных
фруктов».
"""

from .. import config as c
from ..ai import targeting as ai


class Fruit:
    def __init__(self):
        self.active = False
        self.moving = False
        self.idx = 0
        self.spawn_at = 0
        self.cx = self.cy = 0
        self.dir = c.RIGHT
        self.accum = 0.0

    def spawn(self, level, now, moving=False, entrance=None):
        self.active = True
        self.moving = moving
        self.idx = c.fruit_index(level)
        self.spawn_at = now
        self.accum = 0.0
        if moving:                            # Ms. Pac-Man: входит из тоннеля и бродит
            col, row = entrance or (1, c.TUNNEL_ROW)
            self.cx = col * c.TILE + c.TILE // 2
            self.cy = row * c.TILE + c.TILE // 2
            self.dir = c.RIGHT if col < c.COLS // 2 else c.LEFT

    # --- Позиция (для подвижного фрукта) -----------------------------------
    @property
    def col(self):
        return int(self.cx // c.TILE)

    @property
    def row(self):
        return int(self.cy // c.TILE)

    def _aligned(self):
        return ((self.cx - c.TILE // 2) % c.TILE == 0 and
                (self.cy - c.TILE // 2) % c.TILE == 0)

    def _wrap(self):
        if self.cx < 0:
            self.cx += c.FIELD_W
        elif self.cx >= c.FIELD_W:
            self.cx -= c.FIELD_W

    def update(self, now, maze=None, rng=None):
        if not self.active:
            return
        if now - self.spawn_at >= c.FRUIT_MS:
            self.active = False
            return
        if self.moving and maze is not None and rng is not None:
            self.accum += c.FRIGHT_SPEED
            if self.accum >= 1.0:
                self.accum -= 1.0
                if self._aligned():
                    self.dir = ai.frightened_dir(maze, self.col, self.row, self.dir, rng)
                self.cx += self.dir[0] * 2
                self.cy += self.dir[1] * 2
                self._wrap()

    def eat(self, pac_tile):
        """Статический фрукт: съесть, если Пакман на клетке фрукта."""
        if self.active and not self.moving and pac_tile == c.FRUIT_TILE:
            self.active = False
            return c.FRUITS[self.idx][1]
        return 0

    def eat_moving(self, pac_cx, pac_cy):
        """Подвижный фрукт: съесть при сближении с Пакманом."""
        if self.active and self.moving and \
                abs(self.cx - pac_cx) < c.TILE * 0.6 and abs(self.cy - pac_cy) < c.TILE * 0.6:
            self.active = False
            return c.FRUITS[self.idx][1]
        return 0

    def draw(self, surface, oy):
        if not self.active:
            return
        if self.moving:
            cx, cy = int(self.cx), int(self.cy) + oy
        else:
            col, row = c.FRUIT_TILE
            cx = col * c.TILE + c.TILE // 2
            cy = row * c.TILE + c.TILE // 2 + oy
        draw_icon(surface, cx, cy, self.idx, c.TILE // 2)


def draw_icon(surface, cx, cy, idx, r):
    """Нарисовать иконку фрукта `idx` радиусом ~`r` в точке (cx, cy)."""
    import pygame

    name, _pts, color = c.FRUITS[idx]
    green = (0, 200, 60)
    if name == "cherry":
        pygame.draw.circle(surface, color, (cx - r // 3, cy + r // 3), r // 2)
        pygame.draw.circle(surface, color, (cx + r // 3, cy + r // 3), r // 2)
        pygame.draw.line(surface, green, (cx - r // 3, cy + r // 3),
                         (cx + r // 4, cy - r), 2)
        pygame.draw.line(surface, green, (cx + r // 3, cy + r // 3),
                         (cx + r // 4, cy - r), 2)
    elif name == "strawberry":
        pygame.draw.polygon(surface, color, [
            (cx - r + 2, cy - r // 2), (cx + r - 2, cy - r // 2), (cx, cy + r)])
        pygame.draw.circle(surface, green, (cx, cy - r // 2), r // 2)
        for dx, dy in ((-3, 0), (3, 2), (0, 5), (-4, 6), (4, 7)):
            pygame.draw.circle(surface, (255, 240, 120), (cx + dx, cy + dy), 1)
    elif name == "galaxian":
        pygame.draw.polygon(surface, color, [
            (cx, cy - r), (cx - r, cy + r), (cx, cy + r // 3), (cx + r, cy + r)])
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)
    elif name == "bell":
        pygame.draw.rect(surface, color, (cx - r + 2, cy + r - 6, 2 * r - 4, 5),
                         border_radius=2)
        pygame.draw.polygon(surface, color, [
            (cx - r + 3, cy + r - 4), (cx, cy - r), (cx + r - 3, cy + r - 4)])
        pygame.draw.circle(surface, (60, 40, 0), (cx, cy + r - 2), 2)
    elif name == "key":
        pygame.draw.circle(surface, color, (cx, cy - r // 2), r // 2, 2)
        pygame.draw.line(surface, color, (cx, cy - r // 4), (cx, cy + r), 3)
        pygame.draw.line(surface, color, (cx, cy + r), (cx + r // 2, cy + r), 3)
    else:                                 # orange / apple / melon — круглые
        pygame.draw.circle(surface, color, (cx, cy + 1), r - 1)
        pygame.draw.line(surface, (120, 70, 20), (cx, cy - r + 2), (cx, cy - r // 2), 2)
        pygame.draw.polygon(surface, green, [
            (cx, cy - r // 2), (cx + r // 2, cy - r), (cx + r // 2, cy - r // 2)])
