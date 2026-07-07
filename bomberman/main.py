"""Bomberman на pygame — точка входа.

Пока это временное превью (Этапы 1–4): арена, игрок, бомбы с крестообразным
взрывом, цепные детонации, бонусы/проклятия и ИИ-боты в режиме «последний
выживший». По мере готовности `src/game.py` заменит предпросмотр полноценным
игровым циклом.

Запуск (из каталога bomberman):
    python main.py

    Движение — WASD или стрелки (работает при любой раскладке: RUS/ENG/…)
    Пробел — бомба, E — детонатор (с бонусом)
    1/2/3 — сложность ботов, [ и ] — число ботов, R — заново, Esc — выход
"""

import pygame

from src import config as c
from src.controls import Input, SCAN_E, SCAN_R
from src.entities.bomb import Bomb, can_place
from src.entities.bot import Bot
from src.entities.explosion import detonate_chain
from src.entities.player import Player
from src.entities.powerup import PowerUp, pickup, render_badge
from src.world.arena import Arena


def make_bomb_icon():
    """Иконка окна — классическая бомбочка с фитилём (вместо змейки pygame)."""
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    cx, cy, r = 15, 19, 11
    pygame.draw.circle(icon, (30, 32, 40), (cx, cy), r)
    pygame.draw.circle(icon, (12, 12, 16), (cx, cy), r, 2)
    pygame.draw.circle(icon, (120, 128, 150), (cx - 4, cy - 4), 3)
    pygame.draw.rect(icon, (90, 92, 100), (cx - 3, cy - r - 3, 6, 5), border_radius=1)
    pygame.draw.lines(icon, (200, 170, 90), False,
                      [(cx + 1, cy - r - 2), (cx + 5, cy - r - 6), (cx + 2, cy - r - 9)], 2)
    pygame.draw.circle(icon, (250, 220, 90), (cx + 2, cy - r - 10), 4)
    pygame.draw.circle(icon, (250, 140, 40), (cx + 2, cy - r - 10), 2)
    return icon


