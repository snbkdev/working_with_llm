"""Ввод, независимый от раскладки клавиатуры (RUS/ENG/DE/…).

`pygame.key.get_pressed()` индексируется keycode'ами, а те зависят от
раскладки: на русской раскладке физическая клавиша W даёт 'ц', и `K_w` не
срабатывает. Поэтому направление берём по **scancode** — физической позиции
клавиши, одинаковой при любой раскладке. Управляем стрелками или WASD.
"""

import pygame

from . import config as c


def _scan(name, default):
    """Скан-код клавиши: pygame.KSCAN_<name>, иначе стабильный SDL-код."""
    return getattr(pygame, "KSCAN_" + name, default)


# Стандартные SDL-скан-коды (значения зафиксированы в SDL/USB HID)
SCAN_W, SCAN_A, SCAN_S, SCAN_D = _scan("W", 26), _scan("A", 4), _scan("S", 22), _scan("D", 7)
SCAN_UP, SCAN_DOWN = _scan("UP", 82), _scan("DOWN", 81)
SCAN_LEFT, SCAN_RIGHT = _scan("LEFT", 80), _scan("RIGHT", 79)

# Обе схемы сразу — один игрок ходит и стрелками, и WASD
SCHEME = {
    SCAN_W: c.UP, SCAN_S: c.DOWN, SCAN_A: c.LEFT, SCAN_D: c.RIGHT,
    SCAN_UP: c.UP, SCAN_DOWN: c.DOWN, SCAN_LEFT: c.LEFT, SCAN_RIGHT: c.RIGHT,
}


class Input:
    """Отслеживает зажатые клавиши движения; на перекрёстке — последняя нажатая."""

    def __init__(self, scheme=None):
        self.scheme = scheme if scheme is not None else SCHEME
        self._held = []          # scancode'ы в порядке нажатия

    def handle(self, e):
        """Скармливать сюда события клавиатуры из игрового цикла."""
        sc = getattr(e, "scancode", None)     # у не-клавиатурных событий его нет
        if sc is None:
            return
        if e.type == pygame.KEYDOWN:
            if sc in self.scheme and sc not in self._held:
                self._held.append(sc)
        elif e.type == pygame.KEYUP:
            if sc in self._held:
                self._held.remove(sc)

    def direction(self):
        """Текущее направление (последняя зажатая клавиша) или None."""
        if self._held:
            return self.scheme[self._held[-1]]
        return None

    def clear(self):
        self._held.clear()
