"""Главное меню Battle City.

Пункты: «Новая игра» (активна), «Загрузка» и «Настройки» (заглушки,
пока неактивны), «Выход» (активна). Управление — клавишами и мышью.
Метод handle_event возвращает строку-действие выбранного пункта или None.
"""

import pygame

from . import config as c

ITEM_FONT_SIZE = 26
TITLE_FONT_SIZE = 48


class Menu:
    def __init__(self):
        self.title_font = pygame.font.SysFont("Helvetica", TITLE_FONT_SIZE, bold=True)
        self.item_font = pygame.font.SysFont("Helvetica", ITEM_FONT_SIZE, bold=True)
        self.small_font = pygame.font.SysFont("Helvetica", 14)
        # (подпись, действие, активен ли)
        self.items = [
            ("Новая игра", "new_game", True),
            ("Загрузка", "load", False),
            ("Настройки", "settings", False),
            ("Выход", "quit", True),
        ]
        self.index = 0
        self.start_y = int(c.HEIGHT * 0.44)
        self.gap = 52

    # --- Геометрия пунктов (для мыши) ---
    def item_rects(self):
        rects = []
        for i in range(len(self.items)):
            rect = pygame.Rect(0, 0, 260, 40)
            rect.center = (c.WIDTH // 2, self.start_y + i * self.gap)
            rects.append(rect)
        return rects

    # --- Логика ---
    def _move(self, delta):
        self.index = (self.index + delta) % len(self.items)

    def _activate(self, i):
        _, action, active = self.items[i]
        return action if active else None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._move(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self._activate(self.index)
            elif event.key == pygame.K_ESCAPE:
                return "quit"
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.item_rects()):
                if rect.collidepoint(event.pos):
                    self.index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.item_rects()):
                if rect.collidepoint(event.pos):
                    self.index = i
                    return self._activate(i)
        return None

    # --- Отрисовка ---
    def draw(self, screen):
        screen.fill(c.BG_COLOR)

        title = self.title_font.render("BATTLE CITY", True, c.PLAYER_COLOR)
        screen.blit(title, (c.WIDTH // 2 - title.get_width() // 2, int(c.HEIGHT * 0.20)))
        sub = self.small_font.render("Tank 1990 · pygame", True, c.STEEL_COLOR)
        screen.blit(sub, (c.WIDTH // 2 - sub.get_width() // 2,
                          int(c.HEIGHT * 0.20) + title.get_height() + 6))

        for i, rect in enumerate(self.item_rects()):
            label, _, active = self.items[i]
            selected = (i == self.index)
            if not active:
                color = (110, 110, 110)         # заглушка — серый
            elif selected:
                color = c.ACCENT
            else:
                color = c.TEXT_COLOR

            surf = self.item_font.render(label, True, color)
            sx = rect.centerx - surf.get_width() // 2
            sy = rect.centery - surf.get_height() // 2
            screen.blit(surf, (sx, sy))

            # Маркер-стрелка у выбранного пункта (рисуем фигурой, не глифом)
            if selected:
                ty = rect.centery
                tx = sx - 22
                pygame.draw.polygon(
                    screen, color, [(tx, ty - 8), (tx + 13, ty), (tx, ty + 8)]
                )

        hint = self.small_font.render(
            "W/S или стрелки — выбор  ·  Enter — ОК  ·  Esc — выход",
            True, (150, 150, 150),
        )
        screen.blit(hint, (c.WIDTH // 2 - hint.get_width() // 2, int(c.HEIGHT * 0.88)))
