"""Игрок: движение по сетке в 4 стороны.

Движение попиксельное (скорость в px/кадр) с привязкой перпендикуляра к
полосе сетки — как танк в battle_city. Привязка даёт «соскальзывание в
проёмы»: если жмёшь в стену, но почти напротив прохода, персонаж
подравнивается к полосе и въезжает.

Коллизии считаются по клеткам арены (без pygame), поэтому логику движения
можно тестировать headless. pygame нужен только для отрисовки.
"""

import math

from .. import config as c


class Player:
    def __init__(self, col, row, index=0):
        self.index = index
        self.size = c.PLAYER_SIZE
        self.dir = c.DOWN
        self.alive = True
        self.dead_at = None                 # момент гибели (мс) для анимации/паузы
        self.color = c.PLAYER_COLORS[index % len(c.PLAYER_COLORS)]
        self.jumping = False                # в прыжке (перелёт через клетку)
        self.jump_h = 0.0                   # текущая высота прыжка (для отрисовки)
        self.jump_from = (0.0, 0.0)
        self.jump_to = (0.0, 0.0)
        self.jump_start = 0
        self.special_until = 0              # пауза после телепорта/батута
        self.infect_until = 0              # пауза между передачами болезни
        self.reset_stats()
        self.place_at_cell(col, row)

    def reset_stats(self):
        """Стартовые статы (новый раунд/матч сбрасывает бонусы)."""
        self.max_bombs = 1
        self.fire = 1
        self.speed_level = 0
        self.kick = False
        self.punch = False                  # перчатка: бросок бомбы
        self.jump = False                   # пружина: прыжок через клетку
        self.detonator = False
        self.curse = None                   # тип проклятия или None
        self.curse_until = 0                # до какого `now` действует

    # --- Статы под влиянием бонусов и проклятий ---
    def update_curse(self, now):
        """Снимает истёкшее проклятие."""
        if self.curse is not None and now >= self.curse_until:
            self.curse = None

    def set_curse(self, kind, now):
        """Навести болезнь на срок `CURSE_MS`."""
        self.curse = kind
        self.curse_until = now + c.CURSE_MS

    def clear_curse(self):
        self.curse = None

    def touches(self, other):
        """Пересекаются ли габариты двух бойцов (касание для заражения)."""
        return (abs(self.x - other.x) < self.size
                and abs(self.y - other.y) < self.size)

    @property
    def speed(self):
        """Эффективная скорость (болезни перебивают бонусы)."""
        if self.curse == c.CURSE_SLOW:
            return c.CURSE_SPEED_SLOW
        if self.curse == c.CURSE_FAST:
            return c.CURSE_SPEED_FAST
        return c.PLAYER_SPEED + self.speed_level

    @property
    def flame(self):
        """Эффективная длина пламени (болезни «мини»/«мега» перебивают огонь)."""
        if self.curse == c.CURSE_MINI:
            return 1
        if self.curse == c.CURSE_MEGAFIRE:
            return c.MAX_FIRE
        return self.fire

    @property
    def bomb_fuse(self):
        """Фитиль ставящейся бомбы: короткий при болезни «короткий фитиль»."""
        return c.SHORTFUSE_MS if self.curse == c.CURSE_SHORTFUSE else c.FUSE_MS

    @property
    def can_bomb(self):
        return self.curse != c.CURSE_NOBOMB

    @property
    def auto_bomb(self):
        return self.curse == c.CURSE_AUTOBOMB

    def input_dir(self, direction):
        """Направление ввода с учётом болезни-реверса."""
        if direction is None:
            return None
        if self.curse == c.CURSE_REVERSE:
            return (-direction[0], -direction[1])
        return direction

    def apply_powerup(self, kind, now=0, rng=None):
        """Применяет подобранный бонус; череп наводит случайную болезнь."""
        import random
        rng = rng or random
        if kind == c.POW_BOMB:
            self.max_bombs = min(c.MAX_BOMBS, self.max_bombs + 1)
        elif kind == c.POW_FIRE:
            self.fire = min(c.MAX_FIRE, self.fire + 1)
        elif kind == c.POW_SPEED:
            self.speed_level = min(c.MAX_SPEED_LVL, self.speed_level + 1)
        elif kind == c.POW_KICK:
            self.kick = True
        elif kind == c.POW_PUNCH:
            self.punch = True
        elif kind == c.POW_JUMP:
            self.jump = True
        elif kind == c.POW_FULLFIRE:
            self.fire = min(c.MAX_FIRE, self.fire + 1)   # тоже +1 клетка, а не сразу максимум
        elif kind == c.POW_DETON:
            self.detonator = True
        elif kind == c.POW_SKULL:
            self.curse = rng.choice(c.CURSES)
            self.curse_until = now + c.CURSE_MS

    # --- Позиция ---
    @property
    def offset(self):
        """Отступ внутри клетки, чтобы центрировать персонажа в полосе."""
        return (c.TILE - self.size) // 2

    def place_at_cell(self, col, row):
        self.x = float(col * c.TILE + self.offset)
        self.y = float(row * c.TILE + self.offset)

    def kill(self, now=0):
        """Пометить погибшим (попал в пламя). Идемпотентно."""
        if self.alive:
            self.alive = False
            self.dead_at = now

    def respawn(self, col, row):
        """Оживить на клетке для нового раунда (бонусы сбрасываются)."""
        self.alive = True
        self.dead_at = None
        self.dir = c.DOWN
        self.jumping = False
        self.jump_h = 0.0
        self.special_until = 0
        self.infect_until = 0
        self.reset_stats()
        self.place_at_cell(col, row)

    def in_flame(self, explosions):
        """Накрыт ли игрок пламенем хотя бы одного взрыва (по клетке).

        В прыжке игрок в воздухе — пламя под ним не задевает (до приземления)."""
        if self.jumping:
            return False
        cell = self.cell
        return any(ex.contains(cell) for ex in explosions)

    # --- Прыжок через клетку (пружина) ---
    def jump_target(self, arena, direction):
        """Клетка приземления прыжка (через одну) или None, если некуда."""
        col, row = self.cell
        tc = col + direction[0] * c.JUMP_TILES
        tr = row + direction[1] * c.JUMP_TILES
        if not arena.in_bounds(tc, tr) or arena.is_solid(tc, tr):
            return None
        return tc, tr

    def start_jump(self, arena, now, force=False):
        """Начать прыжок в сторону взгляда.

        Обычно нужна пружина (`self.jump`); `force=True` (батут) прыгает без неё
        и при отсутствии выхода подпрыгивает на месте.
        """
        if self.jumping or (not self.jump and not force):
            return False
        target = self.jump_target(arena, self.dir)
        if target is None:
            if not force:
                return False
            target = self.cell                       # батут без выхода — на месте
        tc, tr = target
        self.jumping = True
        self.jump_start = now
        self.jump_from = (self.x, self.y)
        self.jump_to = (float(tc * c.TILE + self.offset),
                        float(tr * c.TILE + self.offset))
        self.jump_h = 0.0
        return True

    def update_jump(self, now):
        """Двигает игрока по параболе прыжка; по прилёту — приземляет."""
        if not self.jumping:
            return
        t = (now - self.jump_start) / c.JUMP_MS
        if t >= 1.0:
            self.x, self.y = self.jump_to
            self.jumping = False
            self.jump_h = 0.0
            return
        fx, fy = self.jump_from
        tx, ty = self.jump_to
        self.x = fx + (tx - fx) * t
        self.y = fy + (ty - fy) * t
        self.jump_h = math.sin(math.pi * t) * c.JUMP_ARC

    @property
    def center(self):
        return int(self.x + self.size / 2), int(self.y + self.size / 2)

    @property
    def cell(self):
        cx, cy = self.center
        return cx // c.TILE, cy // c.TILE

    @property
    def at_center(self):
        """Стоит ли ровно в центре клетки (можно безопасно менять направление)."""
        ox = round(self.x - self.offset) % c.TILE
        oy = round(self.y - self.offset) % c.TILE
        return ox == 0 and oy == 0

    def snap_to_center(self):
        """Ставит игрока ровно в центр текущей клетки (сброс дрейфа сетки).

        Нужно ботам: при нестандартной скорости (после бонуса) позиция может не
        попадать в узлы сетки — выравнивание держит движение по клеткам."""
        col, row = self.cell
        self.x = float(col * c.TILE + self.offset)
        self.y = float(row * c.TILE + self.offset)

    def _snap(self, value):
        """Привязка координаты к ближайшей полосе (с учётом отступа)."""
        return round((value - self.offset) / c.TILE) * c.TILE + self.offset

    # --- Коллизии по клеткам ---
    def _cells_at(self, x, y):
        """Клетки, которые накрывает габарит [x..x+size) в позиции (x, y)."""
        c0 = int(x) // c.TILE
        c1 = int(x + self.size - 1) // c.TILE
        r0 = int(y) // c.TILE
        r1 = int(y + self.size - 1) // c.TILE
        return [(col, row) for col in range(c0, c1 + 1)
                for row in range(r0, r1 + 1)]

    def _blocked(self, arena, x, y, solid_bombs=()):
        """Пересекает ли габарит непроходимую клетку арены или бомбу."""
        for col, row in self._cells_at(x, y):
            if arena.is_solid(col, row) or (col, row) in solid_bombs:
                return True
        return False

    # --- Движение ---
    def try_move(self, arena, direction, bomb_cells=()):
        """Шаг в направлении с привязкой к полосе. True, если сдвинулись.

        Привязка перпендикуляра и шаг применяются атомарно: двигаемся только
        если и подравнивание, и шаг свободны — так нельзя въехать в стену.

        `bomb_cells` — клетки со стоящими бомбами. Бомба под самим игроком
        проходима (только что поставил и уходит), сошёл с неё — блокирует.
        """
        if direction is None:
            return False
        self.dir = direction
        # Бомбы твёрдые, кроме тех, на которых игрок сейчас стоит
        here = set(self._cells_at(self.x, self.y))
        solid_bombs = {cell for cell in bomb_cells if cell not in here}

        nx, ny = self.x, self.y
        if direction in (c.LEFT, c.RIGHT):
            ny = self._snap(self.y)          # подравнять по вертикали к полосе
        else:
            nx = self._snap(self.x)          # подравнять по горизонтали
        nx += direction[0] * self.speed
        ny += direction[1] * self.speed

        # Границы поля
        if nx < 0 or ny < 0 or nx + self.size > c.FIELD_W or ny + self.size > c.FIELD_H:
            return False
        if self._blocked(arena, nx, ny, solid_bombs):
            return False

        self.x, self.y = nx, ny
        return True

    def push(self, arena, direction, dist, bomb_cells=()):
        """Сдвиг на `dist` px по направлению без смены взгляда (конвейер).

        Привязывает перпендикуляр к полосе и уважает стены/бомбы — как `try_move`,
        но не трогает `self.dir` и не зависит от скорости персонажа.
        """
        here = set(self._cells_at(self.x, self.y))
        solid_bombs = {cell for cell in bomb_cells if cell not in here}
        nx, ny = self.x, self.y
        if direction in (c.LEFT, c.RIGHT):
            ny = self._snap(self.y)
        else:
            nx = self._snap(self.x)
        nx += direction[0] * dist
        ny += direction[1] * dist
        if nx < 0 or ny < 0 or nx + self.size > c.FIELD_W or ny + self.size > c.FIELD_H:
            return False
        if self._blocked(arena, nx, ny, solid_bombs):
            return False
        self.x, self.y = nx, ny
        return True

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen, now=0):
        import pygame

        x, s = int(self.x), self.size
        lift = int(self.jump_h)                      # подъём в прыжке
        gy = int(self.y)                             # «земля» (для тени)
        y = gy - lift                                # корпус приподнят
        cx = x + s // 2
        out = c.PLAYER_OUTLINE
        # Погибший — обесцвеченный, оседает и мигает; глаза-крестики, нимб
        dead = not self.alive
        col = c.DEAD_COLOR if dead else self.color
        if dead:
            self._draw_dead(pygame, screen, x, y, s, cx, out, now)
            return
        dark = tuple(int(v * 0.55) for v in col)     # тень корпуса/шлема
        light = tuple(min(255, int(v * 1.15)) for v in col)

        # Тень на полу (в прыжке — уменьшается и остаётся под ногами)
        sw = max(6, s - lift)
        shadow = pygame.Surface((sw, s // 3), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 70 if lift == 0 else 45))
        screen.blit(shadow, (x + (s - sw) // 2, gy + s - s // 4))

        # Проклятие — болезненная зеленца тела и мигающая аура под ногами
        if self.curse is not None:
            col = (int(col[0] * 0.7 + 30), int(col[1] * 0.7 + 60),
                   int(col[2] * 0.7 + 30))
            dark = tuple(int(v * 0.55) for v in col)
            light = tuple(min(255, int(v * 1.15)) for v in col)
            import math
            aura = 3 + int(2 * (1 + math.sin(now * 0.02)))
            pygame.draw.ellipse(screen, (150, 90, 190),
                                (x + 2, y + s - 6, s - 4, 6), max(1, aura // 2))

        # Ножки
        pygame.draw.ellipse(screen, out, (x + 5, y + s - 7, 8, 7))
        pygame.draw.ellipse(screen, out, (x + s - 13, y + s - 7, 8, 7))

        # Туловище (пухлый комбинезон)
        body = pygame.Rect(x + 5, y + s // 2 + 1, s - 10, s // 2 - 4)
        pygame.draw.rect(screen, col, body, border_radius=7)
        pygame.draw.rect(screen, out, body, 2, border_radius=7)
        # Ремень + пряжка
        belt_y = body.y + body.height // 2
        pygame.draw.line(screen, dark, (body.x + 2, belt_y), (body.right - 2, belt_y), 3)
        pygame.draw.rect(screen, c.ACCENT, (cx - 3, belt_y - 2, 6, 4))

        # Голова-шлем: круглый купол с бликом
        head_r = s // 2 - 1
        hcx, hcy = cx, y + head_r
        pygame.draw.circle(screen, col, (hcx, hcy), head_r)
        pygame.draw.circle(screen, light, (hcx - head_r // 3, hcy - head_r // 3),
                           max(2, head_r // 4))
        pygame.draw.circle(screen, out, (hcx, hcy), head_r, 2)

        # Антенна с «камушком» на макушке
        pygame.draw.line(screen, out, (hcx, hcy - head_r), (hcx, hcy - head_r - 5), 2)
        pygame.draw.circle(screen, c.ACCENT, (hcx, hcy - head_r - 6), 3)
        pygame.draw.circle(screen, out, (hcx, hcy - head_r - 6), 3, 1)

        # Тёмный козырёк-полоса поверх глаз (уже диаметра — не выходит за купол)
        vw, vh = int(head_r * 1.6), max(9, head_r)
        visor = pygame.Rect(hcx - vw // 2, hcy - 2, vw, vh)
        pygame.draw.rect(screen, dark, visor, border_radius=vh // 2)

        # Большие глаза на козырьке, зрачки смотрят по направлению движения
        dx, dy = self.dir
        eye_y = visor.y + vh // 2
        for off in (-5, 6):
            pygame.draw.ellipse(screen, (250, 250, 250), (hcx + off - 4, eye_y - 4, 8, 9))
            pygame.draw.circle(screen, (30, 40, 90),
                               (hcx + off + dx * 2, eye_y + dy * 2), 2)

    def _draw_dead(self, pygame, screen, x, y, s, cx, out, now):
        """Побеждённый: серый, оседает вниз, глаза-крестики и нимб; мигает."""
        elapsed = 0 if self.dead_at is None else max(0, now - self.dead_at)
        k = min(1.0, elapsed / max(1, c.RESPAWN_MS))     # 0 → 1 за паузу
        if (now // 120) % 2 == 0 and k > 0.15:            # мигание перед рестартом
            return
        sink = int(6 * k)                                 # немного «оседает»
        col = c.DEAD_COLOR

        # Тень
        shadow = pygame.Surface((s, s // 3), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 70))
        screen.blit(shadow, (x, y + s - s // 4))

        # Туловище (осевшее)
        body = pygame.Rect(x + 5, y + s // 2 + 1 + sink, s - 10, s // 2 - 4 - sink)
        if body.height > 4:
            pygame.draw.rect(screen, col, body, border_radius=7)
            pygame.draw.rect(screen, out, body, 2, border_radius=7)

        # Голова с крестиками-глазами
        head_r = s // 2 - 1
        hcx, hcy = cx, y + head_r + sink
        pygame.draw.circle(screen, col, (hcx, hcy), head_r)
        pygame.draw.circle(screen, out, (hcx, hcy), head_r, 2)
        for ex in (-5, 6):
            ecx, ecy = hcx + ex, hcy
            pygame.draw.line(screen, out, (ecx - 3, ecy - 3), (ecx + 3, ecy + 3), 2)
            pygame.draw.line(screen, out, (ecx - 3, ecy + 3), (ecx + 3, ecy - 3), 2)

        # Нимб над головой
        halo_y = hcy - head_r - 6
        pygame.draw.ellipse(screen, c.ACCENT, (hcx - 8, halo_y - 3, 16, 7), 2)


def spread_curse(a, b, now):
    """Заражение касанием: больной передаёт болезнь здоровому и выздоравливает.

    «Горячая картошка» из Atomic Bomberman — болезнь перескакивает на того, кого
    коснулся заражённый. Работает, только если ровно один из двоих болен, оба на
    земле (не в прыжке) и не в паузе после недавней передачи. Возвращает True при
    передаче.
    """
    if a.jumping or b.jumping:
        return False
    if now < a.infect_until or now < b.infect_until:
        return False
    if not a.touches(b):
        return False
    if (a.curse is None) == (b.curse is None):     # оба больны или оба здоровы
        return False
    sick, well = (a, b) if a.curse is not None else (b, a)
    well.set_curse(sick.curse, now)
    sick.clear_curse()
    a.infect_until = b.infect_until = now + c.CONTAGION_CD_MS
    return True
