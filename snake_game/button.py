"""Простая кликабельная кнопка для интерфейса."""

import pygame

from config import BTN_COLOR, BTN_HOVER, TEXT_COLOR


class Button:
    def __init__(self, rect, label, callback, text_color=TEXT_COLOR):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.text_color = text_color

    def draw(self, screen, font, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        pygame.draw.rect(
            screen, BTN_HOVER if hover else BTN_COLOR, self.rect,
            border_radius=6,
        )
        text = font.render(self.label, True, self.text_color)
        screen.blit(text, (
            self.rect.centerx - text.get_width() // 2,
            self.rect.centery - text.get_height() // 2,
        ))

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()
            return True
        return False
