"""Бомба: лежит на клетке, тикает фитилём и по истечении «взрывается».

Сам крестообразный взрыв (пламя, разрушение блоков, цепные детонации) —
следующий шаг Этапа 1; здесь бомба лишь помечается `exploded`, когда
догорел фитиль. Таймер — на инъектируемом `now` (мс), чтобы тестировать
без pygame и без окна. pygame нужен только для отрисовки.
"""

import math

from .. import config as c


class Bomb:
    def __init__(self, col, row, owner=0, fire=1, now=0):
        self.col = col
        self.row = row
        self.owner = owner          # индекс игрока-владельца (для лимита/счёта)
        self.fire = fire            # длина будущего пламени
        self.placed = now
        self.fuse = c.FUSE_MS
        self.exploded = False

    @property
    def cell(self):
        return self.col, self.row

    def center(self):
        return self.col * c.TILE + c.TILE // 2, self.row * c.TILE + c.TILE // 2

    def time_left(self, now):
        return max(0, self.fuse - (now - self.placed))

    def update(self, now):
        """Тик фитиля. Возвращает True, если бомба уже взорвалась."""
        if not self.exploded and now - self.placed >= self.fuse:
            self.exploded = True
        return self.exploded

    def detonate(self):
        """Мгновенный подрыв (цепная реакция/детонатор — следующие шаги)."""
        self.exploded = True

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen, now):
        import pygame

        cx, cy = self.center()
        progress = 1.0 - self.time_left(now) / self.fuse     # 0 → 1 к взрыву
        base = c.TILE // 2 - 4
        speed = 0.006 + 0.014 * progress                     # пульс учащается
        r = int(base * (1 + 0.10 * math.sin(now * speed)))

        pygame.draw.circle(screen, c.BOMB_COLOR, (cx, cy), r)
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
