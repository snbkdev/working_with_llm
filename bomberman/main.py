"""Bomberman на pygame — точка входа.

Превью Этапов 1–5: арена, бомбы с крестообразным взрывом, цепные детонации,
бонусы/проклятия, ИИ-боты и **режимы игры** с выбором в меню:
  • 1 игрок против ИИ,
  • 2 игрока: дуэль (друг против друга),
  • 2 игрока против ИИ.

Запуск (из каталога bomberman):
    python main.py

Меню: ↑/↓ — режим, ←/→ — число ботов, 1/2/3 — сложность, Enter — старт, Esc — выход.
Игра: P1 — WASD + Пробел (E детонатор); P2 — стрелки + правый Ctrl (правый Shift
детонатор). R — новый раунд, Esc — в меню.
"""

import pygame

from src import config as c
from src.controls import (Input, SCHEME_ARROWS, SCHEME_BOTH, SCHEME_WASD,
                          SCAN_E, SCAN_R)
from src.entities.bomb import Bomb, can_place
from src.entities.bot import Bot
from src.entities.explosion import detonate_chain
from src.entities.player import Player
from src.entities.powerup import PowerUp, pickup, render_badge
from src.sound import Synth
from src.world.arena import Arena

# Строки главного меню
ROW_PLAY, ROW_MODE, ROW_BOTS, ROW_DIFF, ROW_SOUND, ROW_QUIT = range(6)
MENU_ROWS = (ROW_PLAY, ROW_MODE, ROW_BOTS, ROW_DIFF, ROW_SOUND, ROW_QUIT)


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


class Human:
    """Живой игрок: спрайт + своя схема управления и клавиши действий."""

    def __init__(self, player, scheme, bomb_key, deton_key=None, deton_scan=None):
        self.player = player
        self.input = Input(scheme)
        self.bomb_key = bomb_key
        self.deton_key = deton_key          # клавиша детонатора (pygame key) или None
        self.deton_scan = deton_scan        # или скан-код детонатора
        self.last_autobomb = 0

    def wants_detonate(self, e):
        return ((self.deton_key is not None and e.key == self.deton_key)
                or (self.deton_scan is not None and e.scancode == self.deton_scan))


