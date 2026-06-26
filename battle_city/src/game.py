"""Игровой цикл Battle City.

Этап 3: бой и правила — пули уничтожают врагов (+очки) и игрока (жизни,
респаун с неуязвимостью), разрушение базы = поражение, уничтожение всех
врагов = победа. Состояния: меню, игра, пауза, управление, финал.
"""

import random
import sys

import pygame

from . import config as c
from .entities.enemy import Enemy
from .entities.explosion import Explosion
from .entities.tank import Tank
from .menu import Menu
from .sound import Sounds
from .world import levels
from .world.level import Level

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_CONTROLS = "controls"
STATE_LEVELCLEAR = "levelclear"
STATE_GAMEOVER = "gameover"

MAIN_MENU_ITEMS = [
    ("Новая игра", "new_game", True),
    ("Загрузка", "load", False),
    ("Настройки", "settings", False),
    ("Выход", "quit", True),
]
PAUSE_MENU_ITEMS = [
    ("Продолжить", "resume", True),
    ("Сохранить/Загрузить", "saveload", False),
    ("Управление", "controls", True),
    ("Выйти", "exit", True),
]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
        pygame.display.set_caption("Battle City")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Helvetica", 18, bold=True)
        self.small = pygame.font.SysFont("Helvetica", 13)
        # Крупные шрифты финальных экранов — создаём один раз, не покадрово
        self.big = pygame.font.SysFont("Helvetica", 44, bold=True)
        self.big2 = pygame.font.SysFont("Helvetica", 40, bold=True)
        self.sounds = Sounds(c.SOUND_ENABLED)

        # Начинаем с главного меню; уровень создаётся при «Новой игре»
        self.state = STATE_MENU
        self.menu = Menu(MAIN_MENU_ITEMS, title="BATTLE CITY",
                         subtitle="Tank 1990 · pygame")
        self.pause_menu = Menu(PAUSE_MENU_ITEMS, title="ПАУЗА", overlay=True)

    def reset(self):
        """Новая игра с первого уровня: сбрасываются очки и жизни."""
        self.lives = c.PLAYER_LIVES
        self.score = 0
        self.load_level(0)

    def load_level(self, index):
        """Загружает уровень index и сбрасывает поле.

        Очки и жизни сохраняются между уровнями (их обнуляет только reset).
        """
        self.level_index = index
        self.level = Level(levels.load_level(index))
        col, row = self.level.player_spawn
        self.player = Tank(col, row, c.UP, is_player=True)
        self.bullets = []
        self.explosions = []
        self.last_shot = 0
        self.result = None
        # Кратковременная неуязвимость на старте
        self.player_invuln_until = (
            pygame.time.get_ticks() + c.PLAYER_INVULN_MS
        )

        # Враги: случайное число за уровень (10–15)
        self.enemies = []
        self.enemies_to_spawn = random.randint(
            c.ENEMY_COUNT_MIN, c.ENEMY_COUNT_MAX
        )
        self.spawn_index = 0
        # Пауза перед первым врагом (~6 сек после старта)
        self.next_spawn_at = pygame.time.get_ticks() + c.ENEMY_START_DELAY

    # --- Переходы состояний ---
    def start_new_game(self):
        self.reset()
        self.state = STATE_PLAYING

    def back_to_menu(self):
        self.sounds.engine_stop()
        self.state = STATE_MENU

    def pause(self):
        self.sounds.engine_stop()
        self.pause_menu.index = 0
        self.state = STATE_PAUSED

    def resume(self):
        self.state = STATE_PLAYING

    # --- Бой и исходы ---
    def spawn_explosion(self, pos, big=True):
        self.explosions.append(Explosion(pos[0], pos[1], big))

    def respawn_player(self):
        col, row = self.level.player_spawn
        self.player = Tank(col, row, c.UP, is_player=True)
        self.player_invuln_until = (
            pygame.time.get_ticks() + c.PLAYER_INVULN_MS
        )

    def player_hit(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over("lose")
        else:
            self.respawn_player()

    def game_over(self, result):
        if self.state != STATE_PLAYING:
            return
        self.result = result
        self.sounds.engine_stop()
        self.state = STATE_GAMEOVER

    def level_cleared(self):
        """Уровень зачищен: следующий уровень либо финальная победа."""
        if self.state != STATE_PLAYING:
            return
        self.sounds.engine_stop()
        if self.level_index + 1 < levels.level_count():
            self.state = STATE_LEVELCLEAR     # ждём подтверждения игрока
        else:
            self.game_over("win")             # пройден последний уровень

    def next_level(self):
        self.load_level(self.level_index + 1)
        self.state = STATE_PLAYING

    # --- Стрельба ---
    def player_bullets(self):
        return [b for b in self.bullets if b.owner == "player"]

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot < c.PLAYER_SHOOT_COOLDOWN:
            return
        if len(self.player_bullets()) >= c.PLAYER_MAX_BULLETS:
            return
        self.bullets.append(self.player.shoot())
        self.sounds.play_shoot()
        self.last_shot = now

    # --- Появление врагов ---
    def try_spawn_enemy(self, now):
        if self.enemies_to_spawn <= 0:
            return
        if len(self.enemies) >= c.MAX_ACTIVE_ENEMIES:
            return
        if now < self.next_spawn_at:
            return

        spawns = self.level.enemy_spawns           # лево / центр / право
        occupied = [t.rect for t in self.enemies] + [self.player.rect]

        # Берём первую свободную точку, перебирая по кругу от текущего индекса
        n = len(spawns)
        for k in range(n):
            cell = spawns[(self.spawn_index + k) % n]
            enemy = Enemy(*cell)
            if not any(enemy.rect.colliderect(o) for o in occupied):
                self.enemies.append(enemy)
                self.enemies_to_spawn -= 1
                self.spawn_index = (self.spawn_index + k + 1) % n
                self.next_spawn_at = now + c.ENEMY_SPAWN_INTERVAL
                return
        # Все точки заняты — попробуем в следующий раз

    # --- Ввод ---
    def handle_game_event(self, e):
        """Дискретные клавиши в режиме игры (стрельба, пауза, рестарт)."""
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                self.pause()
            elif e.key == pygame.K_ESCAPE:
                self.back_to_menu()
            elif e.key == pygame.K_r:
                self.reset()
            elif e.key == pygame.K_SPACE:
                self.shoot()

    def read_direction(self, keys):
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            return c.UP
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            return c.DOWN
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            return c.LEFT
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            return c.RIGHT
        return None

    # --- Логика ---
    def update(self):
        now = pygame.time.get_ticks()
        self.try_spawn_enemy(now)

        keys = pygame.key.get_pressed()
        direction = self.read_direction(keys)
        solids = self.level.solid_rects()

        # Игрок (враги — препятствия)
        enemy_rects = [e.rect for e in self.enemies]
        moved = False
        if direction is not None:
            self.player.face(direction)
            moved = self.player.try_move(solids, enemy_rects)

        # Звук двигателя — пока игрок реально едет
        if moved:
            self.sounds.engine_start()
        else:
            self.sounds.engine_stop()

        # Враги (ИИ)
        for e in self.enemies:
            blockers = [o.rect for o in self.enemies if o is not e]
            blockers.append(self.player.rect)
            bullet = e.update_ai(solids, blockers)
            if bullet is not None:
                self.bullets.append(bullet)

        # Пули
        for b in self.bullets:
            b.update()
            if not (0 <= b.x <= c.FIELD_W and 0 <= b.y <= c.FIELD_H):
                b.alive = False
                continue
            # Попадание в стену/базу
            res = self.level.hit(b.rect)
            if res:
                b.alive = False
                self.sounds.play_hit()
                self.spawn_explosion(b.rect.center, big=(res == "base"))
                if res == "base":
                    self.game_over("lose")
                continue
            # Попадание в танк
            self._bullet_vs_tanks(b, now)

        # Взаимное уничтожение встречных пуль
        self._bullets_cancel()

        # Взрывы: гаснут по истечении анимации
        for ex in self.explosions:
            ex.update(now)

        # Убираем уничтоженных врагов, погасшие пули и отыгравшие взрывы
        self.enemies = [e for e in self.enemies if e.alive]
        self.bullets = [b for b in self.bullets if b.alive]
        self.explosions = [ex for ex in self.explosions if ex.alive]

        # Уровень зачищен: все враги уничтожены и больше не появятся
        if self.enemies_to_spawn == 0 and not self.enemies:
            self.level_cleared()

    def _bullet_vs_tanks(self, b, now):
        if b.owner == "player":
            for e in self.enemies:
                if e.alive and b.rect.colliderect(e.rect):
                    e.alive = False
                    b.alive = False
                    self.score += c.ENEMY_SCORE
                    self.sounds.play_hit()
                    self.spawn_explosion(e.rect.center, big=True)
                    return
        else:  # пуля врага
            if b.rect.colliderect(self.player.rect):
                b.alive = False
                self.sounds.play_hit()
                if now >= self.player_invuln_until:
                    self.spawn_explosion(self.player.rect.center, big=True)
                    self.player_hit()

    def _bullets_cancel(self):
        pb = [b for b in self.bullets if b.alive and b.owner == "player"]
        eb = [b for b in self.bullets if b.alive and b.owner == "enemy"]
        for p in pb:
            for e in eb:
                if p.alive and e.alive and p.rect.colliderect(e.rect):
                    p.alive = False
                    e.alive = False
                    break

    # --- Отрисовка ---
    def draw(self):
        if self.state == STATE_MENU:
            self.menu.draw(self.screen)
            pygame.display.flip()
            return

        self._draw_scene()
        if self.state == STATE_PAUSED:
            self.pause_menu.draw(self.screen)
        elif self.state == STATE_CONTROLS:
            self.draw_controls()
        elif self.state == STATE_LEVELCLEAR:
            self.draw_levelclear()
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover()
        pygame.display.flip()

    def _draw_scene(self):
        self.screen.fill(c.BG_COLOR)
        pygame.draw.rect(self.screen, c.FIELD_COLOR, (0, 0, c.FIELD_W, c.FIELD_H))
        self.draw_grid()
        self.level.draw(self.screen)
        # Игрок: мигает, пока действует неуязвимость
        now = pygame.time.get_ticks()
        invuln = now < self.player_invuln_until
        if not invuln or (now // 120) % 2 == 0:
            self.player.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        for b in self.bullets:
            b.draw(self.screen)
        for ex in self.explosions:
            ex.draw(self.screen)
        pygame.draw.rect(self.screen, c.FIELD_BORDER, (0, 0, c.FIELD_W, c.FIELD_H), 2)
        self.draw_hud()

    def draw_grid(self):
        for x in range(c.TILE, c.FIELD_W, c.TILE):
            pygame.draw.line(self.screen, c.GRID_LINE, (x, 0), (x, c.FIELD_H))
        for y in range(c.TILE, c.FIELD_H, c.TILE):
            pygame.draw.line(self.screen, c.GRID_LINE, (0, y), (c.FIELD_W, y))

    def _mini_tank(self, x, y, size, body, track):
        """Маленькая иконка танка для панели."""
        pygame.draw.rect(self.screen, track, (x, y, size, size), border_radius=2)
        pygame.draw.rect(self.screen, body,
                         (x + 3, y + 2, size - 6, size - 4), border_radius=2)
        pygame.draw.rect(self.screen, track,
                         (x + size // 2 - 1, y - 2, 2, size // 2 + 2))

    def draw_hud(self):
        x = c.FIELD_W
        pygame.draw.rect(self.screen, c.HUD_BG, (x, 0, c.HUD_W, c.HEIGHT))

        title = self.font.render("BATTLE CITY", True, c.HUD_TEXT)
        self.screen.blit(title, (x + (c.HUD_W - title.get_width()) // 2, 18))

        # --- Очки ---
        slbl = self.small.render("ОЧКИ", True, c.HUD_TEXT)
        self.screen.blit(slbl, (x + 14, 48))
        snum = self.font.render(str(self.score), True, (40, 60, 90))
        self.screen.blit(snum, (x + c.HUD_W - 14 - snum.get_width(), 44))
        pygame.draw.line(self.screen, (70, 70, 70),
                         (x + 12, 74), (x + c.HUD_W - 12, 74), 1)

        # --- Жизни игрока ---
        lbl = self.small.render("ЖИЗНИ", True, c.HUD_TEXT)
        self.screen.blit(lbl, (x + 14, 88))
        num = self.font.render(str(self.lives), True, (60, 90, 40))
        self.screen.blit(num, (x + c.HUD_W - 32, 82))
        for i in range(self.lives):
            self._mini_tank(x + 16 + i * 24, 110, 16, c.PLAYER_COLOR, c.PLAYER_TRACK)

        pygame.draw.line(self.screen, (70, 70, 70),
                         (x + 12, 138), (x + c.HUD_W - 12, 138), 1)

        # --- Враги (осталось за уровень) ---
        remaining = self.enemies_to_spawn + len(self.enemies)
        lbl2 = self.small.render("ВРАГИ", True, c.HUD_TEXT)
        self.screen.blit(lbl2, (x + 14, 152))
        num2 = self.font.render(str(remaining), True, (70, 30, 30))
        self.screen.blit(num2, (x + c.HUD_W - 32, 146))
        # Сетка иконок оставшихся врагов
        ix, iy = x + 16, 176
        for i in range(remaining):
            col = i % 6
            row = i // 6
            self._mini_tank(ix + col * 21, iy + row * 22, 15,
                            c.ENEMY_COLOR, c.ENEMY_TRACK)

        # --- Уровень и подсказки ---
        lvl = self.small.render(
            f"Уровень {self.level_index + 1}/{levels.level_count()}",
            True, c.HUD_TEXT)
        self.screen.blit(lvl, (x + 14, c.HEIGHT - 76))

        hints = ["P — пауза", "Esc — в меню"]
        y = c.HEIGHT - 50
        for line in hints:
            surf = self.small.render(line, True, c.HUD_TEXT)
            self.screen.blit(surf, (x + 14, y))
            y += 20

    def draw_controls(self):
        dim = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
        dim.fill((10, 10, 14, 215))
        self.screen.blit(dim, (0, 0))
        cx = c.FIELD_W // 2

        title = self.font.render("УПРАВЛЕНИЕ", True, c.PLAYER_COLOR)
        self.screen.blit(title, (cx - title.get_width() // 2, 80))

        rows = [
            ("Движение", "Стрелки / W A S D"),
            ("Огонь", "Пробел"),
            ("Пауза", "P"),
            ("Рестарт", "R"),
            ("В меню", "Esc"),
        ]
        y = 150
        for action, key in rows:
            a = self.small.render(action, True, c.STEEL_COLOR)
            k = self.small.render(key, True, c.TEXT_COLOR)
            self.screen.blit(a, (cx - 120, y))
            self.screen.blit(k, (cx + 20, y))
            y += 34

        back = self.small.render("Esc или Enter — назад", True, (150, 150, 150))
        self.screen.blit(back, (cx - back.get_width() // 2, c.FIELD_H - 60))

    def draw_gameover(self):
        dim = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
        dim.fill((10, 10, 14, 210))
        self.screen.blit(dim, (0, 0))
        cx = c.FIELD_W // 2

        if self.result == "win":
            text, color = "ПОБЕДА!", c.PLAYER_COLOR
        else:
            text, color = "ПОРАЖЕНИЕ", c.ACCENT
        t = self.big.render(text, True, color)
        self.screen.blit(t, (cx - t.get_width() // 2, c.FIELD_H // 2 - 80))

        score = self.font.render(f"Очки: {self.score}", True, c.TEXT_COLOR)
        self.screen.blit(score, (cx - score.get_width() // 2, c.FIELD_H // 2 - 16))

        for i, line in enumerate(["R — играть заново", "Esc — в меню"]):
            s = self.small.render(line, True, (170, 170, 170))
            self.screen.blit(s, (cx - s.get_width() // 2, c.FIELD_H // 2 + 30 + i * 24))

    def draw_levelclear(self):
        dim = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
        dim.fill((10, 10, 14, 210))
        self.screen.blit(dim, (0, 0))
        cx = c.FIELD_W // 2

        t = self.big2.render("УРОВЕНЬ ПРОЙДЕН", True, c.PLAYER_COLOR)
        self.screen.blit(t, (cx - t.get_width() // 2, c.FIELD_H // 2 - 90))

        stage = self.font.render(
            f"{self.level_index + 1} / {levels.level_count()}", True, c.STEEL_COLOR)
        self.screen.blit(stage, (cx - stage.get_width() // 2, c.FIELD_H // 2 - 34))

        score = self.font.render(f"Очки: {self.score}", True, c.TEXT_COLOR)
        self.screen.blit(score, (cx - score.get_width() // 2, c.FIELD_H // 2 + 2))

        hint = self.small.render("Enter / Пробел — следующий уровень", True, (180, 180, 180))
        self.screen.blit(hint, (cx - hint.get_width() // 2, c.FIELD_H // 2 + 44))

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.quit()
                elif self.state == STATE_MENU:
                    self.handle_menu_event(e)
                elif self.state == STATE_PAUSED:
                    self.handle_pause_event(e)
                elif self.state == STATE_CONTROLS:
                    self.handle_controls_event(e)
                elif self.state == STATE_LEVELCLEAR:
                    self.handle_levelclear_event(e)
                elif self.state == STATE_GAMEOVER:
                    self.handle_gameover_event(e)
                else:
                    self.handle_game_event(e)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()
            self.clock.tick(c.FPS)

    def handle_menu_event(self, e):
        action = self.menu.handle_event(e)
        if action == "new_game":
            self.start_new_game()
        elif action == "quit":
            self.quit()
        # «load» и «settings» пока без действия

    def handle_pause_event(self, e):
        # P или Esc — быстро снять паузу
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_p, pygame.K_ESCAPE):
            self.resume()
            return
        action = self.pause_menu.handle_event(e)
        if action == "resume":
            self.resume()
        elif action == "controls":
            self.state = STATE_CONTROLS
        elif action == "exit":
            self.back_to_menu()
        # «saveload» пока без действия

    def handle_controls_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (
            pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE,
        ):
            self.state = STATE_PAUSED
        elif e.type == pygame.MOUSEBUTTONDOWN:
            self.state = STATE_PAUSED

    def handle_levelclear_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.next_level()
            elif e.key == pygame.K_ESCAPE:
                self.back_to_menu()

    def handle_gameover_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_r:
                self.start_new_game()
            elif e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.back_to_menu()
