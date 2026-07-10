"""Главное меню: заголовок с тенью, «команда» героев, панель пунктов.

Навигация — стрелки ↑/↓ (пункт), ←/→ (значение), Enter (действие); коды этих
клавиш не зависят от раскладки. Состояние держит игровой цикл, здесь — только
отрисовка. Всё процедурно (pygame.draw), без ассетов.
"""

import math

import pygame

from . import config as c

# Пункты меню
PLAY, MODE, MAZE, ENEMIES, DIFFICULTY, SOUND, VOLUME, QUIT = range(8)
ROWS = [PLAY, MODE, MAZE, ENEMIES, DIFFICULTY, SOUND, VOLUME, QUIT]
LABELS = {
    PLAY: "ИГРАТЬ", MODE: "РЕЖИМ", MAZE: "ЛАБИРИНТ", ENEMIES: "ВРАГИ",
    DIFFICULTY: "СЛОЖНОСТЬ", SOUND: "ЗВУК", VOLUME: "ГРОМКОСТЬ", QUIT: "ВЫХОД",
}
ADJUSTABLE = (MODE, MAZE, ENEMIES, DIFFICULTY, SOUND, VOLUME)
ACTIONS = (PLAY, QUIT)

# Оттенки для «спокойного» тёмно-синего оформления
PANEL_BG = (16, 16, 38, 235)
PANEL_EDGE = (60, 60, 170)
HILITE = (255, 255, 0, 26)
DIM = (150, 152, 175)
BORDER_DOT = (55, 55, 90)


def _value_text(row, st):
    if row == MODE:
        return "MS. PACMAN" if st["ms_mode"] else "PAC-MAN"
    if row == MAZE:
        return "СЛУЧАЙНО" if st["maze_choice"] == 0 else str(st["maze_choice"])
    if row == ENEMIES:
        return str(st["enemies"])
    if row == DIFFICULTY:
        return c.DIFF_NAMES[st["difficulty"]]
    if row == SOUND:
        return "ВКЛ" if st["sound_on"] else "ВЫКЛ"
    if row == VOLUME:
        return f"{int(round(st['volume'] * 100))}%"
    return None


def _pacman(surface, cx, cy, r, now, color=c.PACMAN):
    half = 6 + 26 * (0.5 + 0.5 * math.sin(now * 0.008))
    pygame.draw.circle(surface, color, (cx, cy), r)
    pts = [(cx, cy)]
    for i in range(11):
        a = math.radians(-half + 2 * half * i / 10)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(surface, c.BLACK, pts)


def _mini_ghost(surface, cx, cy, r, color, phase):
    pygame.draw.circle(surface, color, (cx, cy - 2), r)
    pygame.draw.rect(surface, color, (cx - r, cy - 2, 2 * r, r))
    step = (2 * r) // 3
    for i in range(3):
        x = cx - r + i * step
        base = cy + r - 2 + (2 if (i % 2) else 0)
        pygame.draw.polygon(surface, color,
                            [(x, base), (x + step // 2, cy + r - 6), (x + step, base)])
    look = int(2 * math.sin(phase))
    for ex in (cx - r // 2, cx + r // 2):
        pygame.draw.circle(surface, c.EYE_WHITE, (ex, cy - 2), r // 3 + 1)
        pygame.draw.circle(surface, c.EYE_IRIS, (ex + look, cy - 1), 2)


def draw(screen, fonts, sel, st, now):
    big, small = fonts
    screen.fill(c.BLACK)

    # Точечная рамка сверху/снизу — как в аркадном аттракте
    for x in range(24, c.WIDTH - 12, 24):
        pygame.draw.circle(screen, BORDER_DOT, (x, 16), 2)
        pygame.draw.circle(screen, BORDER_DOT, (x, c.HEIGHT - 16), 2)

    # Заголовок с синей тенью
    tf = c.font(66)
    shadow = tf.render("PAC-MAN", True, c.WALL)
    title = tf.render("PAC-MAN", True, c.PACMAN)
    tx = c.WIDTH // 2 - title.get_width() // 2
    screen.blit(shadow, (tx + 3, 42 + 4))
    screen.blit(title, (tx, 42))

    # «Команда»: Пакман гонится за дорожкой точек, следом 4 призрака
    y = 150
    lead = c.WIDTH // 2 - 116
    for k in range(1, 4):
        pygame.draw.circle(screen, c.DOT, (lead - 20 - k * 15, y), 3)
    _pacman(screen, lead, y, 18, now)
    for k, name in enumerate((c.BLINKY, c.PINKY, c.INKY, c.CLYDE)):
        _mini_ghost(screen, lead + 50 + k * 46, y, 15, c.GHOST_COLORS[name], now * 0.02 + k)

    hs = small.render(f"HIGH SCORE   {st['high']}", True, (224, 224, 168))
    screen.blit(hs, (c.WIDTH // 2 - hs.get_width() // 2, 196))

    # Панель пунктов
    px = 92
    pw = c.WIDTH - 2 * px
    row_h = 52
    pad = 18
    ptop = 232
    ph = pad * 2 + len(ROWS) * row_h
    panel = pygame.Rect(px, ptop, pw, ph)
    bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
    bg.fill(PANEL_BG)
    screen.blit(bg, (px, ptop))
    pygame.draw.rect(screen, PANEL_EDGE, panel, width=3, border_radius=18)

    for i, row in enumerate(ROWS):
        active = i == sel
        ry = ptop + pad + i * row_h
        cy = ry + row_h // 2
        color = c.PACMAN if active else c.TEXT

        if active:                                    # плашка выделения
            rr = pygame.Rect(px + 12, ry + 5, pw - 24, row_h - 10)
            hi = pygame.Surface((rr.w, rr.h), pygame.SRCALPHA)
            hi.fill(HILITE)
            screen.blit(hi, (rr.x, rr.y))
            pygame.draw.rect(screen, c.PACMAN, rr, width=2, border_radius=12)
            _pacman(screen, px + 34, cy, 9, now)      # маркер-Пакман

        label = big.render(LABELS[row], True, color)
        val = _value_text(row, st)
        if row in ACTIONS:
            screen.blit(label, (c.WIDTH // 2 - label.get_width() // 2, cy - label.get_height() // 2))
        else:
            screen.blit(label, (px + 54, cy - label.get_height() // 2))
            vs = big.render(val, True, color)
            vx = px + pw - 52 - vs.get_width()
            screen.blit(vs, (vx, cy - vs.get_height() // 2))
            if active:                                # стрелки-подсказки ‹ ›
                lt = big.render("‹", True, c.PACMAN)
                rt = big.render("›", True, c.PACMAN)
                screen.blit(lt, (vx - 24, cy - lt.get_height() // 2))
                screen.blit(rt, (px + pw - 30, cy - rt.get_height() // 2))

    hint = small.render("↑↓ — пункт     ←→ — значение     Enter — старт", True, DIM)
    screen.blit(hint, (c.WIDTH // 2 - hint.get_width() // 2, c.HEIGHT - 42))
