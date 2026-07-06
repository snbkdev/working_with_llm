"""Ввод, независимый от раскладки клавиатуры (RUS/ENG/DE/…).

`pygame.key.get_pressed()` индексируется keycode'ами, а те зависят от
раскладки: на русской раскладке физическая клавиша W даёт 'ц', и `K_w`
не срабатывает. Поэтому движение берём по **scancode** — это физическая
позиция клавиши, одинаковая при любой раскладке (в pygame 2 `event.scancode`
возвращает SDL-скан-код по позиции на стандартной US-раскладке).

Держим нажатые scancode'ы в порядке нажатия и отдаём направление последней
актуальной клавиши (на перекрёстке приоритетна последняя нажатая). Поддержаны
обе схемы сразу: WASD и стрелки.
"""

import pygame

from . import config as c


def _scan(name, default):
    """Скан-код клавиши: pygame.KSCAN_<name>, а если его нет — стабильный
    SDL-код (USB HID). event.scancode в pygame 2 совпадает с этими значениями."""
    return getattr(pygame, "KSCAN_" + name, default)


# Стандартные SDL-скан-коды (значения зафиксированы в SDL/USB HID)
SCAN_W, SCAN_A, SCAN_S, SCAN_D = _scan("W", 26), _scan("A", 4), _scan("S", 22), _scan("D", 7)
SCAN_UP, SCAN_DOWN = _scan("UP", 82), _scan("DOWN", 81)
SCAN_LEFT, SCAN_RIGHT = _scan("LEFT", 80), _scan("RIGHT", 79)
SCAN_R = _scan("R", 21)

# Физическая позиция клавиши (scancode) → направление
SCAN_DIR = {
    SCAN_W: c.UP, SCAN_UP: c.UP,
    SCAN_S: c.DOWN, SCAN_DOWN: c.DOWN,
    SCAN_A: c.LEFT, SCAN_LEFT: c.LEFT,
    SCAN_D: c.RIGHT, SCAN_RIGHT: c.RIGHT,
}


class Input:
    """Отслеживает зажатые клавиши движения по их физической позиции."""

    def __init__(self):
        self._held = []          # scancode'ы в порядке нажатия

    def handle(self, e):
        """Скармливать сюда события клавиатуры из цикла."""
        if e.type == pygame.KEYDOWN:
            if e.scancode in SCAN_DIR and e.scancode not in self._held:
                self._held.append(e.scancode)
        elif e.type == pygame.KEYUP:
            if e.scancode in self._held:
                self._held.remove(e.scancode)

    def direction(self):
        """Текущее направление (последняя зажатая клавиша) или None."""
        if self._held:
            return SCAN_DIR[self._held[-1]]
        return None

    def clear(self):
        self._held.clear()
