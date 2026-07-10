"""Pac-Man — точка входа и игровой цикл (Этапы 1–2 + часть 3).

Готово: меню с настройками (враги 1–4, сложность, звук, громкость) и рекордом;
лабиринт; Пакман; **4 призрака** с индивидуальным ИИ (Blinky/Pinky/Inky/Clyde),
режимы scatter/chase, испуг после энергайзера и съедание призраков; гибель и
Game Over. Настройки/рекорд — в save.json.

Запуск:  python main.py  (из каталога pacman)
Меню: ↑/↓ — пункт, ←/→ — значение, Enter — старт.
Игра: стрелки или WASD — движение, P — пауза, Esc — в меню.
"""

import random

import pygame

from src import config as c
from src import menu
from src import storage
from src.controls import Input
from src.sound import Synth
from src.world.maze import Maze
from src.world import levels
from src.entities.pacman import Pacman
from src.entities.ghost import Ghost, ROAM, LEAVE
from src.entities.fruit import Fruit, draw_icon

SPAWN = (13, 23)
TOTAL_DOTS = 280

MENU, READY, PLAY, PAUSE, CLEAR, DYING, GAMEOVER = range(7)


def draw_hud(screen, fonts, st):
    big, small = fonts
    screen.blit(small.render("1UP", True, c.TEXT), (c.TILE, 4))
    score = big.render(str(st["score"]), True, c.TEXT)
    screen.blit(score, (c.TILE, 4 + small.get_height()))
    screen.blit(small.render("HIGH SCORE", True, c.TEXT), (c.WIDTH // 2 - 60, 4))
    hi = big.render(str(st["high"]), True, c.TEXT)
    screen.blit(hi, (c.WIDTH // 2 - hi.get_width() // 2, 4 + small.get_height()))

    y = c.HUD_TOP + c.FIELD_H + c.HUD_BOTTOM // 2
    for i in range(st["lives"]):
        pygame.draw.circle(screen, c.PACMAN, (c.TILE + i * (c.TILE + 6), y), c.TILE // 2 - 2)
    lvl = small.render(f"LEVEL {st['level']}", True, c.TEXT)
    screen.blit(lvl, (c.WIDTH - lvl.get_width() - c.TILE, y - lvl.get_height() // 2))

    # собранные фрукты — справа от жизней (последние 7)
    fr = st["fruits_got"][-7:]
    x0 = c.WIDTH // 2 - len(fr) * (c.TILE + 4) // 2
    for i, idx in enumerate(fr):
        draw_icon(screen, x0 + i * (c.TILE + 4), y, idx, c.TILE // 2 - 3)


def center_msg(screen, font, text, color):
    msg = font.render(text, True, color)
    screen.blit(msg, (c.WIDTH // 2 - msg.get_width() // 2,
                      c.HUD_TOP + c.FIELD_H * 3 // 5))


def main():
    pygame.init()
    screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
    pygame.display.set_caption("Pac-Man")
    clock = pygame.time.Clock()
    fonts = (c.font(26), c.font(16))
    rng = random.Random()

    snd = Synth()
    saved = storage.load()
    snd.enabled = bool(saved["sound"])
    snd.volume = float(saved["volume"])

    inp = Input()
    st = {
        "score": 0, "high": int(saved["high"]), "lives": c.START_LIVES,
        "level": 1, "scene": MENU, "timer": 0, "sel": 0,
        "enemies": int(saved["enemies"]), "difficulty": int(saved["difficulty"]),
        "mode": c.SCATTER, "mode_left": 0, "fright_until": 0, "eat_chain": 0,
        "fruit_spawned": set(), "fruits_got": [], "extra_awarded": False,
    }
    maze = Maze()
    pac = Pacman(*SPAWN)
    ghosts = []
    fruit = Fruit()

    def params():
        return levels.params(st["level"], st["difficulty"])

    def spawn_ghosts():
        order = [c.BLINKY, c.PINKY, c.INKY, c.CLYDE][:st["enemies"]]
        return [Ghost(name) for name in order]

    def reset_actors():
        pac.reset(*SPAWN)
        for g in ghosts:
            g.reset()
        st["mode"] = c.SCATTER
        st["mode_left"] = params()["scatter_ms"]
        st["fright_until"] = 0
        st["eat_chain"] = 0
        inp.clear()

    def reset_level_items():
        fruit.active = False
        st["fruit_spawned"] = set()

    def persist():
        storage.save({"high": st["high"], "sound": snd.enabled, "volume": snd.volume,
                      "enemies": st["enemies"], "difficulty": st["difficulty"]})

    def start_ready():
        nonlocal ghosts
        ghosts = spawn_ghosts()
        reset_actors()
        st["scene"] = READY
        st["timer"] = pygame.time.get_ticks()
        snd.play("ready")

    def new_game():
        nonlocal maze
        maze = Maze()
        st.update(score=0, lives=c.START_LIVES, level=1,
                  fruits_got=[], extra_awarded=False)
        reset_level_items()
        start_ready()

    def next_level():
        nonlocal maze
        maze = Maze()
        st["level"] += 1
        reset_level_items()
        start_ready()

    def blinky_tile():
        for g in ghosts:
            if g.name == c.BLINKY:
                return g.tile()
        return pac.tile()

    # --- Меню ---
    def menu_adjust(row, step):
        if row == menu.ENEMIES:
            st["enemies"] = max(c.MIN_ENEMIES, min(c.MAX_ENEMIES, st["enemies"] + step))
        elif row == menu.DIFFICULTY:
            st["difficulty"] = (st["difficulty"] + step) % len(c.DIFF_NAMES)
        elif row == menu.SOUND:
            snd.toggle()
        elif row == menu.VOLUME:
            snd.set_volume(round(snd.volume + 0.1 * step, 2))
        snd.play("blip")
        persist()

    def menu_activate(row):
        if row == menu.PLAY:
            snd.play("select")
            new_game()
        elif row in menu.ADJUSTABLE:
            menu_adjust(row, 1)
        elif row == menu.QUIT:
            return False
        return True

    def lose_life():
        st["lives"] -= 1
        st["scene"] = DYING
        st["timer"] = pygame.time.get_ticks()
        snd.play("death")

    def update_modes(now, dt):
        """Scatter↔chase по таймеру; испуг замораживает таймер режима."""
        if now < st["fright_until"]:
            return                                  # во время испуга режим стоит
        if st["fright_until"]:                       # испуг только что кончился
            for g in ghosts:
                g.frightened = False
            st["fright_until"] = 0
            st["eat_chain"] = 0
        st["mode_left"] -= dt
        if st["mode_left"] <= 0:
            st["mode"] = c.CHASE if st["mode"] == c.SCATTER else c.SCATTER
            st["mode_left"] = params()["chase_ms" if st["mode"] == c.CHASE else "scatter_ms"]
            for g in ghosts:
                g.reverse()

    def eat_energizer(now):
        st["fright_until"] = now + params()["fright_ms"]
        st["eat_chain"] = 0
        for g in ghosts:
            if g.state == ROAM:
                g.frightened = True
                g.reverse()
        snd.play("fright")

    def check_collisions(now):
        thr = c.TILE * 0.6
        for g in ghosts:
            if not g.is_hittable():
                continue
            if abs(g.cx - pac.cx) < thr and abs(g.cy - pac.cy) < thr:
                if g.frightened:
                    pts = c.GHOST_EAT_POINTS[min(st["eat_chain"], 3)]
                    st["score"] += pts
                    st["eat_chain"] += 1
                    g.eaten()
                    snd.play("eatghost")
                else:
                    lose_life()
                    return

    running = True
    while running:
        now = pygame.time.get_ticks()
        dt = clock.get_time()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif st["scene"] == MENU and e.type == pygame.KEYDOWN:
                row = menu.ROWS[st["sel"]]
                if e.key in (pygame.K_UP, pygame.K_w):
                    st["sel"] = (st["sel"] - 1) % len(menu.ROWS); snd.play("blip")
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    st["sel"] = (st["sel"] + 1) % len(menu.ROWS); snd.play("blip")
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    menu_adjust(row, -1)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    menu_adjust(row, +1)
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    running = menu_activate(row)
                elif e.key == pygame.K_ESCAPE:
                    running = False
            elif st["scene"] == GAMEOVER and e.type == pygame.KEYDOWN:
                st["scene"] = MENU
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                st["scene"] = MENU
                inp.clear()
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_p and st["scene"] in (PLAY, PAUSE):
                st["scene"] = PAUSE if st["scene"] == PLAY else PLAY
            else:
                inp.handle(e)

        # --- Обновление ----------------------------------------------------
        if st["scene"] == READY:
            if now - st["timer"] >= c.READY_MS:
                st["scene"] = PLAY
        elif st["scene"] == PLAY:
            p = params()
            pac.want_dir = inp.direction()
            gained = pac.update(maze, p["pac_speed"])
            if gained == c.PTS_ENERGIZER:
                eat_energizer(now)
            elif gained == c.PTS_DOT:
                snd.munch()
            st["score"] += gained

            # выпуск призраков по числу съеденных точек
            eaten = TOTAL_DOTS - maze.dots_left
            for g in ghosts:
                if eaten >= c.GHOST_RELEASE_DOTS[g.name]:
                    g.release()

            # появление фрукта после порогов съеденных точек
            for thr in c.FRUIT_DOTS:
                if eaten >= thr and thr not in st["fruit_spawned"]:
                    st["fruit_spawned"].add(thr)
                    fruit.spawn(st["level"], now)
            fruit.update(now)
            fpts = fruit.eat(pac.tile())
            if fpts:
                st["score"] += fpts
                st["fruits_got"].append(fruit.idx)
                snd.play("fruit")

            # экстра-жизнь на пороге очков (один раз)
            if not st["extra_awarded"] and st["score"] >= c.EXTRA_LIFE_AT:
                st["extra_awarded"] = True
                st["lives"] += 1
                snd.play("extra")

            st["high"] = max(st["high"], st["score"])

            update_modes(now, dt)
            pt, pd = pac.tile(), pac.dir
            bt = blinky_tile()
            for g in ghosts:
                g.update(maze, pt, pd, bt, st["mode"], p["ghost_speed"], rng)

            check_collisions(now)
            if st["scene"] == PLAY and maze.cleared():
                st["scene"] = CLEAR
                st["timer"] = now
                snd.play("level")
                persist()
        elif st["scene"] == CLEAR:
            if now - st["timer"] >= c.LEVEL_CLEAR_MS:
                next_level()
        elif st["scene"] == DYING:
            if now - st["timer"] >= c.DEATH_MS:
                if st["lives"] > 0:
                    reset_actors()
                    st["scene"] = READY
                    st["timer"] = now
                else:
                    st["scene"] = GAMEOVER
                    st["timer"] = now
                    persist()
        elif st["scene"] == GAMEOVER:
            if now - st["timer"] >= c.GAMEOVER_MS:
                st["scene"] = MENU

        # --- Отрисовка -----------------------------------------------------
        if st["scene"] == MENU:
            view = {"high": st["high"], "enemies": st["enemies"],
                    "difficulty": st["difficulty"], "sound_on": snd.enabled,
                    "volume": snd.volume}
            menu.draw(screen, fonts, st["sel"], view, now)
            pygame.display.flip()
            clock.tick(c.FPS)
            continue

        screen.fill(c.BLACK)
        blink = (now // 200) % 2 == 0
        maze_blink = st["scene"] != CLEAR or (now // 150) % 2 == 0
        if maze_blink:
            maze.draw(screen, c.HUD_TOP, blink=blink)

        if st["scene"] != DYING:
            fruit.draw(screen, c.HUD_TOP)
        if st["scene"] != DYING:
            pac.draw(screen, c.HUD_TOP)
        flash = st["fright_until"] and (st["fright_until"] - now) < 2000 and (now // 200) % 2 == 0
        if st["scene"] not in (DYING,):
            for g in ghosts:
                g.draw(screen, c.HUD_TOP, flash=flash)
        draw_hud(screen, fonts, st)

        if st["scene"] == READY:
            center_msg(screen, fonts[0], "READY!", c.READY_COLOR)
        elif st["scene"] == PAUSE:
            center_msg(screen, fonts[0], "ПАУЗА", c.READY_COLOR)
        elif st["scene"] == DYING:
            pac.draw(screen, c.HUD_TOP)      # Пакман на месте гибели
        elif st["scene"] == GAMEOVER:
            center_msg(screen, fonts[0], "GAME OVER", c.GAMEOVER_COLOR)

        pygame.display.flip()
        clock.tick(c.FPS)

    persist()
    pygame.quit()


if __name__ == "__main__":
    main()
