"""Главное меню: заголовок, пункты-настройки, анимированный Пакман, рекорд.

Навигация — стрелки ↑/↓ (выбор пункта), ←/→ (менять значение), Enter (действие).
Коды этих клавиш не зависят от раскладки. Состояние выбора и значений держит
игровой цикл; здесь только отрисовка.
"""

import math

import pygame

from . import config as c

# Пункты меню
PLAY, ENEMIES, DIFFICULTY, SOUND, VOLUME, QUIT = range(6)
ROWS = [PLAY, ENEMIES, DIFFICULTY, SOUND, VOLUME, QUIT]
LABELS = {
    PLAY: "ИГРАТЬ", ENEMIES: "ВРАГИ", DIFFICULTY: "СЛОЖНОСТЬ",
    SOUND: "ЗВУК", VOLUME: "ГРОМКОСТЬ", QUIT: "ВЫХОД",
}
ADJUSTABLE = (ENEMIES, DIFFICULTY, SOUND, VOLUME)


def _row_text(row, st):
    if row == ENEMIES:
        return f"{LABELS[row]}   {st['enemies']}"
    if row == DIFFICULTY:
        return f"{LABELS[row]}   {c.DIFF_NAMES[st['difficulty']]}"
    if row == SOUND:
        return f"{LABELS[row]}   {'ВКЛ' if st['sound_on'] else 'ВЫКЛ'}"
    if row == VOLUME:
        return f"{LABELS[row]}   {int(round(st['volume'] * 100))}%"
    return LABELS[row]


def draw(screen, fonts, sel, st, now):
    """`st` — словарь с ключами high, enemies, difficulty, sound_on, volume."""
    big, small = fonts
    screen.fill(c.BLACK)

    title = c.font(58).render("PAC-MAN", True, c.PACMAN)
    screen.blit(title, (c.WIDTH // 2 - title.get_width() // 2, 40))

    # Анимированный Пакман с дорожкой точек
    cx, cy, r = c.WIDTH // 2, 150, 28
    half = 5 + 30 * (0.5 + 0.5 * math.sin(now * 0.006))
    pygame.draw.circle(screen, c.PACMAN, (cx, cy), r)
    pts = [(cx, cy)]
    for i in range(13):
        a = math.radians(-half + (2 * half) * i / 12)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(screen, c.BLACK, pts)
    for k in range(1, 5):
        pygame.draw.circle(screen, c.DOT, (cx + r + 16 * k, cy), 4)

    hi = small.render(f"HIGH SCORE   {st['high']}", True, c.TEXT)
    screen.blit(hi, (c.WIDTH // 2 - hi.get_width() // 2, 210))

    # Пункты
    base_y = 260
    for i, row in enumerate(ROWS):
        active = i == sel
        color = c.PACMAN if active else c.TEXT
        text = _row_text(row, st)
        if active and row in ADJUSTABLE:
            text = "‹ " + text + " ›"
        label = big.render(text, True, color)
        x = c.WIDTH // 2 - label.get_width() // 2
        y = base_y + i * 48
        screen.blit(label, (x, y))
        if active:
            pygame.draw.circle(screen, c.PACMAN, (x - 22, y + label.get_height() // 2), 8)

    hint = small.render("↑↓ — пункт,  ←→ — значение,  Enter — старт", True, c.TEXT)
    screen.blit(hint, (c.WIDTH // 2 - hint.get_width() // 2, c.HEIGHT - 44))
