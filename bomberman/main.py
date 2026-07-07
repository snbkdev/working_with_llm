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
from src.entities.bomb import Bomb, can_place
from src.entities.explosion import Explosion
from src.entities.player import Player
from src.world.arena import Arena


def make_bomb_icon():
    """Иконка окна — классическая бомбочка с фитилём (вместо змейки pygame)."""
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    cx, cy, r = 15, 19, 11
    pygame.draw.circle(icon, (30, 32, 40), (cx, cy), r)          # тело
    pygame.draw.circle(icon, (12, 12, 16), (cx, cy), r, 2)       # контур
    pygame.draw.circle(icon, (120, 128, 150), (cx - 4, cy - 4), 3)  # блик
    pygame.draw.rect(icon, (90, 92, 100), (cx - 3, cy - r - 3, 6, 5), border_radius=1)  # колпачок
    pygame.draw.lines(icon, (200, 170, 90), False,              # фитиль
                      [(cx + 1, cy - r - 2), (cx + 5, cy - r - 6), (cx + 2, cy - r - 9)], 2)
    pygame.draw.circle(icon, (250, 220, 90), (cx + 2, cy - r - 10), 4)   # искра
    pygame.draw.circle(icon, (250, 140, 40), (cx + 2, cy - r - 10), 2)
    return icon


def main():
    pygame.init()
    screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
    pygame.display.set_icon(make_bomb_icon())
    pygame.display.set_caption("Bomberman — превью (Этап 1)")
    font = pygame.font.SysFont("Helvetica", 15, bold=True)
    small = pygame.font.SysFont("Helvetica", 13)
    clock = pygame.time.Clock()

    seed = 0
    arena = Arena(seed=seed)
    player = Player(*arena.spawns[0], index=0)
    controls = Input()
    bombs = []
    explosions = []

    running = True
    while running:
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                # Пробел (одинаков в любой раскладке) — поставить бомбу
                cell = player.cell
                if can_place(bombs, cell, player.index, player.max_bombs):
                    bombs.append(Bomb(*cell, owner=player.index,
                                      fire=player.fire, now=now))
            # R по scancode — работает и на RUS-раскладке
            elif e.type == pygame.KEYDOWN and e.scancode == SCAN_R:
                seed += 1
                arena.generate(seed)
                player.place_at_cell(*arena.spawns[0])
                controls.clear()
                bombs.clear()
                explosions.clear()
            controls.handle(e)

        # Движение каждый кадр по текущему направлению
        player.try_move(arena, controls.direction())

        # Фитили тикают; догоревшая бомба рождает крестообразное пламя
        for b in bombs:
            if b.update(now):
                explosions.append(Explosion(arena, b.col, b.row, b.fire, now))
        bombs = [b for b in bombs if not b.exploded]

        # Пламя живёт недолго, затем гаснет
        for ex in explosions:
            ex.update(now)
        explosions = [ex for ex in explosions if not ex.done]

        # --- Отрисовка ---
        screen.fill(c.BG_COLOR)
        arena.draw(screen)
        for b in bombs:
            b.draw(screen, now)
        for ex in explosions:
            ex.draw(screen, now)
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
            "Превью: арена+игрок",
            f"Сетка {c.COLS}x{c.ROWS}",
            f"Клетка: {player.cell}",
            f"Бомб: {len(bombs)}/{player.max_bombs}",
            "",
            "WASD / стрелки",
            "(любая раскладка)",
            "Пробел — бомба",
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
