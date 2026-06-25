"""Игровой цикл Battle City.

Этап 1: танк игрока (движение, поворот, стрельба) и столкновения со
стенами. Враги и условия победы/поражения добавим на следующих этапах.
"""

import sys

import pygame

import config as c
from bullet import Bullet
from level import Level
from tank import Tank


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
        pygame.display.set_caption("Battle City")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Helvetica", 18, bold=True)
        self.small = pygame.font.SysFont("Helvetica", 13)
        self.reset()

    def reset(self):
        self.level = Level()
        col, row = self.level.player_spawn
        self.player = Tank(col, row, c.UP, is_player=True)
        self.bullets = []
        self.last_shot = 0

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
        self.last_shot = now

    # --- Ввод ---
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.quit()
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
        keys = pygame.key.get_pressed()
        direction = self.read_direction(keys)
        solids = self.level.solid_rects()
        if direction is not None:
            self.player.face(direction)
            self.player.try_move(solids)

        for b in self.bullets:
            b.update()
            if not (0 <= b.x <= c.FIELD_W and 0 <= b.y <= c.FIELD_H):
                b.alive = False
                continue
            if self.level.hit(b.rect):
                b.alive = False
        self.bullets = [b for b in self.bullets if b.alive]

    # --- Отрисовка ---
    def draw(self):
        self.screen.fill(c.BG_COLOR)
        pygame.draw.rect(self.screen, c.FIELD_COLOR, (0, 0, c.FIELD_W, c.FIELD_H))
        self.level.draw(self.screen)
        self.player.draw(self.screen)
        for b in self.bullets:
            b.draw(self.screen)
        self.draw_hud()
        pygame.display.flip()

    def draw_hud(self):
        x = c.FIELD_W
        pygame.draw.rect(self.screen, c.HUD_BG, (x, 0, c.HUD_W, c.HEIGHT))

        title = self.font.render("BATTLE CITY", True, c.HUD_TEXT)
        self.screen.blit(title, (x + (c.HUD_W - title.get_width()) // 2, 24))

        stage = self.small.render("Этап 1: игрок", True, c.ACCENT)
        self.screen.blit(stage, (x + (c.HUD_W - stage.get_width()) // 2, 52))

        lines = [
            "",
            "Управление:",
            "Стрелки / WASD",
            "  — движение",
            "Пробел — огонь",
            "",
            "R — рестарт",
            "Esc — выход",
        ]
        y = 90
        for line in lines:
            surf = self.small.render(line, True, c.HUD_TEXT)
            self.screen.blit(surf, (x + 14, y))
            y += 22

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(c.FPS)
