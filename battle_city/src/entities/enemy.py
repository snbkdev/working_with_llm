"""Вражеский танк с простым ИИ и типами, как в оригинале Tank 1990.

Типы (см. `config.ENEMY_TYPES`): basic / fast / power / armor — различаются
скоростью, бронёй (HP), скорострельностью и цветом. «Усиленный» (reinforced)
враг после 10-го уровня — крупнее и живучее.

Поведение ИИ: едет в текущем направлении, пока не упрётся; при остановке
или случайно — меняет направление; иногда стреляет.
"""

import random

from .. import config as c
from .tank import Tank

DIRECTIONS = [c.UP, c.DOWN, c.LEFT, c.RIGHT]


class Enemy(Tank):
    def __init__(self, col, row, bonus=False, kind="basic", reinforced=False):
        super().__init__(col, row, c.DOWN, is_player=False)
        self.bonus = bonus       # носитель бонуса: при уничтожении роняет power-up
        self.kind = kind
        self.reinforced = reinforced

        spec = c.ENEMY_TYPES.get(kind, c.ENEMY_TYPES["basic"])
        self.speed = spec["speed"]
        self.hp = spec["hp"]
        self.score = spec["score"]
        self.fast_bullet = spec["fast_bullet"]
        self.body_color = spec["color"]
        size = spec["size"]

        # После 10-го уровня — крупнее и минимум 2 попадания
        if reinforced:
            self.hp = max(self.hp + 1, c.REINFORCE_MIN_HP)
            size = min(size + c.REINFORCE_SIZE_BONUS, c.REINFORCE_MAX_SIZE)

        self.max_hp = self.hp
        if size != self.size:
            self.resize(size)
        if self.max_hp > 1:                 # у броневых цвет отражает остаток HP
            self.body_color = self._armor_color()

    def _armor_color(self):
        """Цвет корпуса по остатку брони: интерполяция «пробит → цел»."""
        if self.max_hp <= 1:
            return self.body_color
        t = (self.hp - 1) / (self.max_hp - 1)   # 1.0 при полной броне, 0.0 при последнем HP
        full, low = c.ARMOR_FULL_COLOR, c.ARMOR_LOW_COLOR
        return tuple(int(low[i] + (full[i] - low[i]) * t) for i in range(3))

    @property
    def armored(self):
        """Многоброневый враг (броневой тип или усиленный) — рисуем окантовку."""
        return self.max_hp > 1

    def damage(self):
        """Учитывает попадание. Возвращает True, если враг уничтожен."""
        self.hp -= 1
        if self.max_hp > 1:
            self.body_color = self._armor_color()
        return self.hp <= 0

    def shoot(self, owner=None):
        b = super().shoot(owner)
        if self.fast_bullet:                # скорострельный тип — быстрые пули
            b.speed = c.BULLET_SPEED + 3
        return b

    def update_ai(self, solids, blockers):
        """Один шаг ИИ. Возвращает Bullet, если враг выстрелил, иначе None."""
        moved = self.try_move(solids, blockers)

        # Сменить направление, если упёрлись или просто по случайности
        if not moved or random.random() < c.ENEMY_TURN_CHANCE:
            self.dir = random.choice(DIRECTIONS)

        if random.random() < c.ENEMY_SHOOT_CHANCE:
            return self.shoot()
        return None
