"""Универсальное меню Battle City.

Используется и для главного меню (на весь экран), и для мини-меню паузы
(полупрозрачный оверлей поверх игры). Пункты задаются списком кортежей
(подпись, действие, активен). handle_event возвращает строку-действие
выбранного пункта или None.
"""

import pygame

from . import config as c


class Menu:
    def __init__(self, items, title=None, subtitle=None, overlay=False):
        self.title_font = pygame.font.SysFont("Helvetica", 44, bold=True)
        self.item_font = pygame.font.SysFont("Helvetica", 24, bold=True)
        self.small_font = pygame.font.SysFont("Helvetica", 14)
        self.items = items                 # [(подпись, действие, активен), ...]
        self.title = title
        self.subtitle = subtitle
        self.overlay = overlay
        self.gap = 48
        # Оверлей центрируем над полем, полноэкранное — над всем окном
        self.cx = (c.FIELD_W // 2) if overlay else (c.WIDTH // 2)
        self.cy = c.HEIGHT // 2 + (10 if overlay else 30)
        self.index = self._first_active()

    # --- Вспомогательное ---
    def _first_active(self):
        for i, item in enumerate(self.items):
            if item[2]:
                return i
        return 0

    def _items_top(self):
        return self.cy - (len(self.items) * self.gap) // 2 + self.gap // 2

    def item_rects(self):
        top = self._items_top()
        return [
            pygame.Rect(self.cx - 140, top + i * self.gap - 19, 280, 38)
            for i in range(len(self.items))
        ]

    def _move(self, delta):
        n = len(self.items)
        j = self.index
        for _ in range(n):                 # пропускаем неактивные пункты
            j = (j + delta) % n
            if self.items[j][2]:
                self.index = j
                return

    def _activate(self, i):
        _, action, active = self.items[i]
        return action if active else None

    # --- Ввод ---
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._move(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self._activate(self.index)
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.item_rects()):
                if rect.collidepoint(event.pos) and self.items[i][2]:
                    self.index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.item_rects()):
                if rect.collidepoint(event.pos):
                    return self._activate(i)
        return None

    # --- Отрисовка ---
    def draw(self, screen):
        if self.overlay:
            dim = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
            dim.fill((10, 10, 14, 205))
            screen.blit(dim, (0, 0))
        else:
            screen.fill(c.BG_COLOR)

        top = self._items_top()
        if self.title:
            t = self.title_font.render(self.title, True, c.PLAYER_COLOR)
            screen.blit(t, (self.cx - t.get_width() // 2, top - 92))
        if self.subtitle:
            s = self.small_font.render(self.subtitle, True, c.STEEL_COLOR)
            screen.blit(s, (self.cx - s.get_width() // 2, top - 46))

        for i, rect in enumerate(self.item_rects()):
            label, _, active = self.items[i]
            selected = (i == self.index)
            if not active:
                color = (110, 110, 110)
            elif selected:
                color = c.ACCENT
            else:
                color = c.TEXT_COLOR

            surf = self.item_font.render(label, True, color)
            sx = rect.centerx - surf.get_width() // 2
            sy = rect.centery - surf.get_height() // 2
            screen.blit(surf, (sx, sy))

            if selected:
                ty = rect.centery
                tx = sx - 20
                pygame.draw.polygon(
                    screen, color, [(tx, ty - 7), (tx + 12, ty), (tx, ty + 7)]
                )

        hint = self.small_font.render(
            "W/S или стрелки — выбор · Enter — ОК", True, (150, 150, 150)
        )
        hy = self._items_top() + len(self.items) * self.gap - self.gap // 2 + 18
        screen.blit(hint, (self.cx - hint.get_width() // 2, hy))
