"""Вражеский танк с простым ИИ.

Поведение: едет в текущем направлении, пока не упрётся; при остановке
или случайно — меняет направление; иногда стреляет.
"""

import random

from .. import config as c
from .tank import Tank

DIRECTIONS = [c.UP, c.DOWN, c.LEFT, c.RIGHT]


class Enemy(Tank):
    def __init__(self, col, row, bonus=False):
        super().__init__(col, row, c.DOWN, is_player=False)
        self.bonus = bonus       # носитель бонуса: при уничтожении роняет power-up

    def update_ai(self, solids, blockers):
        """Один шаг ИИ. Возвращает Bullet, если враг выстрелил, иначе None."""
        moved = self.try_move(solids, blockers)

        # Сменить направление, если упёрлись или просто по случайности
        if not moved or random.random() < c.ENEMY_TURN_CHANCE:
            self.dir = random.choice(DIRECTIONS)

        if random.random() < c.ENEMY_SHOOT_CHANCE:
            return self.shoot()
        return None