def main():
    pygame.init()
    screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
    pygame.display.set_icon(make_bomb_icon())
    pygame.display.set_caption("Bomberman — превью (Этапы 1–4)")
    font = pygame.font.SysFont("Helvetica", 15, bold=True)
    small = pygame.font.SysFont("Helvetica", 13)
    tiny = pygame.font.SysFont("Helvetica", 12, bold=True)
    big = pygame.font.SysFont("Helvetica", 34, bold=True)
    clock = pygame.time.Clock()

    state = {
        "seed": 0,
        "bots": c.DEFAULT_BOTS,
        "difficulty": c.DEFAULT_DIFFICULTY,
        "round_start": 0,
        "over_at": None,          # когда раунд завершился (для паузы)
        "winner": None,
        "wins": 0,                # победы игрока за сессию
    }
    arena = Arena(seed=state["seed"])
    player = Player(*arena.spawns[0], index=0)
    controls = Input()
    fighters = [player]
    bombs = []
    explosions = []
    powerups = []
    last_autobomb = 0

    def spawn_round():
        """Готовит новый раунд: раскладка, игрок и боты по углам, всё чисто."""
        arena.generate(state["seed"])
        player.respawn(*arena.spawns[0])
        fighters[:] = [player]
        for i in range(min(state["bots"], len(arena.spawns) - 1)):
            col, row = arena.spawns[i + 1]
            fighters.append(Bot(col, row, index=i + 1,
                                difficulty=state["difficulty"],
                                seed=state["seed"] * 10 + i))
        controls.clear()
        bombs.clear()
        explosions.clear()
        powerups.clear()
        state["round_start"] = pygame.time.get_ticks()
        state["over_at"] = None
        state["winner"] = None

    def new_round(next_seed=True):
        if next_seed:
            state["seed"] += 1
        spawn_round()

    def place_bomb(fighter, now):
        if not fighter.can_bomb:
            return
        cell = fighter.cell
        if can_place(bombs, cell, fighter.index, fighter.max_bombs):
            remote = fighter.detonator and not getattr(fighter, "is_bot", False)
            bombs.append(Bomb(*cell, owner=fighter.index, fire=fighter.flame,
                              now=now, remote=remote))

    spawn_round()

    running = True
    while running:
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            elif (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE
                  and player.alive):
                place_bomb(player, now)
            elif (e.type == pygame.KEYDOWN and e.scancode == SCAN_E
                  and player.alive and player.detonator):
                for b in bombs:
                    if b.owner == player.index and b.remote:
                        b.detonate()
            elif e.type == pygame.KEYDOWN and e.scancode == SCAN_R:
                new_round()
            elif e.type == pygame.KEYDOWN and e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                state["difficulty"] = {pygame.K_1: c.DIFF_EASY,
                                       pygame.K_2: c.DIFF_MEDIUM,
                                       pygame.K_3: c.DIFF_HARD}[e.key]
                new_round(next_seed=False)
            elif e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFTBRACKET,
                                                        pygame.K_RIGHTBRACKET):
                d = -1 if e.key == pygame.K_LEFTBRACKET else 1
                state["bots"] = max(1, min(len(arena.spawns) - 1, state["bots"] + d))
                new_round(next_seed=False)
            controls.handle(e)

        # --- Обновление бойцов ---
        player.update_curse(now)
        if player.alive:
            move_dir = player.input_dir(controls.direction())
            _try_kick(player, arena, bombs, move_dir)
            player.try_move(arena, move_dir, [b.cell for b in bombs])
            if player.auto_bomb and now - last_autobomb >= c.AUTOBOMB_MS:
                place_bomb(player, now)
                last_autobomb = now

        pu_cells = {p.cell for p in powerups}
        for f in fighters:
            if isinstance(f, Bot) and f.alive:
                f.update_curse(now)
                f.goal_powerups = pu_cells
                enemies = [o for o in fighters if o is not f]
                d, want = f.action(arena, enemies, bombs, explosions, now)
                f.try_move(arena, d, [b.cell for b in bombs])
                if want:
                    place_bomb(f, now)

        # Скольжение пиннутых бомб (стоп у препятствий и у бойцов)
        occupied = {f.cell for f in fighters if f.alive}
        for b in bombs:
            b.update_motion(arena, bombs, occupied)

        # Фитили + цепные детонации
        for b in bombs:
            b.update(now)
        fresh = detonate_chain(arena, bombs, explosions, now)
        bombs = [b for b in bombs if not b.exploded]

        # Бонусы из разрушенных ящиков
        for ex in fresh:
            for cell in ex.destroyed:
                kind = arena.pop_hidden(*cell)
                if kind is not None:
                    powerups.append(PowerUp(*cell, kind, now))

        for ex in explosions:
            ex.update(now)
        explosions = [ex for ex in explosions if not ex.done]

        # Подбор бонусов всеми живыми бойцами
        for f in fighters:
            if f.alive:
                got = pickup(powerups, f.cell)
                if got is not None:
                    f.apply_powerup(got.kind, now)
        powerups = [p for p in powerups if not (
            p.taken or any(ex.born > p.born and ex.contains(p.cell)
                           for ex in explosions))]

        # Гибель в пламени
        for f in fighters:
            if f.alive and f.in_flame(explosions):
                f.kill(now)

        # Итог раунда: остался один (или погиб игрок) → пауза → новый раунд
        if state["over_at"] is None:
            alive = [f for f in fighters if f.alive]
            if not player.alive or len(alive) <= 1:
                state["over_at"] = now
                state["winner"] = alive[0] if len(alive) == 1 else None
                if state["winner"] is player:
                    state["wins"] += 1
        elif now - state["over_at"] >= max(c.RESPAWN_MS, 1400):
            new_round()

        # --- Отрисовка ---
        screen.fill(c.BG_COLOR)
        arena.draw(screen)
        for p in powerups:
            p.draw(screen, now)
        for b in bombs:
            b.draw(screen, now)
        for ex in explosions:
            ex.draw(screen, now)
        for f in fighters:
            if f.alive or (f.dead_at is not None and now - f.dead_at < c.RESPAWN_MS):
                f.draw(screen, now)

        draw_hud(screen, font, small, tiny, player, fighters, bombs, now, state)
        if state["over_at"] is not None:
            _draw_banner(screen, big, small, state, player)

        pygame.display.flip()
        clock.tick(c.FPS)

    pygame.quit()


