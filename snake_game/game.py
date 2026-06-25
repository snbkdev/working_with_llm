"""Игровая логика и отрисовка «Змейки»."""

import random
import sys

import pygame

import config as c
from button import Button
from scores import load_scores, save_score


class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((c.WIDTH, c.TOPBAR + c.HEIGHT))
        pygame.display.set_caption("Змейка")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Helvetica", 18)
        self.small_font = pygame.font.SysFont("Helvetica", 15)
        self.bar_font = pygame.font.SysFont("Helvetica", 18, bold=True)
        self.big_font = pygame.font.SysFont("Helvetica", 30, bold=True)

        self.scores = load_scores()
        self.best = self.scores[0]["score"] if self.scores else 0

        # Кнопки в верхней панели
        btn_y = (c.TOPBAR - 32) // 2
        self.pause_btn = Button(
            (c.WIDTH - 200, btn_y, 110, 32), "Пауза", self.toggle_pause
        )
        self.exit_btn = Button(
            (c.WIDTH - 80, btn_y, 66, 32), "Выход", self.quit,
            text_color=c.BTN_EXIT,
        )
        self.buttons = [self.pause_btn, self.exit_btn]

        self.reset()

    def reset(self):
        start_x, start_y = c.COLS // 2, c.ROWS // 2
        # Змейка — список клеток (x, y), голова — первый элемент
        self.snake = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y),
        ]
        self.direction = (1, 0)
        self.pending_direction = (1, 0)
        self.score = 0
        self.paused = False
        self.game_over = False
        self.place_food()

    def place_food(self):
        free = {
            (x, y) for x in range(c.COLS) for y in range(c.ROWS)
        } - set(self.snake)
        self.food = random.choice(tuple(free)) if free else None

    def toggle_pause(self):
        if not self.game_over:
            self.paused = not self.paused
        self.pause_btn.label = "Продолжить" if self.paused else "Пауза"

    # --- Ввод ---
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.quit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.handle_click(event.pos):
                    return
        if event.type != pygame.KEYDOWN:
            return

        key = event.key
        if key == pygame.K_ESCAPE:
            self.quit()
        if key == pygame.K_r and self.game_over:
            self.reset()
            return
        if key == pygame.K_SPACE:
            self.toggle_pause()
            return

        directions = {
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
        }
        if key in directions:
            nx, ny = directions[key]
            # Запрет разворота на 180 градусов
            if (nx, ny) != (-self.direction[0], -self.direction[1]):
                self.pending_direction = (nx, ny)

    # --- Логика ---
    def step(self):
        if self.paused or self.game_over:
            return

        self.direction = self.pending_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # Столкновение со стеной или с собой
        if not (0 <= new_head[0] < c.COLS and 0 <= new_head[1] < c.ROWS):
            self.end_game()
            return
        if new_head in self.snake:
            self.end_game()
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            self.place_food()
        else:
            self.snake.pop()  # двигаемся: убираем хвост

    def end_game(self):
        self.game_over = True
        self.scores = save_score(self.score)
        self.best = self.scores[0]["score"] if self.scores else 0

    # --- Отрисовка ---
    def draw(self):
        self.screen.fill(c.BG_COLOR)
        self.draw_topbar()
        self.draw_playfield()
        pygame.display.flip()

    def draw_topbar(self):
        mouse = pygame.mouse.get_pos()
        pygame.draw.rect(self.screen, c.BAR_COLOR, (0, 0, c.WIDTH, c.TOPBAR))
        pygame.draw.line(
            self.screen, c.BAR_BORDER, (0, c.TOPBAR), (c.WIDTH, c.TOPBAR), 2
        )
        cy = c.TOPBAR // 2

        title = self.bar_font.render("🐍 Змейка", True, c.ACCENT_COLOR)
        self.screen.blit(title, (14, cy - title.get_height() // 2))

        score = self.bar_font.render(f"Счёт: {self.score}", True, c.TEXT_COLOR)
        self.screen.blit(score, (130, cy - score.get_height() // 2))

        best = self.small_font.render(
            f"Рекорд: {self.best}", True, c.MUTED_COLOR
        )
        self.screen.blit(best, (245, cy - best.get_height() // 2))

        for btn in self.buttons:
            btn.draw(self.screen, self.small_font, mouse)

    def draw_playfield(self):
        for x in range(0, c.WIDTH + 1, c.CELL):
            pygame.draw.line(
                self.screen, c.GRID_COLOR,
                (x, c.TOPBAR), (x, c.TOPBAR + c.HEIGHT),
            )
        for y in range(0, c.HEIGHT + 1, c.CELL):
            pygame.draw.line(
                self.screen, c.GRID_COLOR,
                (0, c.TOPBAR + y), (c.WIDTH, c.TOPBAR + y),
            )

        if self.food:
            self.draw_cell(self.food, c.FOOD_COLOR)
        for i, cell in enumerate(self.snake):
            self.draw_cell(cell, c.HEAD_COLOR if i == 0 else c.SNAKE_COLOR)

        if self.paused:
            self.draw_overlay("ПАУЗА", "Пробел или «Продолжить»")
        elif self.game_over:
            self.draw_gameover()

    def draw_cell(self, cell, color):
        x, y = cell
        pad = 2
        rect = pygame.Rect(
            x * c.CELL + pad, c.TOPBAR + y * c.CELL + pad,
            c.CELL - 2 * pad, c.CELL - 2 * pad,
        )
        pygame.draw.rect(self.screen, color, rect, border_radius=4)

    def _dim(self):
        overlay = pygame.Surface((c.WIDTH, c.HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 30, 46, 200))
        self.screen.blit(overlay, (0, c.TOPBAR))

    def draw_overlay(self, title, subtitle):
        self._dim()
        cy = c.TOPBAR + c.HEIGHT // 2
        t = self.big_font.render(title, True, c.TEXT_COLOR)
        s = self.font.render(subtitle, True, c.MUTED_COLOR)
        self.screen.blit(t, (c.WIDTH // 2 - t.get_width() // 2, cy - 30))
        self.screen.blit(s, (c.WIDTH // 2 - s.get_width() // 2, cy + 12))

    def draw_gameover(self):
        self._dim()
        top = c.TOPBAR + 40

        title = self.big_font.render(
            f"Игра окончена! Счёт: {self.score}", True, c.TEXT_COLOR
        )
        self.screen.blit(title, (c.WIDTH // 2 - title.get_width() // 2, top))

        hint = self.small_font.render("R — рестарт", True, c.MUTED_COLOR)
        self.screen.blit(hint, (c.WIDTH // 2 - hint.get_width() // 2, top + 40))

        # Таблица рекордов
        heading = self.font.render("🏆 Таблица рекордов", True, c.ACCENT_COLOR)
        hy = top + 80
        self.screen.blit(heading, (c.WIDTH // 2 - heading.get_width() // 2, hy))

        col_x = c.WIDTH // 2 - 160
        row_y = hy + 36
        head_dt = self.small_font.render("Дата / время", True, c.MUTED_COLOR)
        head_sc = self.small_font.render("Счёт", True, c.MUTED_COLOR)
        self.screen.blit(head_dt, (col_x, row_y))
        self.screen.blit(head_sc, (col_x + 260, row_y))
        row_y += 26

        for i, entry in enumerate(self.scores[:8], start=1):
            color = c.ACCENT_COLOR if i == 1 else c.TEXT_COLOR
            dt = self.small_font.render(
                f"{i}.  {entry['datetime']}", True, color
            )
            sc = self.small_font.render(str(entry["score"]), True, color)
            self.screen.blit(dt, (col_x, row_y))
            self.screen.blit(sc, (col_x + 260, row_y))
            row_y += 24

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            for event in pygame.event.get():
                self.handle_event(event)
            self.step()
            self.draw()
            self.clock.tick(c.FPS)
