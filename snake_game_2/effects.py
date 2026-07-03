"""Визуальные эффекты: частицы и всплывающий текст."""

import math
import random

import pygame


class Particle:
    """Разлетающаяся искра: гаснет и уменьшается со временем."""

    def __init__(self, x, y, color):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(60, 230)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 40
        self.life = self.max_life = random.uniform(0.35, 0.75)
        self.size = random.uniform(2.0, 4.5)
        self.color = color

    def update(self, dt):
        """Сдвигает частицу; возвращает False, когда она погасла."""
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 320 * dt  # лёгкая гравитация
        return self.life > 0

    def draw(self, surf):
        k = max(0.0, self.life / self.max_life)
        r = max(1, int(self.size * k))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)


class FloatingText:
    """Всплывающая надпись («+1»), уплывает вверх и растворяется."""

    def __init__(self, x, y, text, color, font):
        self.image = font.render(text, True, color)
        self.x = x - self.image.get_width() / 2
        self.y = y - 18
        self.life = self.max_life = 0.9

    def update(self, dt):
        self.life -= dt
        self.y -= 45 * dt
        return self.life > 0

    def draw(self, surf):
        self.image.set_alpha(int(255 * max(0.0, self.life / self.max_life)))
        surf.blit(self.image, (self.x, self.y))
