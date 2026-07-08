"""Бомба: лежит на клетке, тикает фитилём и по истечении «взрывается».

Сам крестообразный взрыв (пламя, разрушение блоков, цепные детонации) —
следующий шаг Этапа 1; здесь бомба лишь помечается `exploded`, когда
догорел фитиль. Таймер — на инъектируемом `now` (мс), чтобы тестировать
без pygame и без окна. pygame нужен только для отрисовки.
"""

import math

from .. import config as c


class Bomb:
    def __init__(self, col, row, owner=0, fire=1, now=0, remote=False, fuse=None):
        self.col = col
        self.row = row
        self.owner = owner          # индекс игрока-владельца (для лимита/счёта)
        self.fire = fire            # длина будущего пламени
        self.placed = now
        self.fuse = c.FUSE_MS if fuse is None else fuse
        self.remote = remote        # детонатор: не срабатывает по фитилю
        self.exploded = False
        # Пиксельная позиция центра — нужна для скольжения при «пинке»
        self.px, self.py = self.center()
        self.vel = None             # направление скольжения (dx, dy) или None
        # Полёт после «броска» (перчатка)
        self.airborne = False
        self.fly_from = (self.px, self.py)
        self.fly_to = (self.px, self.py)
        self.fly_start = 0
        self.fly_dur = c.THROW_MS
        self.fly_h = 0.0            # текущая высота дуги (для отрисовки)
        self._fuse_off = 0         # остаток фитиля, сохраняемый на время полёта

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
        цепную реакцию или пламя. В полёте фитиль «на паузе».
        """
        if self.airborne:
            return self.exploded
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

    # --- Бросок (перчатка) ---
    def throw(self, direction, arena, occupied, now):
        """Швырнуть бомбу по дуге на `THROW_TILES` клеток по направлению.

        Приземляется на первую свободную клетку (с обёрткой вокруг краёв поля).
        Фитиль на время полёта замирает — остаток восстанавливается при посадке.
        """
        if self.airborne or self.moving:
            return
        tc, tr = flight_target(arena, occupied, self.col, self.row, direction)
        self._fuse_off = self.time_left(now)         # сколько фитиля осталось
        self.airborne = True
        self.fly_start = now
        self.fly_from = (self.px, self.py)
        self.fly_to = (tc * c.TILE + c.TILE // 2, tr * c.TILE + c.TILE // 2)
        self.col, self.row = tc, tr                  # логически уже на цели
        self.vel = None

    def update_flight(self, now):
        """Двигает бомбу по параболе; по прилёту — приземляет."""
        if not self.airborne:
            return
        t = (now - self.fly_start) / self.fly_dur
        if t >= 1.0:
            self._land(now)
            return
        fx, fy = self.fly_from
        tx, ty = self.fly_to
        self.px = fx + (tx - fx) * t
        self.py = fy + (ty - fy) * t
        self.fly_h = math.sin(math.pi * t) * c.THROW_ARC

    def _land(self, now):
        self.airborne = False
        self.fly_h = 0.0
        self.px, self.py = self.fly_to
        self.col = int(self.px) // c.TILE
        self.row = int(self.py) // c.TILE
        # Восстановить остаток фитиля: time_left снова равен _fuse_off
        self.placed = now - (self.fuse - self._fuse_off)

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen, now):
        import pygame

        lift = int(self.fly_h)
        if lift > 0:                                          # тень на земле под броском
            sh = pygame.Surface((c.TILE, c.TILE // 3), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 90), (6, 0, c.TILE - 12, c.TILE // 3))
            screen.blit(sh, (int(self.px) - c.TILE // 2, int(self.py) - c.TILE // 6))
        cx, cy = int(self.px), int(self.py) - lift           # с учётом скольжения/полёта
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


def _wrap_cell(col, row):
    """Клетка с обёрткой внутрь поля (края «телепортируют» брошенную бомбу)."""
    lo_c, hi_c = 1, c.COLS - 2
    lo_r, hi_r = 1, c.ROWS - 2
    if col < lo_c:
        col = hi_c
    elif col > hi_c:
        col = lo_c
    if row < lo_r:
        row = hi_r
    elif row > hi_r:
        row = lo_r
    return col, row


def flight_target(arena, occupied, col, row, direction, tiles=None):
    """Клетка приземления брошенной бомбы.

    Летит `tiles` клеток по направлению (с обёрткой вокруг краёв поля). Если
    цель — стена/ящик или занята (`occupied`), ищем дальше по курсу первую
    свободную клетку. Если такой нет — возвращаем исходную (бросок «сорвался»).
    """
    if tiles is None:
        tiles = c.THROW_TILES
    dc, dr = direction
    cc, rr = col, row
    for _ in range(tiles):
        cc, rr = _wrap_cell(cc + dc, rr + dr)
    for _ in range(c.COLS * c.ROWS):
        if not arena.is_solid(cc, rr) and (cc, rr) not in occupied:
            return cc, rr
        cc, rr = _wrap_cell(cc + dc, rr + dr)
    return col, row


def can_place(bombs, cell, owner, max_bombs):
    """Можно ли поставить бомбу: не превышен лимит и клетка ещё свободна."""
    active = sum(1 for b in bombs if b.owner == owner and not b.exploded)
    if active >= max_bombs:
        return False
    if any(b.cell == cell for b in bombs):
        return False
    return True
