"""Игровой цикл Battle City.

Этап 2: игрок + враги с простым ИИ. Бой (пуля × танк) и условия
победы/поражения добавим на следующем этапе.
"""

import sys

import pygame

from . import config as c
from .entities.enemy import Enemy
from .entities.tank import Tank
from .menu import Menu
from .sound import Sounds
from .world.level import Level

STATE_MENU = "menu"
STATE_PLAYING = "playing"


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
        pygame.display.set_caption("Battle City")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Helvetica", 18, bold=True)
        self.small = pygame.font.SysFont("Helvetica", 13)
        self.sounds = Sounds(c.SOUND_ENABLED)

        # Начинаем с главного меню; уровень создаётся при «Новой игре»
        self.state = STATE_MENU
        self.menu = Menu()

    def reset(self):
        self.level = Level()
        col, row = self.level.player_spawn
        self.player = Tank(col, row, c.UP, is_player=True)
        self.bullets = []
        self.last_shot = 0

        # Враги
        self.enemies = []
        self.enemies_to_spawn = c.TOTAL_ENEMIES   # сколько ещё появится
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
        """Дискретные клавиши в режиме игры (стрельба, рестарт, в меню)."""
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
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
            if self.level.hit(b.rect):
                b.alive = False
                self.sounds.play_hit()
                continue
            # Попадание в танк (звук есть; разрушение врага — отдельный этап)
            if self.bullet_hits_tank(b):
                b.alive = False
                self.sounds.play_hit()
        self.bullets = [b for b in self.bullets if b.alive]

    def bullet_hits_tank(self, b):
        """Пуля игрока попадает во врага, пуля врага — в игрока.
        Возвращает True при попадании (танки пока не уничтожаются)."""
        if b.owner == "player":
            return any(b.rect.colliderect(e.rect) for e in self.enemies)
        return b.rect.colliderect(self.player.rect)

    # --- Отрисовка ---
    def draw(self):
        if self.state == STATE_MENU:
            self.menu.draw(self.screen)
            pygame.display.flip()
            return

        self.screen.fill(c.BG_COLOR)
        pygame.draw.rect(self.screen, c.FIELD_COLOR, (0, 0, c.FIELD_W, c.FIELD_H))
        self.draw_grid()
        self.level.draw(self.screen)
        self.player.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        for b in self.bullets:
            b.draw(self.screen)
        pygame.draw.rect(self.screen, c.FIELD_BORDER, (0, 0, c.FIELD_W, c.FIELD_H), 2)
        self.draw_hud()
        pygame.display.flip()

    def draw_grid(self):
        for x in range(c.TILE, c.FIELD_W, c.TILE):
            pygame.draw.line(self.screen, c.GRID_LINE, (x, 0), (x, c.FIELD_H))
        for y in range(c.TILE, c.FIELD_H, c.TILE):
            pygame.draw.line(self.screen, c.GRID_LINE, (0, y), (c.FIELD_W, y))

    def draw_hud(self):
        x = c.FIELD_W
        pygame.draw.rect(self.screen, c.HUD_BG, (x, 0, c.HUD_W, c.HEIGHT))

        title = self.font.render("BATTLE CITY", True, c.HUD_TEXT)
        self.screen.blit(title, (x + (c.HUD_W - title.get_width()) // 2, 24))

        stage = self.small.render("Этап 2: враги", True, c.ACCENT)
        self.screen.blit(stage, (x + (c.HUD_W - stage.get_width()) // 2, 52))

        # Счётчик оставшихся врагов
        remaining = self.enemies_to_spawn + len(self.enemies)
        label = self.small.render("Врагов осталось:", True, c.HUD_TEXT)
        self.screen.blit(label, (x + 14, 84))
        count = self.font.render(str(remaining), True, c.ACCENT)
        self.screen.blit(count, (x + (c.HUD_W - count.get_width()) // 2, 102))

        lines = [
            "Управление:",
            "Стрелки / WASD",
            "  — движение",
            "Пробел — огонь",
            "",
            "R — рестарт",
            "Esc — в меню",
        ]
        y = 150
        for line in lines:
            surf = self.small.render(line, True, c.HUD_TEXT)
            self.screen.blit(surf, (x + 14, y))
            y += 22

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.quit()
                elif self.state == STATE_MENU:
                    action = self.menu.handle_event(e)
                    if action == "new_game":
                        self.start_new_game()
                    elif action == "quit":
                        self.quit()
                    # «load» и «settings» пока без действия
                else:
                    self.handle_game_event(e)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()
            self.clock.tick(c.FPS)
