"""Игрок: движение по сетке в 4 стороны.

Движение попиксельное (скорость в px/кадр) с привязкой перпендикуляра к
полосе сетки — как танк в battle_city. Привязка даёт «соскальзывание в
проёмы»: если жмёшь в стену, но почти напротив прохода, персонаж
подравнивается к полосе и въезжает.

Коллизии считаются по клеткам арены (без pygame), поэтому логику движения
можно тестировать headless. pygame нужен только для отрисовки.
"""

from .. import config as c


class Player:
    def __init__(self, col, row, index=0):
        self.index = index
        self.size = c.PLAYER_SIZE
        self.dir = c.DOWN
        self.alive = True
        self.dead_at = None                 # момент гибели (мс) для анимации/паузы
        self.color = c.PLAYER_COLORS[index % len(c.PLAYER_COLORS)]
        self.reset_stats()
        self.place_at_cell(col, row)

    def reset_stats(self):
        """Стартовые статы (новый раунд/матч сбрасывает бонусы)."""
        self.max_bombs = 1
        self.fire = 1
        self.speed_level = 0
        self.kick = False
        self.detonator = False
        self.curse = None                   # тип проклятия или None
        self.curse_until = 0                # до какого `now` действует

    # --- Статы под влиянием бонусов и проклятий ---
    def update_curse(self, now):
        """Снимает истёкшее проклятие."""
        if self.curse is not None and now >= self.curse_until:
            self.curse = None

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
        """Эффективная длина пламени (болезнь «мини» ужимает до 1)."""
        return 1 if self.curse == c.CURSE_MINI else self.fire

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
        elif kind == c.POW_FULLFIRE:
            self.fire = c.MAX_FIRE
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
        self.reset_stats()
        self.place_at_cell(col, row)

    def in_flame(self, explosions):
        """Накрыт ли игрок пламенем хотя бы одного взрыва (по клетке)."""
        cell = self.cell
        return any(ex.contains(cell) for ex in explosions)

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

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen, now=0):
        import pygame

        x, y, s = int(self.x), int(self.y), self.size
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

        # Тень на полу
        shadow = pygame.Surface((s, s // 3), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 70))
        screen.blit(shadow, (x, y + s - s // 4))

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