def main():
    pygame.init()
    screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
    pygame.display.set_icon(make_bomb_icon())
    pygame.display.set_caption("Bomberman")
    fonts = {
        "big": pygame.font.SysFont("Helvetica", 34, bold=True),
        "font": pygame.font.SysFont("Helvetica", 15, bold=True),
        "small": pygame.font.SysFont("Helvetica", 13),
        "tiny": pygame.font.SysFont("Helvetica", 12, bold=True),
    }
    clock = pygame.time.Clock()
    snd = Synth()

    st = {
        "scene": "menu",
        "menu_row": ROW_PLAY,
        "mode": c.MODE_1P_AI,
        "bots": c.DEFAULT_BOTS,
        "difficulty": c.DEFAULT_DIFFICULTY,
        "seed": 0,
        "round_start": 0,
        "over_at": None,
        "winner": None,
        "scores": {},                       # индекс бойца → число побед
        "roster": [],                       # [(индекс, подпись)] участников матча
        "round_no": 1,
        "intro_until": 0,
    }
    arena = Arena(seed=st["seed"])
    fighters = []
    humans = []
    bombs, explosions, powerups = [], [], []

    def bot_cap():
        """Максимум ботов для текущего режима (всего бойцов ≤ 4)."""
        if st["mode"] == c.MODE_2P_DUEL:
            return 0
        return c.MAX_FIGHTERS - c.MODE_HUMANS[st["mode"]]

    def spawn_round():
        nonlocal fighters, humans
        arena.generate(st["seed"])
        fighters = []
        humans = []
        n_humans = c.MODE_HUMANS[st["mode"]]
        spawns = arena.spawns

        # Живые игроки
        p1 = Player(*spawns[0], index=0)
        if n_humans == 1:
            humans.append(Human(p1, SCHEME_BOTH, pygame.K_SPACE, deton_scan=SCAN_E))
        else:
            humans.append(Human(p1, SCHEME_WASD, pygame.K_SPACE, deton_scan=SCAN_E))
            p2 = Player(*spawns[1], index=1)
            humans.append(Human(p2, SCHEME_ARROWS, pygame.K_RCTRL,
                                deton_key=pygame.K_RSHIFT))
            fighters.append(p1)
            fighters.append(p2)
        if n_humans == 1:
            fighters.append(p1)

        # Боты занимают оставшиеся углы
        n_bots = min(st["bots"], bot_cap(), len(spawns) - n_humans)
        for i in range(n_bots):
            col, row = spawns[n_humans + i]
            fighters.append(Bot(col, row, index=n_humans + i,
                                difficulty=st["difficulty"],
                                seed=st["seed"] * 10 + i))

        # Ростер матча (стабильные индексы → подписи для таблицы счёта)
        roster = []
        bi = 0
        for f in fighters:
            if f.index < n_humans:
                roster.append((f.index, f"P{f.index + 1}"))
            else:
                bi += 1
                roster.append((f.index, f"Бот {bi}"))
        st["roster"] = roster

        for h in humans:
            h.input.clear()
        bombs.clear()
        explosions.clear()
        powerups.clear()
        st["round_start"] = pygame.time.get_ticks()
        st["over_at"] = None
        st["winner"] = None

    def begin_intro(bump_seed):
        """Готовит раунд и включает заставку «Раунд N»."""
        if bump_seed:
            st["seed"] += 1
        spawn_round()
        st["intro_until"] = pygame.time.get_ticks() + c.INTRO_MS
        st["scene"] = "intro"
        snd.play("round")

    def new_round(next_seed=True):
        if next_seed:
            st["seed"] += 1
        spawn_round()

    def place_bomb(fighter, now):
        if not fighter.can_bomb:
            return
        cell = fighter.cell
        if can_place(bombs, cell, fighter.index, fighter.max_bombs):
            remote = fighter.detonator and not getattr(fighter, "is_bot", False)
            bombs.append(Bomb(*cell, owner=fighter.index, fire=fighter.flame,
                              now=now, remote=remote))
            snd.play("bomb")

    running = True
    while running:
        now = pygame.time.get_ticks()

        if st["scene"] == "menu":
            def start_match():
                st["scores"] = {}
                st["round_no"] = 1
                begin_intro(bump_seed=False)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    row = st["menu_row"]
                    if e.key == pygame.K_ESCAPE:
                        running = False
                    elif e.key in (pygame.K_UP, pygame.K_DOWN):
                        step = -1 if e.key == pygame.K_UP else 1
                        st["menu_row"] = (row + step) % len(MENU_ROWS)
                        snd.play("blip")
                    elif e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        d = -1 if e.key == pygame.K_LEFT else 1
                        if row == ROW_MODE:
                            st["mode"] = (st["mode"] + d) % len(c.MODE_NAMES)
                            st["bots"] = min(st["bots"], max(1, bot_cap()))
                        elif row == ROW_BOTS and bot_cap():
                            st["bots"] = max(1, min(bot_cap(), st["bots"] + d))
                        elif row == ROW_DIFF:
                            st["difficulty"] = (st["difficulty"] + d) % len(c.DIFF_NAMES)
                        elif row == ROW_SOUND:
                            snd.toggle()
                        snd.play("blip")
                    elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        if row == ROW_QUIT:
                            running = False
                        elif row == ROW_SOUND:
                            snd.toggle()
                        else:
                            start_match()
                    elif e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        st["difficulty"] = {pygame.K_1: c.DIFF_EASY,
                                            pygame.K_2: c.DIFF_MEDIUM,
                                            pygame.K_3: c.DIFF_HARD}[e.key]
            draw_menu(screen, fonts, st, bot_cap(), snd.enabled, now)
            pygame.display.flip()
            clock.tick(c.FPS)
            continue

        if st["scene"] == "intro":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    st["scene"] = "menu"
            if now >= st["intro_until"]:
                st["round_start"] = now
                st["scene"] = "play"
            screen.fill(c.BG_COLOR)
            arena.draw(screen)
            for f in fighters:
                if f.alive:
                    f.draw(screen, now)
            draw_hud(screen, fonts, humans, fighters, now, st)
            draw_intro(screen, fonts, st)
            pygame.display.flip()
            clock.tick(c.FPS)
            continue

        if st["scene"] == "scoreboard":
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key in (
                        pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE,
                        pygame.K_SPACE):
                    st["scene"] = "menu"
            draw_scoreboard(screen, fonts, st)
            pygame.display.flip()
            clock.tick(c.FPS)
            continue

        # --- Сцена игры ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                st["scene"] = "menu"
            elif e.type == pygame.KEYDOWN and e.scancode == SCAN_R:
                new_round()
            elif e.type == pygame.KEYDOWN:
                for h in humans:
                    if e.key == h.bomb_key and h.player.alive:
                        place_bomb(h.player, now)
                    if h.wants_detonate(e) and h.player.alive and h.player.detonator:
                        for b in bombs:
                            if b.owner == h.player.index and b.remote:
                                b.detonate()
            for h in humans:
                h.input.handle(e)

        # --- Обновление живых игроков ---
        for h in humans:
            p = h.player
            if not p.alive:
                continue
            p.update_curse(now)
            move_dir = p.input_dir(h.input.direction())
            _try_kick(p, arena, bombs, move_dir)
            p.try_move(arena, move_dir, [b.cell for b in bombs])
            if p.auto_bomb and now - h.last_autobomb >= c.AUTOBOMB_MS:
                place_bomb(p, now)
                h.last_autobomb = now

        # --- Обновление ботов ---
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

        occupied = {f.cell for f in fighters if f.alive}
        for b in bombs:
            b.update_motion(arena, bombs, occupied)
        for b in bombs:
            b.update(now)
        fresh = detonate_chain(arena, bombs, explosions, now)
        bombs = [b for b in bombs if not b.exploded]
        if fresh:
            snd.play("boom")

        for ex in fresh:
            for cell in ex.destroyed:
                kind = arena.pop_hidden(*cell)
                if kind is not None:
                    powerups.append(PowerUp(*cell, kind, now))

        for ex in explosions:
            ex.update(now)
        explosions = [ex for ex in explosions if not ex.done]

        for f in fighters:
            if f.alive:
                got = pickup(powerups, f.cell)
                if got is not None:
                    f.apply_powerup(got.kind, now)
                    snd.play("curse" if got.kind == c.POW_SKULL else "pickup")
        powerups = [p for p in powerups if not (
            p.taken or any(ex.born > p.born and ex.contains(p.cell)
                           for ex in explosions))]

        for f in fighters:
            if f.alive and f.in_flame(explosions):
                f.kill(now)
                snd.play("death")

        # Итог раунда
        if st["over_at"] is None:
            alive = [f for f in fighters if f.alive]
            humans_alive = [h.player for h in humans if h.player.alive]
            done = len(alive) <= 1 or (humans and not humans_alive)
            if done:
                st["over_at"] = now
                st["winner"] = alive[0] if len(alive) == 1 else None
                if st["winner"] is not None:
                    idx = st["winner"].index
                    st["scores"][idx] = st["scores"].get(idx, 0) + 1
        elif now - st["over_at"] >= max(c.RESPAWN_MS, 1600):
            # Раунд завершён: матч продолжается или — итоговая таблица
            if max(st["scores"].values(), default=0) >= c.WINS_TO_MATCH:
                st["scene"] = "scoreboard"
                snd.play("win")
            else:
                st["round_no"] += 1
                begin_intro(bump_seed=True)

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

        draw_hud(screen, fonts, humans, fighters, now, st)
        if st["over_at"] is not None:
            _draw_banner(screen, fonts, st, humans, fighters)

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


