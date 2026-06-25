"""Игра «Змейка» на pygame.

Управление:
    - Стрелки или WASD — движение
    - Пробел — пауза
    - R — рестарт после проигрыша
    - Esc / закрытие окна — выход
"""

import random
import sys

import pygame

# --- Настройки игры ---
CELL = 25            # размер одной клетки в пикселях
COLS = 24            # количество клеток по горизонтали
ROWS = 20            # количество клеток по вертикали
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL
HUD = 40             # высота нижней панели со счётом
FPS = 12             # скорость игры (кадров/шагов в секунду)

# Цвета (R, G, B)
BG_COLOR = (30, 30, 46)
GRID_COLOR = (39, 41, 61)
SNAKE_COLOR = (166, 227, 161)
HEAD_COLOR = (148, 226, 213)
FOOD_COLOR = (243, 139, 168)
TEXT_COLOR = (205, 214, 244)


class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD))
        pygame.display.set_caption("Змейка")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Helvetica", 18)
        self.big_font = pygame.font.SysFont("Helvetica", 32, bold=True)
        self.reset()

    def reset(self):
        start_x, start_y = COLS // 2, ROWS // 2
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
            (x, y) for x in range(COLS) for y in range(ROWS)
        } - set(self.snake)
        self.food = random.choice(tuple(free)) if free else None

    def handle_input(self, event):
        if event.type == pygame.QUIT:
            self.quit()
        if event.type != pygame.KEYDOWN:
            return

        key = event.key
        if key == pygame.K_ESCAPE:
            self.quit()
        if key == pygame.K_r and self.game_over:
            self.reset()
            return
        if key == pygame.K_SPACE:
            if not self.game_over:
                self.paused = not self.paused
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

    def step(self):
        if self.paused or self.game_over:
            return

        self.direction = self.pending_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # Столкновение со стеной
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            self.game_over = True
            return
        # Столкновение с собой
        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            self.place_food()
        else:
            self.snake.pop()  # двигаемся: убираем хвост

    def draw(self):
        self.screen.fill(BG_COLOR)

        # Сетка
        for x in range(0, WIDTH, CELL):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT + 1, CELL):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y))

        # Еда
        if self.food:
            self.draw_cell(self.food, FOOD_COLOR)

        # Змейка
        for i, cell in enumerate(self.snake):
            self.draw_cell(cell, HEAD_COLOR if i == 0 else SNAKE_COLOR)

        # Панель со счётом
        pygame.draw.rect(self.screen, GRID_COLOR, (0, HEIGHT, WIDTH, HUD))
        score = self.font.render(f"Счёт: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score, (10, HEIGHT + (HUD - score.get_height()) // 2))

        if self.paused:
            self.center_text("ПАУЗА", "Пробел — продолжить")
        elif self.game_over:
            self.center_text(
                f"Игра окончена! Счёт: {self.score}", "R — рестарт"
            )

        pygame.display.flip()

    def draw_cell(self, cell, color):
        x, y = cell
        pad = 2
        rect = pygame.Rect(
            x * CELL + pad, y * CELL + pad, CELL - 2 * pad, CELL - 2 * pad
        )
        pygame.draw.rect(self.screen, color, rect, border_radius=4)

    def center_text(self, title, subtitle):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 30, 46, 180))
        self.screen.blit(overlay, (0, 0))

        t = self.big_font.render(title, True, TEXT_COLOR)
        s = self.font.render(subtitle, True, TEXT_COLOR)
        self.screen.blit(
            t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 30)
        )
        self.screen.blit(
            s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 12)
        )

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            for event in pygame.event.get():
                self.handle_input(event)
            self.step()
            self.draw()
            self.clock.tick(FPS)


def main():
    SnakeGame().run()


if __name__ == "__main__":
    main()
