"""Анимация взрыва — покадровый процедурный спрайт.

Большой взрыв — при уничтожении танка, маленький — при попадании пули
в стену. Кадры заданы как набор слоёв (звезда искр или вспышка-круг),
кадр выбирается по времени с момента создания.
"""

import math
import random

import pygame

from .. import config as c

# Кадр: (длительность_мс, [слои]); слой: (цвет, радиус, доля_внутр_радиуса, лучи)
# лучи == 0 → сплошной круг-вспышка, иначе — звезда искр.
_BIG = [
    (50, [(c.EXPLOSION_FLASH, 7, 0.0, 0)]),
    (60, [(c.EXPLOSION_CORE, 15, 0.5, 8), (c.EXPLOSION_FLASH, 6, 0.0, 0)]),
    (80, [(c.EXPLOSION_MID, 26, 0.45, 8), (c.EXPLOSION_CORE, 14, 0.5, 8)]),
    (80, [(c.EXPLOSION_OUTER, 30, 0.55, 10), (c.EXPLOSION_MID, 18, 0.5, 8),
          (c.EXPLOSION_FLASH, 7, 0.0, 0)]),
    (90, [(c.EXPLOSION_SMOKE, 24, 0.5, 10), (c.EXPLOSION_OUTER, 13, 0.5, 8)]),
]
_SMALL = [
    (45, [(c.EXPLOSION_FLASH, 5, 0.0, 0)]),
    (60, [(c.EXPLOSION_CORE, 10, 0.5, 7), (c.EXPLOSION_FLASH, 4, 0.0, 0)]),
    (70, [(c.EXPLOSION_MID, 13, 0.45, 7)]),
]


def _star_points(cx, cy, outer, inner, spikes, rot):
    pts = []
    for i in range(spikes * 2):
        r = outer if i % 2 == 0 else inner
        ang = rot + math.pi * i / spikes
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


class Explosion:
    def __init__(self, cx, cy, big=True):
        self.cx = int(cx)
        self.cy = int(cy)
        self.start = pygame.time.get_ticks()
        self.frames = _BIG if big else _SMALL
        self.duration = sum(dur for dur, _ in self.frames)
        self.rot = random.uniform(0, math.pi)
        self.alive = True

    def update(self, now):
        if now - self.start >= self.duration:
            self.alive = False

    def draw(self, screen):
        elapsed = pygame.time.get_ticks() - self.start
        t = 0
        for dur, layers in self.frames:
            if elapsed < t + dur:
                for color, outer, inner_ratio, spikes in layers:
                    if spikes == 0:
                        pygame.draw.circle(screen, color, (self.cx, self.cy), outer)
                    else:
                        pts = _star_points(self.cx, self.cy, outer,
                                           outer * inner_ratio, spikes, self.rot)
                        pygame.draw.polygon(screen, color, pts)
                return
            t += dur
