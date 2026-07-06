"""Bomberman на pygame — точка входа.

Пока это временное превью (Этап 1): арена + управляемый игрок. По мере
готовности `src/game.py` заменит предпросмотр полноценным игровым циклом.

Запуск (из каталога bomberman):
    python main.py

    Движение — WASD или стрелки (работает при любой раскладке: RUS/ENG/…)
    R   — перегенерировать арену
    Esc — выход
"""

import pygame

from src import config as c
from src.controls import Input, SCAN_R
from src.entities.player import Player
from src.world.arena import Arena


def main():
    pygame.init()
    screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
    pygame.display.set_caption("Bomberman — превью (Этап 1)")
    font = pygame.font.SysFont("Helvetica", 15, bold=True)
    small = pygame.font.SysFont("Helvetica", 13)
    clock = pygame.time.Clock()

    seed = 0
    arena = Arena(seed=seed)
    player = Player(*arena.spawns[0], index=0)
    controls = Input()

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            # R по scancode — работает и на RUS-раскладке
            elif e.type == pygame.KEYDOWN and e.scancode == SCAN_R:
                seed += 1
                arena.generate(seed)
                player.place_at_cell(*arena.spawns[0])
                controls.clear()
            controls.handle(e)

        # Движение каждый кадр по текущему направлению
        player.try_move(arena, controls.direction())

        # --- Отрисовка ---
        screen.fill(c.BG_COLOR)
        arena.draw(screen)
        # Прочие стартовые углы — метки
        for i, (col, row) in enumerate(arena.spawns[1:], start=2):
            cx, cy = arena.cell_center(col, row)
            pygame.draw.circle(screen, c.ACCENT, (cx, cy), 6, 2)
            lbl = small.render(str(i), True, c.WHITE)
            screen.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))
        player.draw(screen)

        # Правая панель
        x = c.FIELD_W
        pygame.draw.rect(screen, c.HUD_BG, (x, 0, c.HUD_W, c.HEIGHT))
        screen.blit(font.render("BOMBERMAN", True, c.HUD_TEXT), (x + 14, 16))
        info = [
            "Превью: арена + игрок",
            f"Сетка {c.COLS}x{c.ROWS}",
            f"Клетка: {player.cell}",
            "",
            "WASD / стрелки",
            "(любая раскладка)",
            "R — заново",
            "Esc — выход",
        ]
        y = 52
        for line in info:
            screen.blit(small.render(line, True, c.HUD_TEXT), (x + 14, y))
            y += 22

        pygame.display.flip()
        clock.tick(c.FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
