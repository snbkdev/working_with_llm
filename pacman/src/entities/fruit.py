"""Фрукт-бонус: появляется под домом на время, даёт очки по номеру уровня.

Логика (появление/таймаут/съедание) — чистая, тестируется headless. Иконки
рисуются процедурно функцией `draw_icon`, её же зовёт HUD для «собранных
фруктов».
"""

from .. import config as c


class Fruit:
    def __init__(self):
        self.active = False
        self.idx = 0
        self.spawn_at = 0

    def spawn(self, level, now):
        self.active = True
        self.idx = c.fruit_index(level)
        self.spawn_at = now

    def update(self, now):
        if self.active and now - self.spawn_at >= c.FRUIT_MS:
            self.active = False

    def eat(self, pac_tile):
        """Съесть, если Пакман на клетке фрукта. Вернуть очки (0 — нет)."""
        if self.active and pac_tile == c.FRUIT_TILE:
            self.active = False
            return c.FRUITS[self.idx][1]
        return 0

    def draw(self, surface, oy):
        if not self.active:
            return
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
