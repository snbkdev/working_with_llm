"""Простая кликабельная кнопка для интерфейса."""

import pygame

from config import ACCENT_COLOR, BTN_COLOR, BTN_HOVER, TEXT_COLOR


class Button:
    def __init__(self, rect, label, callback, text_color=TEXT_COLOR):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.text_color = text_color
        self.selected = False  # подсветка выбранного варианта (переключатели)

    def draw(self, screen, font, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        pygame.draw.rect(
            screen, BTN_HOVER if hover else BTN_COLOR, self.rect,
            border_radius=6,
        )
        if self.selected:
            pygame.draw.rect(
                screen, ACCENT_COLOR, self.rect, 2, border_radius=6
            )
        color = ACCENT_COLOR if self.selected else self.text_color
        text = font.render(self.label, True, color)
        screen.blit(text, (
            self.rect.centerx - text.get_width() // 2,
            self.rect.centery - text.get_height() // 2,
        ))

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()
            return True
        return False
