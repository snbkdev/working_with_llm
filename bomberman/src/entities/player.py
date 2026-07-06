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
        # Тень под ногами
        shadow = pygame.Surface((s, s // 3), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 70))
        screen.blit(shadow, (x, y + s - s // 3 + 2))

        # Туловище (капелька-комбинезон)
        body = pygame.Rect(x + 3, y + s // 2 - 2, s - 6, s // 2)
        pygame.draw.rect(screen, self.color, body, border_radius=6)
        pygame.draw.rect(screen, out, body, 2, border_radius=6)
        # Ножки
        pygame.draw.rect(screen, out, (x + 6, y + s - 6, 6, 5), border_radius=2)
        pygame.draw.rect(screen, out, (x + s - 12, y + s - 6, 6, 5), border_radius=2)

        # Голова-шлем
        head_r = s // 3
        head_c = (cx, y + head_r + 2)
        pygame.draw.circle(screen, self.color, head_c, head_r)
        pygame.draw.circle(screen, out, head_c, head_r, 2)
        # Козырёк шлема
        pygame.draw.arc(screen, out,
                        (cx - head_r, y + 2, head_r * 2, head_r * 2),
                        0.2, 2.94, 2)

        # Глаза смотрят по направлению движения
        dx, dy = self.dir
        ex, ey = head_c[0] + dx * 3, head_c[1] + dy * 2
        for off in (-4, 4):
            pygame.draw.circle(screen, (250, 250, 250), (ex + off, ey), 3)
            pygame.draw.circle(screen, (30, 40, 90),
                               (ex + off + dx, ey + dy), 1)
