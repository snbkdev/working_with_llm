"""Босс финального (20-го) уровня.

Крупный танк, патрулирующий верх поля. Держит много попаданий; по мере
пробития переходит в более агрессивные фазы (чаще и «веером» стреляет).
Не наследует Tank — своё движение (без привязки к полосам) и отрисовка.
"""

import math
import random

import pygame

from .. import config as c
from .bullet import Bullet


class Boss:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = c.BOSS_SIZE
        self.hp = c.BOSS_HP
        self.max_hp = c.BOSS_HP
        self.score = c.BOSS_SCORE
        self.move_dir = random.choice((c.LEFT, c.RIGHT))   # патруль по горизонтали
        self.last_fire = pygame.time.get_ticks()
        self.alive = True
        # Совместимость с логикой врагов (bonus/kind не используются, но пусть будут)
        self.bonus = False
        self.kind = "boss"

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    def phase(self):
        """0 — >66% HP, 1 — 33–66%, 2 — <33%. Чем ниже HP, тем злее."""
        frac = self.hp / self.max_hp
        if frac > 0.66:
            return 0
        if frac > 0.33:
            return 1
        return 2

    def damage(self):
        """Попадание. Возвращает True, если босс уничтожен."""
        self.hp -= 1
        return self.hp <= 0

    # --- Поведение ---
    def update(self, now, solids, player_rect):
        """Шаг патруля + возможный залп. Возвращает список выпущенных пуль."""
        speed = c.BOSS_SPEED + self.phase()          # к финалу — быстрее
        nx = self.x + self.move_dir[0] * speed
        new = pygame.Rect(int(nx), int(self.y), self.size, self.size)
        blocked = (new.left < 0 or new.right > c.FIELD_W
                   or any(new.colliderect(s) for s in solids))
        if blocked:
            self.move_dir = (-self.move_dir[0], 0)   # разворот
        else:
            self.x = nx

        bullets = []
        interval = c.BOSS_FIRE_INTERVAL[self.phase()]
        if now - self.last_fire >= interval:
            self.last_fire = now
            bullets = self._fire()
        return bullets

    def _fire(self):
        """Залп из нижней кромки: веер расширяется с фазой."""
        cx = self.rect.centerx
        by = self.rect.bottom
        # Направления «веера» вниз по фазам
        fans = [
            [c.DOWN],
            [(-0.5, 1), c.DOWN, (0.5, 1)],
            [(-1, 1), (-0.4, 1), c.DOWN, (0.4, 1), (1, 1)],
        ]
        out = []
        for dx, dy in fans[self.phase()]:
            mag = math.hypot(dx, dy)
            d = (dx / mag, dy / mag)                  # нормируем диагонали
            out.append(Bullet(cx, by, d, owner="enemy",
                              speed=c.BULLET_SPEED + 1))
        return out

    # --- Отрисовка ---
    def draw(self, screen):
        r = self.rect
        out = c.TANK_OUTLINE
        pygame.draw.rect(screen, out, r, border_radius=8)
        # Гусеницы слева/справа
        pygame.draw.rect(screen, c.BOSS_TRACK, (r.x, r.y, 10, r.height), border_radius=4)
        pygame.draw.rect(screen, c.BOSS_TRACK,
                         (r.right - 10, r.y, 10, r.height), border_radius=4)
        for i in range(r.y + 5, r.bottom - 3, 8):
            pygame.draw.line(screen, out, (r.x + 1, i), (r.x + 8, i), 2)
            pygame.draw.line(screen, out, (r.right - 8, i), (r.right - 1, i), 2)
        # Корпус
        body = r.inflate(-22, -14)
        pygame.draw.rect(screen, c.BOSS_COLOR, body, border_radius=6)
        pygame.draw.rect(screen, c.BOSS_DARK, body, 3, border_radius=6)
        # Заклёпки по углам корпуса
        for bx, by in ((body.x + 6, body.y + 6), (body.right - 6, body.y + 6),
                       (body.x + 6, body.bottom - 6), (body.right - 6, body.bottom - 6)):
            pygame.draw.circle(screen, c.BOSS_DARK, (bx, by), 3)
        # Башня и горящий «глаз»
        pygame.draw.circle(screen, c.BOSS_DARK, r.center, 16)
        eye_r = 8 + (pygame.time.get_ticks() // 200) % 3
        pygame.draw.circle(screen, c.BOSS_EYE, r.center, eye_r)
        # Ствол вниз
        pygame.draw.rect(screen, c.BOSS_DARK, (r.centerx - 4, r.centery, 8, r.height // 2 + 6))
        self._draw_hp(screen, r)

    def _draw_hp(self, screen, r):
        bw, bh = r.width, 5
        bx, by = r.x, r.y - 10
        pygame.draw.rect(screen, c.BOSS_HP_BACK, (bx, by, bw, bh), border_radius=2)
        frac = max(0.0, self.hp / self.max_hp)
        pygame.draw.rect(screen, c.BOSS_HP_FILL, (bx, by, int(bw * frac), bh), border_radius=2)
