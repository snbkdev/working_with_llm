"""Призрак: состояния (дом/выход/охота/глаза), движение по сетке, отрисовка.

Позиция — в пикселях (центр). В режиме охоты движется по сетке жадно к своей
цели (см. `ai.targeting`), решения — в центре клетки, скорость дробная (часть
кадров делает шаг). Съеденный превращается в «глаза» и возвращается в дом.
pygame нужен только для `draw`, поэтому логика движения тестируется headless.
"""

import math

from .. import config as c
from ..ai import targeting as ai

# Состояния
HOUSE, LEAVE, ROAM, EYES = range(4)


def _center(tile):
    return (tile[0] * c.TILE + c.TILE // 2, tile[1] * c.TILE + c.TILE // 2)


class Ghost:
    def __init__(self, name):
        self.name = name
        self.color = c.GHOST_COLORS[name]
        self.home = c.GHOST_HOME[name]
        self.frightened = False
        self.reset()

    def reset(self):
        self.cx, self.cy = _center(self.home)
        self.dir = c.LEFT
        self.frightened = False
        self.accum = 0.0
        self.bob = 0
        self._eyes_phase = 0
        # Blinky стартует снаружи (над воротцами), остальные — в доме
        self.state = ROAM if self.name == c.BLINKY else HOUSE

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
        return ((self.cx - c.TILE // 2) % c.TILE == 0 and
                (self.cy - c.TILE // 2) % c.TILE == 0)

    def _in_tunnel(self):
        return self.row == c.TUNNEL_ROW

    def release(self):
        """Выпустить из дома (вызывает игра по счётчику точек)."""
        if self.state == HOUSE:
            self.state = LEAVE

    def reverse(self):
        """Развернуться (смена scatter↔chase / начало испуга)."""
        if self.state == ROAM:
            self.dir = (-self.dir[0], -self.dir[1])

    def eaten(self):
        """Съеден Пакманом — уходит «глазами» домой."""
        self.state = EYES
        self.frightened = False
        self._eyes_phase = 0

    def is_hittable(self):
        return self.state in (ROAM, LEAVE)

    # --- Обновление --------------------------------------------------------
    def update(self, maze, pac_tile, pac_dir, blinky_tile, mode, speed, rng):
        if self.state == HOUSE:
            self._do_bob()
        elif self.state == LEAVE:
            self._do_leave()
        elif self.state == EYES:
            for _ in range(2):                # «глаза» быстрые
                self._eyes_step(maze)
        else:                                 # ROAM
            frac = c.FRIGHT_SPEED if self.frightened else speed
            if self._in_tunnel():
                frac = min(frac, c.TUNNEL_SPEED)
            self.accum += frac
            if self.accum >= 1.0:
                self.accum -= 1.0
                self._roam_step(maze, pac_tile, pac_dir, blinky_tile, mode, rng)

    def _roam_step(self, maze, pac_tile, pac_dir, blinky_tile, mode, rng):
        if self._aligned():
            col, row = self.col, self.row
            if self.frightened:
                self.dir = ai.frightened_dir(maze, col, row, self.dir, rng)
            elif mode == c.SCATTER:
                self.dir = ai.best_dir(maze, col, row, self.dir, c.SCATTER_TARGETS[self.name])
            else:
                target = ai.chase_target(self.name, pac_tile, pac_dir, blinky_tile, (col, row))
                self.dir = ai.best_dir(maze, col, row, self.dir, target)
        self.cx += self.dir[0] * 2
        self.cy += self.dir[1] * 2
        self._wrap()

    def _do_bob(self):
        hx, hy = _center(self.home)
        self.bob = (self.bob + 4) % 360
        self.cx = hx
        self.cy = hy + int(5 * math.sin(math.radians(self.bob)))

    def _do_leave(self):
        ex, ey = _center(c.HOUSE_EXIT)
        if self.cx != ex:
            self.cx += 2 if self.cx < ex else -2
        elif self.cy > ey:
            self.cy -= 2
        else:
            self.cx, self.cy = ex, ey
            self.state = ROAM
            self.dir = c.LEFT

    def _eyes_step(self, maze):
        if self._eyes_phase == 0:             # вернуться к выходу над домом
            if self.tile() == c.HOUSE_EXIT and self._aligned():
                self._eyes_phase = 1
                return
            if self._aligned():
                self.dir = ai.best_dir(maze, self.col, self.row, self.dir,
                                       c.HOUSE_EXIT, gate_ok=True)
            self.cx += self.dir[0] * 2
            self.cy += self.dir[1] * 2
            self._wrap()
        else:                                 # спуститься в дом и ожить
            tx, ty = _center(self.home)
            if self.cx != tx:
                self.cx += 2 if self.cx < tx else -2
            elif self.cy != ty:
                self.cy += 2 if self.cy < ty else -2
            else:
                self.state = LEAVE            # ожил — снова наружу

    def _wrap(self):
        if self.cx < 0:
            self.cx += c.FIELD_W
        elif self.cx >= c.FIELD_W:
            self.cx -= c.FIELD_W

    # --- Отрисовка ---------------------------------------------------------
    def draw(self, surface, oy, flash=False):
        import pygame

        px, py = int(self.cx), int(self.cy + oy)
        r = c.TILE // 2 - 1

        if self.state != EYES:
            if self.frightened:
                body = c.FRIGHT_WHITE if flash else c.FRIGHT_BLUE
            else:
                body = self.color
            # Голова-полукруг + туловище
            pygame.draw.circle(surface, body, (px, py - 1), r)
            pygame.draw.rect(surface, body, (px - r, py - 1, 2 * r, r))
            # Юбка-волна снизу
            step = (2 * r) // 3
            for i in range(3):
                x = px - r + i * step
                pygame.draw.polygon(surface, body, [
                    (x, py + r - 1), (x + step // 2, py + r - 6), (x + step, py + r - 1)])

        # Глаза (и у испуганного, и у обычного, и у «глаз»)
        if self.frightened and self.state != EYES:
            for ex in (px - r // 2, px + r // 2):     # испуганное «лицо»
                pygame.draw.circle(surface, c.FRIGHT_WHITE if not flash else c.FRIGHT_BLUE,
                                   (ex, py - 2), 3)
        else:
            dx, dy = self.dir
            for ex in (px - r // 2, px + r // 2):
                pygame.draw.circle(surface, c.EYE_WHITE, (ex, py - 3), 5)
                pygame.draw.circle(surface, c.EYE_IRIS, (ex + dx * 2, py - 3 + dy * 2), 2)