def _draw_menu_bomb(screen, cx, cy, r, now):
    """Крупная пульсирующая бомба-логотип для меню."""
    import math
    r = int(r * (1 + 0.05 * math.sin(now * 0.004)))
    pygame.draw.circle(screen, (30, 32, 40), (cx, cy), r)
    pygame.draw.circle(screen, (12, 12, 16), (cx, cy), r, 3)
    pygame.draw.circle(screen, (120, 128, 150), (cx - r // 3, cy - r // 3), max(3, r // 4))
    pygame.draw.rect(screen, (90, 92, 100), (cx - 5, cy - r - 6, 10, 8), border_radius=2)
    tipx, tipy = cx + 9, cy - r - 16
    pygame.draw.lines(screen, (200, 170, 90), False,
                      [(cx + 2, cy - r - 4), (cx + 11, cy - r - 9), (tipx, tipy)], 3)
    if (now // 180) % 2 == 0:
        pygame.draw.circle(screen, (250, 220, 90), (tipx, tipy), 6)
        pygame.draw.circle(screen, (250, 140, 40), (tipx, tipy), 3)


def draw_menu(screen, fonts, st, cap, sound_on, now):
    """Главное меню при запуске: логотип и строки-пункты."""
    screen.fill(c.BG_COLOR)
    # Лёгкая «шахматка» пола на фоне
    for row in range(0, c.HEIGHT, c.TILE):
        for col in range(0, c.WIDTH, c.TILE):
            shade = c.FLOOR_A if (col // c.TILE + row // c.TILE) % 2 == 0 else c.FLOOR_B
            shade = tuple(int(v * 0.35) for v in shade)
            pygame.draw.rect(screen, shade, (col, row, c.TILE, c.TILE))

    _draw_menu_bomb(screen, c.WIDTH // 2 - 150, 70, 26, now)
    title = fonts["big"].render("BOMBERMAN", True, c.ACCENT)
    screen.blit(title, (c.WIDTH // 2 - title.get_width() // 2 + 20, 52))
    sub = fonts["small"].render("Аренный боевик в духе Atomic Bomberman", True, c.WHITE)
    screen.blit(sub, (c.WIDTH // 2 - sub.get_width() // 2, 96))

    bots_val = f"{min(st['bots'], cap)}" if cap else "—"
    rows = {
        ROW_PLAY: ("Играть", None),
        ROW_MODE: ("Режим", c.MODE_NAMES[st["mode"]]),
        ROW_BOTS: ("Ботов", bots_val),
        ROW_DIFF: ("Сложность", c.DIFF_NAMES[st["difficulty"]]),
        ROW_SOUND: ("Звук", "вкл" if sound_on else "выкл"),
        ROW_QUIT: ("Выход", None),
    }
    y = 126
    for r in MENU_ROWS:
        label, value = rows[r]
        sel = r == st["menu_row"]
        box = pygame.Rect(c.WIDTH // 2 - 180, y, 360, 38)
        pygame.draw.rect(screen, (46, 50, 64) if sel else (26, 28, 36), box, border_radius=8)
        if sel:
            pygame.draw.rect(screen, c.ACCENT, box, 2, border_radius=8)
            pygame.draw.circle(screen, c.ACCENT, (box.x + 16, box.centery), 4)
        col = c.ACCENT if sel else c.HUD_TEXT
        screen.blit(fonts["font"].render(label, True, col), (box.x + 30, box.y + 10))
        if value is not None:
            vs = fonts["font"].render(value, True, c.WHITE if sel else (170, 174, 186))
            vx = box.right - vs.get_width() - 30
            screen.blit(vs, (vx, box.y + 10))
            if sel:  # стрелки выбора ‹ ›
                arr = fonts["font"].render("<", True, c.ACCENT)
                screen.blit(arr, (vx - 20, box.y + 10))
                screen.blit(fonts["font"].render(">", True, c.ACCENT),
                            (box.right - 22, box.y + 10))
        y += 42

    lines = [
        "↑/↓ — пункт    ←/→ — значение    Enter — выбрать    Esc — выход",
        "P1: WASD + Пробел (E — детонатор)     P2: стрелки + пр.Ctrl (пр.Shift)",
    ]
    y = c.HEIGHT - 44
    for ln in lines:
        surf = fonts["tiny"].render(ln, True, (190, 194, 206))
        screen.blit(surf, (c.WIDTH // 2 - surf.get_width() // 2, y))
        y += 20


def draw_intro(screen, fonts, st):
    """Заставка перед раундом: затемнение поля и крупное «Раунд N»."""
    veil = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 150))
    screen.blit(veil, (0, 0))
    title = fonts["big"].render(f"Раунд {st['round_no']}", True, c.ACCENT)
    screen.blit(title, (c.FIELD_W // 2 - title.get_width() // 2, c.FIELD_H // 2 - 46))
    sub = fonts["font"].render(c.MODE_NAMES[st["mode"]], True, c.WHITE)
    screen.blit(sub, (c.FIELD_W // 2 - sub.get_width() // 2, c.FIELD_H // 2 + 2))
    go = fonts["small"].render(f"до {c.WINS_TO_MATCH} побед — приготовься!", True, (200, 204, 214))
    screen.blit(go, (c.FIELD_W // 2 - go.get_width() // 2, c.FIELD_H // 2 + 30))


def draw_scoreboard(screen, fonts, st):
    """Итоговая таблица счёта матча."""
    screen.fill(c.BG_COLOR)
    title = fonts["big"].render("Итоги матча", True, c.ACCENT)
    screen.blit(title, (c.WIDTH // 2 - title.get_width() // 2, 40))

    roster = sorted(st["roster"], key=lambda r: -st["scores"].get(r[0], 0))
    win_idx = roster[0][0] if roster and st["scores"].get(roster[0][0], 0) else None
    y = 130
    for idx, label in roster:
        wins = st["scores"].get(idx, 0)
        champ = idx == win_idx
        box = pygame.Rect(c.WIDTH // 2 - 200, y, 400, 44)
        pygame.draw.rect(screen, (46, 50, 64) if champ else (28, 30, 38), box, border_radius=8)
        if champ:
            pygame.draw.rect(screen, c.ACCENT, box, 2, border_radius=8)
        col = c.ACCENT if champ else c.HUD_TEXT
        screen.blit(fonts["font"].render(label, True, col), (box.x + 20, box.y + 13))
        # Победы значками-бомбами
        for k in range(wins):
            render_badge(screen, c.POW_BOMB, box.right - 30 - k * 26, box.centery, 9)
        screen.blit(fonts["font"].render(f"{wins}", True, col),
                    (box.right - 30 - c.WINS_TO_MATCH * 26 - 24, box.y + 13))
        y += 54

    champ_label = next((lbl for idx, lbl in roster if idx == win_idx), None)
    if champ_label:
        won = fonts["big"].render(f"Победитель: {champ_label}", True, (120, 220, 130))
        screen.blit(won, (c.WIDTH // 2 - won.get_width() // 2, y + 6))
    hint = fonts["small"].render("Enter — в меню", True, c.WHITE)
    screen.blit(hint, (c.WIDTH // 2 - hint.get_width() // 2, c.HEIGHT - 34))


def draw_hud(screen, fonts, humans, fighters, now, st):
    """Правая панель: режим, статы игроков, счёт, подсказки."""
    x = c.FIELD_W
    small, tiny, font = fonts["small"], fonts["tiny"], fonts["font"]
    pygame.draw.rect(screen, c.HUD_BG, (x, 0, c.HUD_W, c.HEIGHT))
    secs = max(0, (now - st["round_start"]) // 1000)
    screen.blit(font.render("BOMBERMAN", True, c.HUD_TEXT), (x + 12, 10))
    screen.blit(tiny.render(f"{c.MODE_NAMES[st['mode']]}", True, c.ACCENT), (x + 12, 30))
    alive_bots = sum(1 for f in fighters if getattr(f, "is_bot", False) and f.alive)
    screen.blit(tiny.render(f"Раунд {secs//60}:{secs%60:02d}   боты:{alive_bots}",
                            True, c.HUD_TEXT), (x + 12, 46))

    y = 66
    for i, h in enumerate(humans):
        y = _draw_player_block(screen, fonts, h.player, x, y, f"P{i+1}",
                               st["scores"].get(h.player.index, 0), now)

    hints = [
        "P1 WASD+Пробел",
        "P2 стрелки+ПКМCtrl",
        "R — раунд",
        "Esc — меню",
    ]
    hy = c.HEIGHT - len(hints) * 18 - 8
    for line in hints:
        screen.blit(tiny.render(line, True, (170, 174, 186)), (x + 12, hy))
        hy += 18


def _draw_player_block(screen, fonts, player, x, y, label, wins, now):
    """Компактный блок статов одного игрока: имя, значки, проклятие, победы."""
    small, tiny = fonts["small"], fonts["tiny"]
    name_col = player.color if player.alive else c.DEAD_COLOR
    pygame.draw.rect(screen, (36, 38, 46), (x + 8, y, c.HUD_W - 16, 74), border_radius=6)
    tag = tiny.render(f"{label}  побед: {wins}", True, name_col)
    screen.blit(tag, (x + 14, y + 4))
    if not player.alive:
        screen.blit(tiny.render("выбыл", True, (200, 120, 120)), (x + c.HUD_W - 54, y + 4))
    # Значки статов в ряд
    rows = [(c.POW_BOMB, str(player.max_bombs)), (c.POW_FIRE, str(player.fire)),
            (c.POW_SPEED, str(player.speed_level + 1))]
    bx = x + 20
    for kind, val in rows:
        render_badge(screen, kind, bx, y + 34, 9)
        screen.blit(tiny.render(val, True, c.HUD_TEXT), (bx + 11, y + 27))
        bx += 34
    # Способности и проклятие
    if player.kick:
        render_badge(screen, c.POW_KICK, bx, y + 34, 9); bx += 22
    if player.detonator:
        render_badge(screen, c.POW_DETON, bx, y + 34, 9); bx += 22
    if player.curse is not None:
        left = max(0, (player.curse_until - now) // 1000)
        screen.blit(tiny.render(f"! {c.CURSE_NAMES.get(player.curse,'?')} {left}с",
                                True, (240, 150, 160)), (x + 14, y + 52))
    return y + 82


def _draw_banner(screen, fonts, st, humans, fighters):
    """Плашка итога раунда по центру поля."""
    w = st["winner"]
    if w is not None and getattr(w, "is_bot", False):
        text, col = "Победил бот", (235, 130, 120)
    elif w is not None:
        num = next((i + 1 for i, h in enumerate(humans) if h.player is w), None)
        text, col = (f"Победил P{num}!" if num else "Победа!"), (120, 220, 130)
    else:
        # Победителя-одиночки нет: либо все погибли (ничья), либо люди выбыли,
        # а боты ещё живы (поражение игроков).
        humans_alive = any(h.player.alive for h in humans)
        bots_alive = any(getattr(f, "is_bot", False) and f.alive for f in fighters)
        if not humans_alive and bots_alive:
            text, col = "Боты победили", (235, 130, 120)
        else:
            text, col = "Ничья", (220, 220, 140)
    surf = pygame.Surface((c.FIELD_W, 90), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 150))
    screen.blit(surf, (0, c.FIELD_H // 2 - 45))
    label = fonts["big"].render(text, True, col)
    screen.blit(label, (c.FIELD_W // 2 - label.get_width() // 2, c.FIELD_H // 2 - 30))
    sub = fonts["small"].render("новый раунд…", True, c.WHITE)
    screen.blit(sub, (c.FIELD_W // 2 - sub.get_width() // 2, c.FIELD_H // 2 + 12))


if __name__ == "__main__":
    main()
