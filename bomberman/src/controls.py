"""Ввод, независимый от раскладки клавиатуры (RUS/ENG/DE/…).

`pygame.key.get_pressed()` индексируется keycode'ами, а те зависят от
раскладки: на русской раскладке физическая клавиша W даёт 'ц', и `K_w`
не срабатывает. Поэтому движение берём по **scancode** — это физическая
позиция клавиши, одинаковая при любой раскладке.

Поддержаны две схемы для двух игроков за одной клавиатурой:
  • P1 — WASD (+ пробел бомба, E детонатор),
  • P2 — стрелки (+ правый Ctrl бомба, правый Shift детонатор).
`Input(scheme)` держит зажатые клавиши своей схемы; на перекрёстке
приоритетна последняя нажатая.
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
SCAN_R = _scan("R", 21)
SCAN_E = _scan("E", 8)          # детонатор P1 (ручной подрыв)
SCAN_LSHIFT = _scan("LSHIFT", 225)   # прыжок P1

# Схемы движения по физическим позициям клавиш
SCHEME_WASD = {SCAN_W: c.UP, SCAN_S: c.DOWN, SCAN_A: c.LEFT, SCAN_D: c.RIGHT}
SCHEME_ARROWS = {SCAN_UP: c.UP, SCAN_DOWN: c.DOWN, SCAN_LEFT: c.LEFT, SCAN_RIGHT: c.RIGHT}
SCHEME_BOTH = {**SCHEME_WASD, **SCHEME_ARROWS}     # для одиночного режима


class Input:
    """Отслеживает зажатые клавиши движения одной схемы (для одного игрока)."""

    def __init__(self, scheme=None):
        self.scheme = scheme if scheme is not None else SCHEME_BOTH
        self._held = []          # scancode'ы в порядке нажатия

    def handle(self, e):
        """Скармливать сюда события клавиатуры из цикла."""
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
