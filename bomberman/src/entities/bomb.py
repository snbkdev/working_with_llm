"""Бомба: лежит на клетке, тикает фитилём и по истечении «взрывается».

Сам крестообразный взрыв (пламя, разрушение блоков, цепные детонации) —
следующий шаг Этапа 1; здесь бомба лишь помечается `exploded`, когда
догорел фитиль. Таймер — на инъектируемом `now` (мс), чтобы тестировать
без pygame и без окна. pygame нужен только для отрисовки.
"""

import math

from .. import config as c


class Bomb:
    def __init__(self, col, row, owner=0, fire=1, now=0, remote=False):
        self.col = col
        self.row = row
        self.owner = owner          # индекс игрока-владельца (для лимита/счёта)
        self.fire = fire            # длина будущего пламени
        self.placed = now
        self.fuse = c.FUSE_MS
        self.remote = remote        # детонатор: не срабатывает по фитилю
        self.exploded = False
        # Пиксельная позиция центра — нужна для скольжения при «пинке»
        self.px, self.py = self.center()
        self.vel = None             # направление скольжения (dx, dy) или None

    @property
    def cell(self):
        return self.col, self.row

    @property
    def moving(self):
        return self.vel is not None

    def center(self):
        return self.col * c.TILE + c.TILE // 2, self.row * c.TILE + c.TILE // 2

    def time_left(self, now):
        return max(0, self.fuse - (now - self.placed))

    def update(self, now):
        """Тик фитиля. Возвращает True, если бомба уже взорвалась.

        Детонаторные (remote) бомбы по фитилю не взрываются — ждут кнопку,
        цепную реакцию или пламя.
        """
        if not self.exploded and not self.remote and now - self.placed >= self.fuse:
            self.exploded = True
        return self.exploded

    def detonate(self):
        """Мгновенный подрыв (цепная реакция / детонатор / пламя)."""
        self.exploded = True

    # --- Скольжение после «пинка» ---
    def kick(self, direction):
        """Задать направление скольжения (если бомба стоит)."""
        if not self.moving:
            self.vel = direction

    def update_motion(self, arena, bombs, block_cells):
        """Двигает пиннутую бомбу по пикселям, останавливая у препятствий.

        Останавливается по центру клетки перед стеной/ящиком/другой бомбой
        или клеткой из `block_cells` (например, где стоит игрок).
        """
        if not self.moving:
            return
        dx, dy = self.vel
        self.px += dx * c.KICK_SPEED
        self.py += dy * c.KICK_SPEED
        col = int(self.px) // c.TILE
        row = int(self.py) // c.TILE
        # Пройден центр новой клетки — проверяем следующую
        if (col, row) != (self.col, self.row):
            self.col, self.row = col, row
        cxc, cyc = self.center()
        # У центра клетки решаем: ехать дальше или встать
        near_center = abs(self.px - cxc) <= c.KICK_SPEED and abs(self.py - cyc) <= c.KICK_SPEED
        if near_center:
            nc, nr = self.col + dx, self.row + dy
            occupied = any(b is not self and b.cell == (nc, nr) for b in bombs)
            if arena.is_solid(nc, nr) or occupied or (nc, nr) in block_cells:
                self.px, self.py = cxc, cyc      # встать ровно в клетку
                self.vel = None

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen, now):
        import pygame

        cx, cy = int(self.px), int(self.py)                  # с учётом скольжения
        progress = 1.0 - self.time_left(now) / self.fuse     # 0 → 1 к взрыву
        base = c.TILE // 2 - 4
        speed = 0.006 + 0.014 * progress                     # пульс учащается
        r = int(base * (1 + 0.10 * math.sin(now * speed)))

        # В последней трети бомба «мигает» белым — сигнал скорого взрыва
        body = c.BOMB_COLOR
        if progress > 0.66 and (now // max(60, int(200 * (1 - progress)) + 40)) % 2 == 0:
            f = (progress - 0.66) / 0.34
            body = tuple(min(255, int(v + (240 - v) * f)) for v in c.BOMB_COLOR)
        pygame.draw.circle(screen, body, (cx, cy), r)
        pygame.draw.circle(screen, c.BOMB_DARK, (cx, cy), r, 2)
        pygame.draw.circle(screen, c.BOMB_LIGHT, (cx - r // 3, cy - r // 3),
                           max(2, r // 4))
        # Колпачок-фитильодержатель
        pygame.draw.rect(screen, (90, 92, 100), (cx - 3, cy - r - 3, 6, 5),
                         border_radius=1)
        # Фитиль укорачивается по мере горения
        fl = int(9 * (1 - progress))
        tipx, tipy = cx + 2 + fl // 2, cy - r - 4 - fl
        pygame.draw.line(screen, c.BOMB_FUSE, (cx + 1, cy - r - 2), (tipx, tipy), 2)
        # Искра мигает быстрее к концу
        blink = max(60, int(220 * (1 - progress)) + 60)
        if (now // blink) % 2 == 0:
            pygame.draw.circle(screen, c.BOMB_SPARK, (tipx, tipy), 3)
            pygame.draw.circle(screen, c.BOMB_SPARK2, (tipx, tipy), 1)


def can_place(bombs, cell, owner, max_bombs):
    """Можно ли поставить бомбу: не превышен лимит и клетка ещё свободна."""
    active = sum(1 for b in bombs if b.owner == owner and not b.exploded)
    if active >= max_bombs:
        return False
    if any(b.cell == cell for b in bombs):
        return False
    return True