def _try_kick(fighter, arena, bombs, move_dir):
    """Пинок: упёрся в стоящую бомбу и есть бонус — толкаем её."""
    if not (fighter.kick and move_dir is not None):
        return
    pcol, prow = fighter.cell
    ahead = (pcol + move_dir[0], prow + move_dir[1])
    beyond = (ahead[0] + move_dir[0], ahead[1] + move_dir[1])
    for b in bombs:
        if not b.moving and b.cell == ahead:
            if (not arena.is_solid(*beyond)
                    and not any(bb.cell == beyond for bb in bombs)):
                b.kick(move_dir)
            break


def draw_hud(screen, font, small, tiny, player, fighters, bombs, now, state):
    """Правая панель: таймер, статы игрока, боты/сложность, подсказки."""
    x = c.FIELD_W
    pygame.draw.rect(screen, c.HUD_BG, (x, 0, c.HUD_W, c.HEIGHT))
    screen.blit(font.render("BOMBERMAN", True, c.HUD_TEXT), (x + 14, 12))

    secs = max(0, (now - state["round_start"]) // 1000)
    alive_bots = sum(1 for f in fighters if getattr(f, "is_bot", False) and f.alive)
    screen.blit(small.render(f"Раунд {secs // 60}:{secs % 60:02d}", True, c.ACCENT),
                (x + 14, 34))
    screen.blit(tiny.render(f"Боты живы: {alive_bots}   Победы: {state['wins']}",
                            True, c.HUD_TEXT), (x + 14, 52))

    rows = [
        (c.POW_BOMB, f"x{player.max_bombs}"),
        (c.POW_FIRE, f"x{player.fire}"),
        (c.POW_SPEED, f"x{player.speed_level + 1}"),
        (c.POW_KICK, "есть" if player.kick else "—"),
        (c.POW_DETON, "есть" if player.detonator else "—"),
    ]
    y = 72
    for kind, label in rows:
        render_badge(screen, kind, x + 22, y + 9, 10)
        col = c.HUD_TEXT if label in ("есть",) or label.startswith("x") else (120, 122, 130)
        screen.blit(small.render(label, True, col), (x + 40, y + 2))
        y += 26

    if player.curse is not None:
        render_badge(screen, c.POW_SKULL, x + 22, y + 9, 10)
        left = max(0, (player.curse_until - now) // 1000)
        name = c.CURSE_NAMES.get(player.curse, "?")
        screen.blit(tiny.render(f"{name} {left}с", True, (240, 150, 160)), (x + 40, y + 3))
        y += 26

    hints = [
        f"Сложность: {c.DIFF_NAMES[state['difficulty']]}",
        f"Ботов: {state['bots']}",
        "",
        "Пробел — бомба",
        "E — детонатор",
        "1/2/3 — сложность",
        "[ ] — число ботов",
        "R — заново  Esc — выход",
    ]
    hy = c.HEIGHT - len(hints) * 19 - 10
    for line in hints:
        screen.blit(tiny.render(line, True, c.HUD_TEXT), (x + 14, hy))
        hy += 19


def _draw_banner(screen, big, small, state, player):
    """Плашка итога раунда по центру поля."""
    w = state["winner"]
    if w is player:
        text, col = "ПОБЕДА!", (120, 220, 130)
    elif w is not None:
        text, col = "Победил бот", (235, 130, 120)
    else:
        text, col = "Ничья", (220, 220, 140)
    surf = pygame.Surface((c.FIELD_W, 90), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 150))
    screen.blit(surf, (0, c.FIELD_H // 2 - 45))
    label = big.render(text, True, col)
    screen.blit(label, (c.FIELD_W // 2 - label.get_width() // 2, c.FIELD_H // 2 - 30))
    sub = small.render("новый раунд…", True, c.WHITE)
    screen.blit(sub, (c.FIELD_W // 2 - sub.get_width() // 2, c.FIELD_H // 2 + 12))


if __name__ == "__main__":
    main()
