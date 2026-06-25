"""Танк: общий класс для игрока и врага.

Движение попиксельное. При повороте перпендикулярная координата
привязывается к сетке полос — так танк удобно проходит в проёмы.
"""

import pygame

from .. import config as c
from .bullet import Bullet


class Tank:
    def __init__(self, col, row, direction=c.UP, is_player=True):
        self.x = float(col * c.TILE + c.TANK_OFFSET)
        self.y = float(row * c.TILE + c.TANK_OFFSET)
        self.dir = direction
        self.is_player = is_player
        self.speed = c.PLAYER_SPEED if is_player else c.ENEMY_SPEED
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), c.TANK_SIZE, c.TANK_SIZE)

    # --- Движение ---
    @staticmethod
    def _snap(value):
        """Привязка координаты к ближайшей полосе сетки."""
        return round((value - c.TANK_OFFSET) / c.TILE) * c.TILE + c.TANK_OFFSET

    def _snap_perpendicular(self):
        if self.dir in (c.LEFT, c.RIGHT):
            self.y = self._snap(self.y)
        else:
            self.x = self._snap(self.x)

    def face(self, direction):
        self.dir = direction

    def try_move(self, solids, blockers=()):
        """Двигает танк на шаг в текущем направлении, если путь свободен.

        solids   — стены и база; blockers — прямоугольники других танков.
        """
        self._snap_perpendicular()
        dx = self.dir[0] * self.speed
        dy = self.dir[1] * self.speed
        new = self.rect.move(dx, dy)

        # Границы поля
        if (new.left < 0 or new.top < 0
                or new.right > c.FIELD_W or new.bottom > c.FIELD_H):
            return False
        # Стены, база и другие танки
        for s in solids:
            if new.colliderect(s):
                return False
        for b in blockers:
            if new.colliderect(b):
                return False

        self.x += dx
        self.y += dy
        return True

    # --- Стрельба ---
    def barrel_tip(self):
        r = self.rect
        cx, cy = r.center
        return (cx + self.dir[0] * r.width / 2,
                cy + self.dir[1] * r.height / 2)

    def shoot(self, owner=None):
        tip = self.barrel_tip()
        owner = owner or ("player" if self.is_player else "enemy")
        return Bullet(tip[0], tip[1], self.dir, owner)

    # --- Отрисовка ---
    def draw(self, screen):
        r = self.rect
        body = c.PLAYER_COLOR if self.is_player else c.ENEMY_COLOR
        track = c.PLAYER_TRACK if self.is_player else c.ENEMY_TRACK
        out = c.TANK_OUTLINE
        horiz = self.dir in (c.LEFT, c.RIGHT)

        # Контур-подложка для контраста на тёмном поле
        pygame.draw.rect(screen, out, r, border_radius=5)

        if horiz:
            # Гусеницы сверху и снизу
            pygame.draw.rect(screen, track, (r.x, r.y, r.width, 7), border_radius=3)
            pygame.draw.rect(screen, track, (r.x, r.bottom - 7, r.width, 7), border_radius=3)
            for i in range(r.x + 4, r.right - 2, 6):
                pygame.draw.line(screen, out, (i, r.y + 1), (i, r.y + 5))
                pygame.draw.line(screen, out, (i, r.bottom - 6), (i, r.bottom - 2))
            hull = pygame.Rect(r.x + 3, r.y + 7, r.width - 6, r.height - 14)
        else:
            # Гусеницы слева и справа
            pygame.draw.rect(screen, track, (r.x, r.y, 7, r.height), border_radius=3)
            pygame.draw.rect(screen, track, (r.right - 7, r.y, 7, r.height), border_radius=3)
            for i in range(r.y + 4, r.bottom - 2, 6):
                pygame.draw.line(screen, out, (r.x + 1, i), (r.x + 5, i))
                pygame.draw.line(screen, out, (r.right - 6, i), (r.right - 2, i))
            hull = pygame.Rect(r.x + 7, r.y + 3, r.width - 14, r.height - 6)

        # Корпус
        pygame.draw.rect(screen, body, hull, border_radius=3)

        # Башня
        cx, cy = r.center
        pygame.draw.circle(screen, out, (cx, cy), 7)
        core = c.ENEMY_CORE if not self.is_player else body
        pygame.draw.circle(screen, core, (cx, cy), 5)

        # Ствол (выходит за корпус — видно направление)
        bx = cx + self.dir[0] * (r.width // 2 + 3)
        by = cy + self.dir[1] * (r.height // 2 + 3)
        pygame.draw.line(screen, out, (cx, cy), (bx, by), 6)
        pygame.draw.line(screen, body, (cx, cy), (bx, by), 4)
