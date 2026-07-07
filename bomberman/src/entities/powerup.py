"""Бонусы и проклятия, выпадающие из-под разрушенных ящиков.

Бонус лежит на клетке, подбирается наездом (совпадение клетки с игроком).
Тип определяет эффект (см. `Player.apply_powerup`). Череп `POW_SKULL` — это
проклятие: наводит случайную временную болезнь. Логика (клетка/подбор) —
без pygame; отрисовка иконки — процедурная, только в `draw`.
"""

import math

from .. import config as c


class PowerUp:
    def __init__(self, col, row, kind, now=0):
        self.col = col
        self.row = row
        self.kind = kind
        self.born = now
        self.taken = False

    @property
    def cell(self):
        return self.col, self.row

    def center(self):
        return self.col * c.TILE + c.TILE // 2, self.row * c.TILE + c.TILE // 2

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen, now):
        cx, cy = self.center()
        cy += int(2 * math.sin(now * 0.005))         # лёгкое парение
        render_badge(screen, self.kind, cx, cy, c.TILE // 2 - 6)


def render_badge(screen, kind, cx, cy, r):
    """Значок бонуса: капсула с фаской + пиктограмма. Годится и для HUD."""
    import pygame

    col = c.POW_COLORS[kind]
    dark = tuple(int(v * 0.5) for v in col)
    light = tuple(min(255, int(v * 1.25)) for v in col)
    rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    pygame.draw.rect(screen, dark, rect.inflate(4, 4), border_radius=8)
    pygame.draw.rect(screen, col, rect, border_radius=7)
    pygame.draw.rect(screen, light, rect, 2, border_radius=7)
    _icon(pygame, screen, kind, cx, cy, r)


def _icon(pygame, screen, kind, cx, cy, r):
    """Пиктограмма поверх капсулы — своя для каждого типа."""
    w = (245, 245, 250)
    dark = (30, 30, 38)
    k = kind
    if k == c.POW_BOMB:
        pygame.draw.circle(screen, dark, (cx, cy + 2), r - 3)
        pygame.draw.line(screen, w, (cx, cy - r + 2), (cx + 3, cy - r - 1), 2)
    elif k in (c.POW_FIRE, c.POW_FULLFIRE):
        pts = [(cx, cy - r + 1), (cx + r - 3, cy + r - 3),
               (cx, cy + r - 5), (cx - r + 3, cy + r - 3)]
        pygame.draw.polygon(screen, w, pts)
        pygame.draw.circle(screen, (250, 210, 90), (cx, cy + 2), max(2, r // 3))
        if k == c.POW_FULLFIRE:                  # «максимум» — плюсик
            pygame.draw.line(screen, dark, (cx - 3, cy + 2), (cx + 3, cy + 2), 2)
            pygame.draw.line(screen, dark, (cx, cy - 1), (cx, cy + 5), 2)
    elif k == c.POW_SPEED:
        for off in (-4, 1):                      # двойная стрелка-«шеврон»
            pygame.draw.lines(screen, w, False,
                              [(cx + off - 2, cy - 5), (cx + off + 4, cy),
                               (cx + off - 2, cy + 5)], 2)
    elif k == c.POW_KICK:
        pygame.draw.circle(screen, w, (cx + 3, cy), r - 5, 2)   # мяч-бомба
        pygame.draw.lines(screen, w, False,
                          [(cx - r + 2, cy + 4), (cx - 2, cy), (cx - 5, cy - 4)], 2)
    elif k == c.POW_DETON:
        pygame.draw.rect(screen, w, (cx - 5, cy - 1, 10, 7), border_radius=1)
        pygame.draw.line(screen, w, (cx, cy - 1), (cx, cy - 6), 2)
        pygame.draw.circle(screen, (250, 90, 70), (cx, cy - 7), 2)
    elif k == c.POW_SKULL:
        pygame.draw.circle(screen, w, (cx, cy - 1), r - 4)
        pygame.draw.rect(screen, w, (cx - 3, cy + r - 8, 6, 5))
        pygame.draw.circle(screen, dark, (cx - 3, cy - 2), 2)
        pygame.draw.circle(screen, dark, (cx + 3, cy - 2), 2)
        pygame.draw.line(screen, dark, (cx - 2, cy + 3), (cx + 2, cy + 3), 1)


def pickup(powerups, cell):
    """Возвращает подобранный бонус на клетке (помечает `taken`) или None."""
    for p in powerups:
        if not p.taken and p.cell == cell:
            p.taken = True
            return p
    return None
