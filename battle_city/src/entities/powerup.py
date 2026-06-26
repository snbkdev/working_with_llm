"""Бонус (power-up): лежит на клетке поля, мигает, подбирается наездом.

Виды: 'star' (апгрейд танка), 'helmet' (щит-неуязвимость),
'grenade' (уничтожить всех врагов), 'shovel' (укрепить базу).
Иконки рисуются процедурно, как и вся графика игры.
"""

import math

import pygame

from .. import config as c


def _star_points(cx, cy, outer, inner, spikes=5, rot=-math.pi / 2):
    pts = []
    for i in range(spikes * 2):
        r = outer if i % 2 == 0 else inner
        ang = rot + math.pi * i / spikes
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


class PowerUp:
    def __init__(self, col, row, kind):
        self.col = col
        self.row = row
        self.kind = kind
        self.spawned = pygame.time.get_ticks()
        self.alive = True

    @property
    def rect(self):
        r = pygame.Rect(0, 0, c.TILE - 8, c.TILE - 8)
        r.center = (self.col * c.TILE + c.TILE // 2,
                    self.row * c.TILE + c.TILE // 2)
        return r

    def update(self, now):
        if now - self.spawned >= c.POWERUP_LIFETIME:
            self.alive = False

    # --- Отрисовка ---
    def draw(self, screen):
        now = pygame.time.get_ticks()
        # Под конец жизни мигаем быстрее — сигнал, что бонус вот-вот исчезнет
        left = c.POWERUP_LIFETIME - (now - self.spawned)
        period = c.POWERUP_BLINK_MS // 2 if left < 3000 else c.POWERUP_BLINK_MS
        if (now // period) % 2:
            return

        r = self.rect
        pygame.draw.rect(screen, c.POWERUP_BG, r, border_radius=4)
        pygame.draw.rect(screen, c.POWERUP_FRAME, r, 2, border_radius=4)
        getattr(self, f"_icon_{self.kind}")(screen, r)

    def _icon_star(self, screen, r):
        pts = _star_points(r.centerx, r.centery, r.width * 0.36, r.width * 0.15)
        pygame.draw.polygon(screen, c.STAR_COLOR, pts)

    def _icon_helmet(self, screen, r):
        cx, cy = r.center
        dome = pygame.Rect(0, 0, r.width * 0.6, r.width * 0.6)
        dome.center = (cx, cy + 1)
        pygame.draw.arc(screen, c.HELMET_COLOR, dome, 0, math.pi, 4)
        pygame.draw.line(screen, c.HELMET_COLOR,
                         (dome.left, cy + 1), (dome.right, cy + 1), 4)

    def _icon_grenade(self, screen, r):
        cx, cy = r.center
        body = int(r.width * 0.26)
        pygame.draw.circle(screen, c.GRENADE_COLOR, (cx, cy + 2), body)
        pygame.draw.circle(screen, c.POWERUP_FRAME, (cx, cy + 2), body, 1)
        # Колпачок и запал
        pygame.draw.rect(screen, c.GRENADE_COLOR,
                         (cx - 3, cy - body - 1, 6, 4))
        pygame.draw.line(screen, c.STAR_COLOR,
                         (cx + 2, cy - body - 1), (cx + 6, cy - body - 5), 2)

    def _icon_shovel(self, screen, r):
        cx, cy = r.center
        # Черенок
        pygame.draw.line(screen, c.SHOVEL_COLOR, (cx, cy - 6), (cx, cy + 2), 3)
        # Штык
        pygame.draw.polygon(screen, c.SHOVEL_COLOR, [
            (cx - 5, cy + 1), (cx + 5, cy + 1),
            (cx + 3, cy + 7), (cx - 3, cy + 7)])
