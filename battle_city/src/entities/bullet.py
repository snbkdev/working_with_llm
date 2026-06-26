"""Пуля: летит по прямой в заданном направлении."""

import pygame

from .. import config as c


class Bullet:
    def __init__(self, cx, cy, direction, owner="player", speed=None, power=False):
        self.x = float(cx)
        self.y = float(cy)
        self.dir = direction
        self.owner = owner
        self.speed = c.BULLET_SPEED if speed is None else speed
        self.power = power          # пробивает сталь (танк максимального уровня)
        self.alive = True

    @property
    def rect(self):
        s = c.BULLET_SIZE
        return pygame.Rect(int(self.x - s / 2), int(self.y - s / 2), s, s)

    def update(self):
        self.x += self.dir[0] * self.speed
        self.y += self.dir[1] * self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, c.BULLET_COLOR, self.rect)
