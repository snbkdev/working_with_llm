"""Бонус (power-up): лежит на клетке поля, мигает, подбирается наездом.

Виды: 'star' (апгрейд танка), 'clock' (заморозить врагов),
'bomb' (взорвать всех врагов), 'steel' (стальная броня базы),
'life' (+1 жизнь). Иконки рисуются процедурно, как и вся графика игры.
"""

import math

import pygame

from .. import config as c


def _star_points(cx, cy, outer, inner, spikes=5, rot=-math.pi / 2):
    pts = []
    for i in range(spikes * 2):
        r = outer if i % 2 == 0 else inner
        ang = rot + math.pi * i / spikes
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


class PowerUp:
    def __init__(self, col, row, kind):
        self.col = col
        self.row = row
        self.kind = kind
        self.spawned = pygame.time.get_ticks()
        self.alive = True

    @property
    def rect(self):
        r = pygame.Rect(0, 0, c.TILE - 8, c.TILE - 8)
        r.center = (self.col * c.TILE + c.TILE // 2,
                    self.row * c.TILE + c.TILE // 2)
        return r

    def update(self, now):
        if now - self.spawned >= c.POWERUP_LIFETIME:
            self.alive = False

    # --- Отрисовка ---
    def draw(self, screen):
        now = pygame.time.get_ticks()
        # Под конец жизни мигаем быстрее — сигнал, что бонус вот-вот исчезнет
        left = c.POWERUP_LIFETIME - (now - self.spawned)
        period = c.POWERUP_BLINK_MS // 2 if left < 3000 else c.POWERUP_BLINK_MS
        if (now // period) % 2:
            return

        r = self.rect
        pygame.draw.rect(screen, c.POWERUP_BG, r, border_radius=4)
        pygame.draw.rect(screen, c.POWERUP_FRAME, r, 2, border_radius=4)
        getattr(self, f"_icon_{self.kind}")(screen, r)

    def _icon_star(self, screen, r):
        pts = _star_points(r.centerx, r.centery, r.width * 0.36, r.width * 0.15)
        pygame.draw.polygon(screen, c.STAR_COLOR, pts)

    def _icon_clock(self, screen, r):
        # «Часы»: циферблат со стрелками — заморозка врагов
        cx, cy = r.center
        rad = int(r.width * 0.32)
        pygame.draw.circle(screen, c.CLOCK_COLOR, (cx, cy), rad)
        pygame.draw.circle(screen, c.POWERUP_BG, (cx, cy), rad, 2)
        # Стрелки (на «10:10»)
        pygame.draw.line(screen, c.POWERUP_BG, (cx, cy), (cx, cy - rad + 2), 2)
        pygame.draw.line(screen, c.POWERUP_BG, (cx, cy), (cx + rad - 3, cy - 2), 2)

    def _icon_bomb(self, screen, r):
        # «Бомбочка»: круглый корпус с запалом — взрыв всех врагов
        cx, cy = r.center
        body = int(r.width * 0.26)
        pygame.draw.circle(screen, c.BOMB_COLOR, (cx, cy + 2), body)
        pygame.draw.circle(screen, c.POWERUP_FRAME, (cx, cy + 2), body, 1)
        # Блик и фитиль с искрой
        pygame.draw.circle(screen, c.POWERUP_FRAME, (cx - 2, cy), 1)
        pygame.draw.rect(screen, c.BOMB_COLOR, (cx - 3, cy - body - 1, 6, 4))
        pygame.draw.line(screen, c.STAR_COLOR,
                         (cx + 2, cy - body - 1), (cx + 6, cy - body - 5), 2)

    def _icon_steel(self, screen, r):
        # «Сталь»: бронеплита с заклёпками — броня базы
        cx, cy = r.center
        plate = pygame.Rect(0, 0, int(r.width * 0.56), int(r.width * 0.56))
        plate.center = (cx, cy)
        pygame.draw.rect(screen, c.STEEL_ITEM_COLOR, plate, border_radius=2)
        pygame.draw.rect(screen, c.POWERUP_BG, plate, 2, border_radius=2)
        for bx, by in ((plate.x + 3, plate.y + 3), (plate.right - 3, plate.y + 3),
                       (plate.x + 3, plate.bottom - 3), (plate.right - 3, plate.bottom - 3)):
            pygame.draw.circle(screen, c.POWERUP_BG, (bx, by), 1)

    def _icon_life(self, screen, r):
        # «Орёл»: маленький танк — +1 жизнь
        cx, cy = r.center
        body = pygame.Rect(0, 0, int(r.width * 0.5), int(r.width * 0.42))
        body.center = (cx, cy + 1)
        pygame.draw.rect(screen, c.LIFE_COLOR, body, border_radius=2)
        # Гусеницы по бокам
        pygame.draw.rect(screen, c.POWERUP_BG, (body.x - 2, body.y, 3, body.height))
        pygame.draw.rect(screen, c.POWERUP_BG, (body.right - 1, body.y, 3, body.height))
        # Ствол вверх
        pygame.draw.line(screen, c.LIFE_COLOR, (cx, body.top), (cx, body.top - 5), 3)
