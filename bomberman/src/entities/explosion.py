"""Крестообразный взрыв: пламя из центра бомбы вдоль 4 лучей.

Геометрия: длина каждого луча = «огонь» игрока. Луч гаснет о несокрушимую
стену (её клетка в пламя не входит), а на разрушаемом ящике — включает эту
клетку, ломает **один** ящик и останавливается. Клетки-пламя нужны и для
отрисовки, и для проверки попадания игрока/цепного подрыва других бомб.

Геометрия считается чистой функцией `flame_cells` (без pygame и без мутаций),
поэтому легко тестируется headless. Время жизни — на инъектируемом `now` (мс),
как у бомбы. pygame нужен только для отрисовки.
"""

import random

from .. import config as c

# Порядок лучей — оси креста
_RAYS = (c.UP, c.DOWN, c.LEFT, c.RIGHT)


def flame_cells(arena, col, row, fire):
    """Клетки пламени и попавшие под него ящики (без изменения арены).

    Возвращает (cells, blocks):
      cells  — список (col, row) всех клеток пламени, начиная с центра;
      blocks — подсписок клеток, где стоит разрушаемый ящик (по одному на луч).
    """
    cells = [(col, row)]
    blocks = []
    for dx, dy in _RAYS:
        for step in range(1, fire + 1):
            nc, nr = col + dx * step, row + dy * step
            if arena.is_wall(nc, nr):
                break                       # несокрушимая стена — гасим луч
            if arena.is_block(nc, nr):
                cells.append((nc, nr))
                blocks.append((nc, nr))
                break                       # ломаем один ящик и стоп
            cells.append((nc, nr))          # пол — пламя идёт дальше
    return cells, blocks


class Explosion:
    def __init__(self, arena, col, row, fire=1, now=0):
        self.col = col
        self.row = row
        self.fire = fire
        self.born = now
        self.life = c.FLAME_MS
        self.done = False
        self.cells, blocks = flame_cells(arena, col, row, fire)
        # Разрушаем задетые ящики сразу; список пригодится для выпадения бонусов
        self.destroyed = [cell for cell in blocks if arena.destroy_block(*cell)]

    def contains(self, cell):
        """Накрывает ли пламя клетку (для гибели игрока и цепных детонаций)."""
        return cell in self.cells

    def update(self, now):
        """Тик жизни пламени. Возвращает True, когда пора убирать."""
        if now - self.born >= self.life:
            self.done = True
        return self.done

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen, now):
        import pygame

        # Ярче в начале, гаснет к концу
        k = 1.0 - min(1.0, (now - self.born) / self.life)
        rng = random.Random(self.born * 1000 + now // 60)   # лёгкое дрожание языков
        for col, row in self.cells:
            x, y = col * c.TILE, row * c.TILE
            cx, cy = x + c.TILE // 2, y + c.TILE // 2
            center = (col, row) == (self.col, self.row)
            r_edge = int((c.TILE // 2 - 2) * (0.75 + 0.25 * k))
            r_hot = int(r_edge * 0.72) + rng.randint(-1, 1)
            r_core = int(r_edge * (0.5 if center else 0.4))
            pygame.draw.circle(screen, c.FLAME_EDGE, (cx, cy), r_edge)
            pygame.draw.circle(screen, c.FLAME_HOT, (cx, cy), max(2, r_hot))
            pygame.draw.circle(screen, c.FLAME_CORE, (cx, cy), max(1, r_core))
