"""Мелкие частицы: искры, дым, обломки кирпича.

Дополняют покадровый `Explosion` живой «пылью» — процедурно, без ассетов.
Частица летит с гравитацией и гаснет по таймеру; фабрики ниже собирают
типовые «всплески».
"""

import math
import random

import pygame

from .. import config as c


class Particle:
    def __init__(self, x, y, vx, vy, life, color, size=3, gravity=0.0, shrink=True):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.start = pygame.time.get_ticks()
        self.life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.shrink = shrink
        self.alive = True

    def update(self, now):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        if now - self.start >= self.life:
            self.alive = False

    def draw(self, screen):
        frac = 1.0 - (pygame.time.get_ticks() - self.start) / self.life
        s = max(1, int(self.size * frac)) if self.shrink else self.size
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), s, s))


def spark_burst(x, y, color, count=12, speed=4.0, life=360):
    out = []
    for _ in range(count):
        a = random.uniform(0, 2 * math.pi)
        v = random.uniform(1.0, speed)
        out.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v,
                            random.randint(int(life * 0.6), life), color,
                            size=random.randint(2, 4), gravity=0.12))
    return out


def smoke_puff(x, y, count=6):
    out = []
    for _ in range(count):
        a = random.uniform(0, 2 * math.pi)
        v = random.uniform(0.3, 1.2)
        col = random.choice([c.EXPLOSION_SMOKE, (92, 92, 92), (70, 70, 70)])
        out.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v - 0.4,
                            random.randint(500, 900), col,
                            size=random.randint(3, 6), gravity=-0.02))
    return out


def brick_debris(x, y, count=8):
    out = []
    for _ in range(count):
        col = random.choice([c.BRICK_COLOR, c.BRICK_DARK])
        out.append(Particle(x, y, random.uniform(-2.5, 2.5), random.uniform(-3.5, -1.0),
                            random.randint(400, 700), col,
                            size=random.randint(2, 4), gravity=0.28, shrink=False))
    return out
