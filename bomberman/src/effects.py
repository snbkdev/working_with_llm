"""Сочность: частицы, тряска экрана и вспышка при взрывах и гибели.

Всё живёт в одном менеджере `Effects`, который держит список частиц и текущее
состояние тряски/вспышки. Логика (порождение, интегрирование, затухание) —
чистый Python на инъектируемом `now` (мс), поэтому тестируется headless; pygame
нужен только в методах отрисовки. Кадровый шаг восстанавливаем из разницы `now`
между вызовами `update`, ограничивая скачок, чтобы физика не «телепортировала»
частицы после лага.
"""

import math
import random

from . import config as c


class Particle:
    """Летящая искра/обломок: позиция в px, скорость в px/мс, гравитация."""

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "grav")

    def __init__(self, x, y, vx, vy, life, color, size, grav):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.grav = grav

    def advance(self, dt):
        """Шаг физики за dt мс. Возвращает False, когда частица отжила."""
        self.vy += self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0


class Effects:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.particles = []
        self.shake = 0.0            # текущая амплитуда тряски (px)
        self.flashes = []          # локальные вспышки [x, y, born, fire]
        self._last = None          # прошлый now для расчёта dt

    def reset(self):
        """Сброс на новый раунд — ни частиц, ни тряски, ни вспышек."""
        self.particles.clear()
        self.shake = 0.0
        self.flashes.clear()
        self._last = None

    # --- Триггеры ---
    def explosion(self, cx, cy, now, fire=1):
        """Взрыв в точке: искры наружу + подкрутка тряски и вспышки."""
        n = c.EMBERS_MIN + c.EMBERS_FIRE * fire
        for _ in range(n):
            ang = self.rng.uniform(0, math.tau)
            spd = self.rng.uniform(0.05, 0.05 + 0.03 * fire)
            self.particles.append(Particle(
                cx, cy, math.cos(ang) * spd, math.sin(ang) * spd,
                life=self.rng.uniform(260, 520),
                color=self.rng.choice(c.EMBER_COLORS),
                size=self.rng.randint(2, 4), grav=0.00035))
        self.shake = min(c.SHAKE_MAX, self.shake + c.SHAKE_ADD + c.SHAKE_FIRE * fire)
        self.flashes.append([cx, cy, now, fire])   # локальное свечение у взрыва

    def death(self, cx, cy, now, color):
        """Гибель бойца: облачко обломков в его цвете + серые «косточки»."""
        for _ in range(c.DEBRIS_COUNT):
            ang = self.rng.uniform(-math.pi, 0)          # преимущественно вверх
            spd = self.rng.uniform(0.03, 0.12)
            tone = color if self.rng.random() < 0.6 else c.DEAD_COLOR
            self.particles.append(Particle(
                cx, cy, math.cos(ang) * spd, math.sin(ang) * spd - 0.04,
                life=self.rng.uniform(360, 680),
                color=tone, size=self.rng.randint(2, 4), grav=0.0008))
        self.shake = min(c.SHAKE_MAX, self.shake + c.SHAKE_ADD * 0.6)

    # --- Обновление ---
    def update(self, now):
        """Двигает частицы и гасит тряску/вспышку по прошедшему времени."""
        if self._last is None:
            self._last = now
        dt = now - self._last
        self._last = now
        if dt <= 0:
            return
        dt = min(dt, 50)                                  # защита от скачка после лага
        self.particles = [p for p in self.particles if p.advance(dt)]
        self.shake *= c.SHAKE_DECAY ** (dt / 16.6)
        if self.shake < 0.4:
            self.shake = 0.0
        self.flashes = [f for f in self.flashes if now - f[2] < c.FLASH_MS]

    def shake_offset(self):
        """Случайное смещение поля на текущей амплитуде тряски (dx, dy)."""
        if self.shake <= 0:
            return 0, 0
        return (self.rng.uniform(-self.shake, self.shake),
                self.rng.uniform(-self.shake, self.shake))

    # --- Отрисовка (pygame только здесь) ---
    def draw_particles(self, surf, now):
        import pygame

        for p in self.particles:
            k = max(0.0, p.life / p.max_life)
            a = int(255 * min(1.0, k * 1.4))             # тускнеют к концу
            r = max(1, int(p.size * (0.4 + 0.6 * k)))
            dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*p.color, a), (r, r), r)
            surf.blit(dot, (int(p.x) - r, int(p.y) - r))

    def draw_flash(self, surf, now):
        """Короткое тёплое свечение вокруг каждого взрыва (локально, не на весь экран)."""
        import pygame

        for x, y, born, fire in self.flashes:
            age = now - born
            if age >= c.FLASH_MS:
                continue
            k = 1.0 - age / c.FLASH_MS                    # 1 → 0 за жизнь вспышки
            radius = int(min(fire + 1.0, c.FLASH_TILES) * c.TILE)
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            steps = 5                                     # мягкий радиальный спад к краям
            for s in range(steps, 0, -1):
                rr = int(radius * s / steps)
                a = int(c.FLASH_ALPHA * k * (1.0 - (s - 1) / steps))
                pygame.draw.circle(glow, (*c.FLASH_COLOR, a), (radius, radius), rr)
            surf.blit(glow, (x - radius, y - radius))
