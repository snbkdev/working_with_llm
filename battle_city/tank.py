"""Танк: общий класс для игрока и врага.

Движение попиксельное. При повороте перпендикулярная координата
привязывается к сетке полос — так танк удобно проходит в проёмы.
"""

import pygame

import config as c
from bullet import Bullet


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

    def try_move(self, solids):
        """Двигает танк на шаг в текущем направлении, если путь свободен."""
        self._snap_perpendicular()
        dx = self.dir[0] * self.speed
        dy = self.dir[1] * self.speed
        new = self.rect.move(dx, dy)

        # Границы поля
        if (new.left < 0 or new.top < 0
                or new.right > c.FIELD_W or new.bottom > c.FIELD_H):
            return False
        # Стены и база
        for s in solids:
            if new.colliderect(s):
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

        if self.dir in (c.UP, c.DOWN):
            pygame.draw.rect(screen, track, (r.x, r.y, 6, r.height))
            pygame.draw.rect(screen, track, (r.right - 6, r.y, 6, r.height))
            pygame.draw.rect(
                screen, body, (r.x + 6, r.y + 4, r.width - 12, r.height - 8)
            )
        else:
            pygame.draw.rect(screen, track, (r.x, r.y, r.width, 6))
            pygame.draw.rect(screen, track, (r.x, r.bottom - 6, r.width, 6))
            pygame.draw.rect(
                screen, body, (r.x + 4, r.y + 6, r.width - 8, r.height - 12)
            )

        # Башня и ствол
        pygame.draw.rect(screen, body, r.inflate(-14, -14))
        cx, cy = r.center
        tx, ty = self.barrel_tip()
        pygame.draw.line(screen, body, (cx, cy), (tx, ty), 5)
