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
        self.speed = c.PLAYER_SPEED
        self.dir = c.DOWN
        self.alive = True
        self.color = c.PLAYER_COLORS[index % len(c.PLAYER_COLORS)]
        # Статы (пригодятся на следующих шагах Этапа 1–3)
        self.max_bombs = 1
        self.fire = 1
        self.place_at_cell(col, row)

    # --- Позиция ---
    @property
    def offset(self):
        """Отступ внутри клетки, чтобы центрировать персонажа в полосе."""
        return (c.TILE - self.size) // 2

    def place_at_cell(self, col, row):
        self.x = float(col * c.TILE + self.offset)
        self.y = float(row * c.TILE + self.offset)

    @property
    def center(self):
        return int(self.x + self.size / 2), int(self.y + self.size / 2)

    @property
    def cell(self):
        cx, cy = self.center
        return cx // c.TILE, cy // c.TILE

    def _snap(self, value):
        """Привязка координаты к ближайшей полосе (с учётом отступа)."""
        return round((value - self.offset) / c.TILE) * c.TILE + self.offset

    # --- Коллизии по клеткам ---
    def _blocked(self, arena, x, y):
        """Пересекает ли габарит [x..x+size) непроходимую клетку арены."""
        c0 = int(x) // c.TILE
        c1 = int(x + self.size - 1) // c.TILE
        r0 = int(y) // c.TILE
        r1 = int(y + self.size - 1) // c.TILE
        for col in range(c0, c1 + 1):
            for row in range(r0, r1 + 1):
                if arena.is_solid(col, row):
                    return True
        return False

    # --- Движение ---
    def try_move(self, arena, direction):
        """Шаг в направлении с привязкой к полосе. True, если сдвинулись.

        Привязка перпендикуляра и шаг применяются атомарно: двигаемся только
        если и подравнивание, и шаг свободны — так нельзя въехать в стену.
        """
        if direction is None:
            return False
        self.dir = direction
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
        if self._blocked(arena, nx, ny):
            return False

        self.x, self.y = nx, ny
        return True

    # --- Отрисовка (pygame только здесь) ---
    def draw(self, screen):
        import pygame

        x, y, s = int(self.x), int(self.y), self.size
        cx = x + s // 2
        out = c.PLAYER_OUTLINE
        col = self.color
        dark = tuple(int(v * 0.55) for v in col)     # тень корпуса/шлема
        light = tuple(min(255, int(v * 1.15)) for v in col)

        # Тень на полу
        shadow = pygame.Surface((s, s // 3), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 70))
        screen.blit(shadow, (x, y + s - s // 4))

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
