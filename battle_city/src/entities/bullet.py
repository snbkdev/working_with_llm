"""Пуля: летит по прямой в заданном направлении."""

import pygame

from .. import config as c


class Bullet:
    def __init__(self, cx, cy, direction, owner="player"):
        self.x = float(cx)
        self.y = float(cy)
        self.dir = direction
        self.owner = owner
        self.alive = True

    @property
    def rect(self):
        s = c.BULLET_SIZE
        return pygame.Rect(int(self.x - s / 2), int(self.y - s / 2), s, s)

    def update(self):
        self.x += self.dir[0] * c.BULLET_SPEED
        self.y += self.dir[1] * c.BULLET_SPEED

    def draw(self, screen):
        pygame.draw.rect(screen, c.BULLET_COLOR, self.rect)
