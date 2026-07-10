"""Pac-Man — точка входа и игровой цикл (Этап 1).

Готово: лабиринт, движение Пакмана с буфером поворота и тоннелем, поедание
точек/энергайзеров, счёт, жизни, экраны READY!/зачистки уровня. Призраки —
следующий этап. Запуск:  python main.py  (из каталога pacman).

Управление: стрелки или WASD — движение, P — пауза, Esc — выход.
"""

import pygame

from src import config as c
from src.controls import Input
from src.world.maze import Maze
from src.entities.pacman import Pacman

SPAWN = (13, 23)               # старт Пакмана (низ по центру)

READY, PLAY, CLEAR = range(3)


def draw_hud(screen, fonts, st):
    """Верх — счёт/рекорд, низ — жизни и номер уровня."""
    big, small = fonts
    # Верхняя панель
    screen.blit(small.render("1UP", True, c.TEXT), (c.TILE, 4))
    score = big.render(str(st["score"]), True, c.TEXT)
    screen.blit(score, (c.TILE, 4 + small.get_height()))
    screen.blit(small.render("HIGH SCORE", True, c.TEXT),
                (c.WIDTH // 2 - 60, 4))
    hi = big.render(str(st["high"]), True, c.TEXT)
    screen.blit(hi, (c.WIDTH // 2 - hi.get_width() // 2, 4 + small.get_height()))

    # Нижняя панель — жизни жёлтыми кружками
    y = c.HUD_TOP + c.FIELD_H + c.HUD_BOTTOM // 2
    for i in range(st["lives"]):
        pygame.draw.circle(screen, c.PACMAN, (c.TILE + i * (c.TILE + 6), y), c.TILE // 2 - 2)
    lvl = small.render(f"LEVEL {st['level']}", True, c.TEXT)
    screen.blit(lvl, (c.WIDTH - lvl.get_width() - c.TILE, y - lvl.get_height() // 2))


def main():
    pygame.init()
    screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
    pygame.display.set_caption("Pac-Man")
    clock = pygame.time.Clock()
    fonts = (pygame.font.SysFont("consolas", 26, bold=True),
             pygame.font.SysFont("consolas", 16, bold=True))

    inp = Input()
    st = {
        "score": 0, "high": 0, "lives": c.START_LIVES, "level": 1,
        "scene": READY, "timer": pygame.time.get_ticks(),
    }
    maze = Maze()
    pac = Pacman(*SPAWN)

    def new_level():
        nonlocal maze
        maze = Maze()
        pac.reset(*SPAWN)
        inp.clear()
        st["scene"] = READY
        st["timer"] = pygame.time.get_ticks()

    running = True
    while running:
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            else:
                inp.handle(e)

        # --- Обновление ----------------------------------------------------
        if st["scene"] == READY:
            if now - st["timer"] >= c.READY_MS:
                st["scene"] = PLAY
        elif st["scene"] == PLAY:
            d = inp.direction()
            if d:
                pac.want_dir = d
            st["score"] += pac.update(maze)
            st["high"] = max(st["high"], st["score"])
            if maze.cleared():
                st["scene"] = CLEAR
                st["timer"] = now
        elif st["scene"] == CLEAR:
            if now - st["timer"] >= c.LEVEL_CLEAR_MS:
                st["level"] += 1
                new_level()

        # --- Отрисовка -----------------------------------------------------
        screen.fill(c.BLACK)
        blink = (now // 200) % 2 == 0
        maze_blink = st["scene"] != CLEAR or (now // 150) % 2 == 0
        if maze_blink:
            maze.draw(screen, c.HUD_TOP, blink=blink)
        pac.draw(screen, c.HUD_TOP)
        draw_hud(screen, fonts, st)

        if st["scene"] == READY:
            msg = fonts[0].render("READY!", True, c.READY_COLOR)
            screen.blit(msg, (c.WIDTH // 2 - msg.get_width() // 2,
                              c.HUD_TOP + c.FIELD_H * 3 // 5))

        pygame.display.flip()
        clock.tick(c.FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
