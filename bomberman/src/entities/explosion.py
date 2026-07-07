"""Крестообразный взрыв: пламя из центра бомбы вдоль 4 лучей.

Геометрия: длина каждого луча = «огонь» игрока. Луч гаснет о несокрушимую
стену (её клетка в пламя не входит), а на разрушаемом ящике — включает эту
клетку, ломает **один** ящик и останавливается. Клетки-пламя нужны и для
отрисовки, и для проверки попадания игрока/цепного подрыва других бомб.

Геометрия считается чистыми функциями (`flame_rays`/`flame_cells`, без pygame
и без мутаций), поэтому легко тестируется headless. Время жизни — на
инъектируемом `now` (мс), как у бомбы. pygame нужен только для отрисовки.
"""

import math
import random

from .. import config as c

# Порядок лучей — оси креста
_RAYS = (c.UP, c.DOWN, c.LEFT, c.RIGHT)


def flame_rays(arena, col, row, fire):
    """Лучи пламени по направлениям и список задетых ящиков (без мутаций).

    Возвращает (rays, blocks):
      rays   — dict {направление: [клетки от центра к краю]};
      blocks — клетки с разрушаемым ящиком (по одному на луч, они же — концы).
    """
    rays = {}
    blocks = []
    for d in _RAYS:
        dx, dy = d
        line = []
        for step in range(1, fire + 1):
            nc, nr = col + dx * step, row + dy * step
            if arena.is_wall(nc, nr):
                break                       # несокрушимая стена — гасим луч
            if arena.is_block(nc, nr):
                line.append((nc, nr))
                blocks.append((nc, nr))
                break                       # ломаем один ящик и стоп
            line.append((nc, nr))           # пол — пламя идёт дальше
        rays[d] = line
    return rays, blocks


def flame_cells(arena, col, row, fire):
    """Все клетки пламени (начиная с центра) и задетые ящики."""
    rays, blocks = flame_rays(arena, col, row, fire)
    cells = [(col, row)]
    for d in _RAYS:
        cells.extend(rays[d])
    return cells, blocks


class Explosion:
    def __init__(self, arena, col, row, fire=1, now=0):
        self.col = col
        self.row = row
        self.fire = fire
        self.born = now
        self.life = c.FLAME_MS
        self.done = False
        self.rays, blocks = flame_rays(arena, col, row, fire)
        self.cells = [(col, row)]
        for d in _RAYS:
            self.cells.extend(self.rays[d])
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

        t = min(1.0, max(0.0, (now - self.born) / self.life))
        # Пламя распускается по клеткам от центра наружу за первые ~35% жизни
        reveal = min(1.0, t / 0.35)
        grow = min(1.0, t / 0.18)                     # ширина луча набирается
        fade = 1.0 if t < 0.6 else max(0.0, 1.0 - (t - 0.6) / 0.4)
        alpha = int(230 * fade)
        if alpha <= 0:
            return

        surf = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
        beam = max(5, int(c.TILE * 0.5 * grow))       # уже клетки — луч не «разливается»
        rng = random.Random(self.born + now // 70)

        # Лучи-«балки»: показываем только уже «долетевшие» клетки
        for d, line in self.rays.items():
            visible = math.ceil(len(line) * reveal)
            horiz = d in (c.LEFT, c.RIGHT)
            for i, (col, row) in enumerate(line[:visible]):
                tip = i == visible - 1
                self._band(pygame, surf, col, row, beam, horiz, alpha, rng, tip)
        # Центр — самый яркий, крест из двух полос + ядро
        self._band(pygame, surf, self.col, self.row, beam, True, alpha, rng, False)
        self._band(pygame, surf, self.col, self.row, beam, False, alpha, rng, False)
        cx, cy = self.col * c.TILE + c.TILE // 2, self.row * c.TILE + c.TILE // 2
        self._layers(pygame, surf, cx, cy, int(beam * 0.6), alpha)

        screen.blit(surf, (0, 0))

    def _band(self, pygame, surf, col, row, beam, horiz, alpha, rng, tip):
        """Полоса пламени в клетке вдоль оси (луч), с концом-«вспышкой»."""
        x, y = col * c.TILE, row * c.TILE
        cx, cy = x + c.TILE // 2, y + c.TILE // 2
        jit = rng.randint(-1, 1)                        # лёгкое дрожание языков
        b = max(4, beam + jit)
        if horiz:
            rect = pygame.Rect(x, cy - b // 2, c.TILE, b)
        else:
            rect = pygame.Rect(cx - b // 2, y, b, c.TILE)
        self._layers_rect(pygame, surf, rect, alpha)
        if tip:                                          # конец луча — круглая вспышка
            self._layers(pygame, surf, cx, cy, b // 2, alpha)

    def _layers_rect(self, pygame, surf, rect, alpha):
        r = min(rect.w, rect.h) // 2
        pygame.draw.rect(surf, (*c.FLAME_EDGE, alpha), rect, border_radius=r)
        inner = rect.inflate(-rect.w // 4 if rect.w > rect.h else -6,
                             -rect.h // 4 if rect.h > rect.w else -6)
        pygame.draw.rect(surf, (*c.FLAME_HOT, alpha), inner,
                         border_radius=min(inner.w, inner.h) // 2)

    def _layers(self, pygame, surf, cx, cy, r, alpha):
        pygame.draw.circle(surf, (*c.FLAME_EDGE, alpha), (cx, cy), r)
        pygame.draw.circle(surf, (*c.FLAME_HOT, alpha), (cx, cy), max(2, int(r * 0.7)))
        pygame.draw.circle(surf, (*c.FLAME_CORE, alpha), (cx, cy), max(1, int(r * 0.42)))


def detonate_chain(arena, bombs, explosions, now):
    """Взрывает уже помеченные бомбы с цепной реакцией.

    Перед вызовом фитили обновлены (`bomb.update(now)`), так что часть бомб уже
    `exploded`. Каждая такая бомба порождает пламя; если оно накрывает клетку
    другой живой бомбы — та мгновенно детонирует и тоже попадает в очередь.
    Мутирует `explosions` (добавляет вспышки) и `bombs` (ставит `exploded`).
    Возвращает список новых вспышек.
    """
    queue = [b for b in bombs if b.exploded]
    seen = {id(b) for b in queue}
    fresh = []
    while queue:
        b = queue.pop()
        ex = Explosion(arena, b.col, b.row, b.fire, now)
        explosions.append(ex)
        fresh.append(ex)
        for other in bombs:
            if (id(other) not in seen and not other.exploded
                    and ex.contains(other.cell)):
                other.detonate()
                seen.add(id(other))
                queue.append(other)
    return fresh
