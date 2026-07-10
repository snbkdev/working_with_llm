"""Пакман: движение по сетке с буфером поворота, тоннель, поедание точек.

Позиция хранится в пикселях (центр спрайта) в координатах поля. Движение
попиксельное с привязкой к сетке: скорость делит `TILE`, а решения о повороте
и поедании принимаются только в **центре клетки** — так сетка не «плывёт».
Импорт pygame нужен только для `draw`, поэтому логика тестируется headless.
"""

import math

from .. import config as c


class Pacman:
    def __init__(self, col, row):
        self.cx = col * c.TILE + c.TILE // 2      # центр спрайта, пиксели поля
        self.cy = row * c.TILE + c.TILE // 2
        self.dir = c.NONE                         # текущее направление
        self.want_dir = None                      # буфер: последнее нажатие
        self.moving = False
        self.anim = 0                             # фаза анимации рта
        self.accum = 0.0                          # аккумулятор дробной скорости

    # --- Состояние ---------------------------------------------------------
    @property
    def col(self):
        return int(self.cx // c.TILE)

    @property
    def row(self):
        return int(self.cy // c.TILE)

    def tile(self):
        return (self.col, self.row)

    def _aligned(self):
        """Стоим ли ровно в центре клетки (можно поворачивать/есть)."""
        return ((self.cx - c.TILE // 2) % c.TILE == 0 and
                (self.cy - c.TILE // 2) % c.TILE == 0)

    def reset(self, col, row):
        self.cx = col * c.TILE + c.TILE // 2
        self.cy = row * c.TILE + c.TILE // 2
        self.dir = c.NONE
        self.want_dir = None
        self.moving = False
        self.accum = 0.0

    # --- Обновление --------------------------------------------------------
    def update(self, maze, speed=1.0):
        """Шаг на кадр (доля `speed` кадров делает ход 2 px, чтобы был запас
        на ускорение по уровням). Возвращает очки за поедание (0 — нет)."""
        gained = 0

        # Разворот на 180° разрешён в любой точке — сразу отзывчиво
        if (self.want_dir and self.dir != c.NONE and
                self.want_dir == (-self.dir[0], -self.dir[1])):
            self.dir = self.want_dir

        if self._aligned():
            col, row = self.col, self.row
            gained = maze.eat(col, row)

            if self.want_dir is None:
                # Клавишу отпустили — останавливаемся в центре клетки
                self.moving = False
            elif not maze.blocked(col + self.want_dir[0], row + self.want_dir[1]):
                # В желаемую сторону открыт проход — поворачиваем/едем
                self.dir = self.want_dir
                self.moving = True
            else:
                # Впереди по желаемой — стена; едем прямо, если там свободно
                self.moving = (self.dir != c.NONE and
                               not maze.blocked(col + self.dir[0], row + self.dir[1]))

        self.accum += speed
        if self.accum >= 1.0:
            self.accum -= 1.0
            if self.dir != c.NONE and self.moving:
                self.cx += self.dir[0] * c.PACMAN_SPEED
                self.cy += self.dir[1] * c.PACMAN_SPEED
                self._wrap()
                self.anim += 1

        return gained

    def _wrap(self):
        """Боковой тоннель: уехал за край — появляется с другого края."""
        if self.cx < 0:
            self.cx += c.FIELD_W
        elif self.cx >= c.FIELD_W:
            self.cx -= c.FIELD_W

    # --- Отрисовка ---------------------------------------------------------
    def draw(self, surface, oy):
        import pygame

        px, py = int(self.cx), int(self.cy + oy)
        r = c.TILE // 2 - 2
        pygame.draw.circle(surface, c.PACMAN, (px, py), r)

        # Рот открывается/закрывается; смотрит по направлению движения
        base = {c.RIGHT: 0, c.DOWN: 90, c.LEFT: 180, c.UP: 270}.get(self.dir, 0)
        half = 5 + 30 * (0.5 + 0.5 * math.sin(self.anim * 0.35))   # 5°..40°
        if self.dir == c.NONE:
            half = 40
        pts = [(px, py)]
        steps = 12
        for i in range(steps + 1):
            a = math.radians(base - half + (2 * half) * i / steps)
            pts.append((px + r * math.cos(a), py + r * math.sin(a)))
        pygame.draw.polygon(surface, c.BLACK, pts)
