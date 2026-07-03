"""Игровая логика и отрисовка «Змейки».

Отрисовка идёт на 60 FPS с интерполяцией между логическими шагами,
поэтому змейка ползёт плавно, а не прыгает по клеткам.
"""

import math
import random
import sys

import pygame

import config as c
from button import Button
from effects import FloatingText, Particle
from music import Music
from scores import load_scores, save_score
from settings import load_settings, save_settings
from sound import Sounds


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# Виды бонусов: цвет и вес при случайном выборе
BONUS_KINDS = {
    "star": {"color": c.BONUS_COLOR, "weight": 3},
    "turtle": {"color": c.TURTLE_COLOR, "weight": 2},
    "scissors": {"color": c.SCISSORS_COLOR, "weight": 2},
    "ghost": {"color": c.GHOST_COLOR, "weight": 2},
}


class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((c.WIDTH, c.TOPBAR + c.HEIGHT))
        pygame.display.set_caption("Змейка")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Helvetica", 19)
        self.small_font = pygame.font.SysFont("Helvetica", 16)
        self.bar_font = pygame.font.SysFont("Helvetica", 19, bold=True)
        self.big_font = pygame.font.SysFont("Helvetica", 32, bold=True)
        self.title_font = pygame.font.SysFont("Helvetica", 46, bold=True)
        self.pop_font = pygame.font.SysFont("Helvetica", 17, bold=True)

        saved = load_settings()
        self.sounds = Sounds(saved.get("sound", c.SOUND_ENABLED))
        self.music = Music(
            saved.get("music", c.MUSIC_ENABLED), c.MUSIC_VOLUME
        )
        self.scores = load_scores()
        self.best = self.scores[0]["score"] if self.scores else 0

        # Игровое поле рисуется на отдельной поверхности: так проще
        # сдвигать его целиком при «тряске» экрана
        self.field = pygame.Surface((c.WIDTH, c.HEIGHT))
        self.bg = self._make_background()
        # Многоразовая поверхность для мягкой тени под змейкой
        self.shadow_surf = pygame.Surface((c.WIDTH, c.HEIGHT), pygame.SRCALPHA)

        # Кнопки в верхней панели
        btn_y = (c.TOPBAR - 32) // 2
        self.pause_btn = Button(
            (c.WIDTH - 200, btn_y, 110, 32), "Пауза", self.toggle_pause
        )
        self.exit_btn = Button(
            (c.WIDTH - 80, btn_y, 66, 32), "Выход", self.quit,
            text_color=c.BTN_EXIT,
        )
        # Переключатели звука и музыки (иконки рисуются поверх)
        self.sound_btn = Button(
            (c.WIDTH - 296, btn_y, 42, 32), "", self.toggle_sound
        )
        self.music_btn = Button(
            (c.WIDTH - 248, btn_y, 42, 32), "", self.toggle_music
        )
        # Кнопка «Начать» по центру стартового экрана
        sb_w, sb_h = 200, 50
        self.start_btn = Button(
            (c.WIDTH // 2 - sb_w // 2, c.TOPBAR + c.HEIGHT - 84,
             sb_w, sb_h),
            "Начать", self.start_game, text_color=c.ACCENT_COLOR,
        )
        # Переключатель сложности на стартовом экране
        self.difficulty = c.DEFAULT_DIFFICULTY
        self.diff_btns = []
        bw, bh, gap = 120, 36, 14
        x0 = c.WIDTH // 2 - (3 * bw + 2 * gap) // 2
        dy = c.TOPBAR + c.HEIGHT - 168
        for i, key in enumerate(("easy", "normal", "hard")):
            btn = Button(
                (x0 + i * (bw + gap), dy, bw, bh),
                c.DIFFICULTIES[key]["label"],
                lambda k=key: self.set_difficulty(k),
            )
            btn.selected = key == self.difficulty
            self.diff_btns.append((key, btn))

        self.started = False
        self.reset()

    @staticmethod
    def _make_background():
        """Шахматная подложка вместо линий сетки."""
        bg = pygame.Surface((c.WIDTH, c.HEIGHT))
        bg.fill(c.BG_COLOR)
        for y in range(c.ROWS):
            for x in range(y % 2, c.COLS, 2):
                pygame.draw.rect(
                    bg, c.BG_CHECKER, (x * c.CELL, y * c.CELL, c.CELL, c.CELL)
                )
        return bg

    def diff(self):
        return c.DIFFICULTIES[self.difficulty]

    def set_difficulty(self, key):
        self.difficulty = key
        for k, btn in self.diff_btns:
            btn.selected = k == key

    def start_game(self):
        self.started = True
        self.last_step = pygame.time.get_ticks()

    def to_menu(self):
        self.started = False
        self.reset()

    def topbar_buttons(self):
        # «Пауза» видна только во время самой игры
        buttons = [self.sound_btn, self.music_btn, self.exit_btn]
        if self.started and not self.game_over:
            buttons.insert(2, self.pause_btn)
        return buttons

    def toggle_sound(self):
        self.sounds.enabled = not self.sounds.enabled
        save_settings(sound=self.sounds.enabled)
        self.sounds.play_eat()  # короткий «бип»-подтверждение при включении

    def toggle_music(self):
        self.music.set_enabled(not self.music.enabled)
        save_settings(music=self.music.enabled)

    def reset(self):
        start_x, start_y = c.COLS // 2, c.ROWS // 2
        # Змейка — список клеток (x, y), голова — первый элемент
        self.snake = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y),
        ]
        self.prev_snake = list(self.snake)
        self.direction = (1, 0)
        self.dir_queue = []
        self.score = 0
        self.eaten = 0
        self.paused = False
        self.game_over = False
        self.pause_btn.label = "Пауза"
        self.bonus = None   # {"kind", "cell", "until"}
        self.rotten = None  # {"cell", "until"}
        self.mouse = None   # {"cell", "prev", "until", "moved_at"}
        self.slow_until = 0
        self.ghost_until = 0
        self.combo = 1
        self.combo_until = 0
        self.particles = []
        self.texts = []
        self.death_at = 0
        self.shake_until = 0
        self.last_step = pygame.time.get_ticks()
        self.place_food()

    def step_interval(self):
        """Интервал шага в мс: сложность, ускорение и эффект черепахи."""
        d = self.diff()
        interval = max(
            d["min_step_ms"], d["step_ms"] - d["accel_ms"] * self.eaten
        )
        if pygame.time.get_ticks() < self.slow_until:
            interval = int(interval * c.SLOW_FACTOR)
        return interval

    def _occupied(self):
        occupied = set(self.snake)
        occupied.add(getattr(self, "food", None))
        for item in (self.bonus, self.rotten, self.mouse):
            if item:
                occupied.add(item["cell"])
        return occupied

    def _free_cells(self):
        occupied = self._occupied()
        return [
            (x, y)
            for x in range(c.COLS) for y in range(c.ROWS)
            if (x, y) not in occupied
        ]

    def place_food(self):
        free = self._free_cells()
        self.food = random.choice(free) if free else None

    def spawn_bonus(self, now):
        free = self._free_cells()
        if not free:
            return
        kinds, weights = [], []
        for kind, info in BONUS_KINDS.items():
            if kind == "scissors" and len(self.snake) < c.SCISSORS_MIN_LEN:
                continue  # резать короткую змейку бессмысленно
            kinds.append(kind)
            weights.append(info["weight"])
        self.bonus = {
            "kind": random.choices(kinds, weights)[0],
            "cell": random.choice(free),
            "until": now + c.BONUS_TIME_MS,
        }

    def spawn_rotten(self, now):
        free = self._free_cells()
        if free:
            self.rotten = {
                "cell": random.choice(free),
                "until": now + c.ROTTEN_TIME_MS,
            }

    def spawn_mouse(self, now):
        free = self._free_cells()
        if free:
            cell = random.choice(free)
            self.mouse = {
                "cell": cell, "prev": cell,
                "until": now + c.MOUSE_TIME_MS, "moved_at": now,
            }

    def move_mouse(self, now):
        """Мышка перебегает на соседнюю клетку, убегая от головы змейки."""
        cell = self.mouse["cell"]
        occupied = self._occupied() - {cell}
        options = [cell]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cell[0] + dx, cell[1] + dy
            if self.diff()["walls"]:
                if not (0 <= nx < c.COLS and 0 <= ny < c.ROWS):
                    continue
            else:
                nx, ny = nx % c.COLS, ny % c.ROWS
            if (nx, ny) not in occupied:
                options.append((nx, ny))

        head = self.snake[0]

        def dist(pos):
            if self.diff()["walls"]:
                dx, dy = pos[0] - head[0], pos[1] - head[1]
            else:
                dx, dy = self._wrap_delta(head, pos)
            return abs(dx) + abs(dy)

        best = max(dist(o) for o in options)
        self.mouse["prev"] = cell
        self.mouse["cell"] = random.choice(
            [o for o in options if dist(o) == best]
        )
        self.mouse["moved_at"] = now

    def toggle_pause(self):
        if self.game_over:
            return
        self.paused = not self.paused
        self.pause_btn.label = "Продолжить" if self.paused else "Пауза"
        self.music.set_paused(self.paused)
        now = pygame.time.get_ticks()
        if self.paused:
            self.pause_started = now
        else:
            # Сдвигаем все таймеры на длительность паузы, чтобы бонусы
            # и эффекты не «сгорали», пока игра стояла
            delta = now - self.pause_started
            for item in (self.bonus, self.rotten, self.mouse):
                if item:
                    item["until"] += delta
            if self.mouse:
                self.mouse["moved_at"] += delta
            for attr in ("slow_until", "ghost_until", "combo_until"):
                setattr(self, attr, getattr(self, attr) + delta)
            # И чтобы змейка не прыгала на клетку вперёд
            self.last_step = now

    # --- Ввод ---
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.quit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            buttons = self.topbar_buttons()
            if not self.started:
                buttons = buttons + [self.start_btn]
                buttons += [btn for _, btn in self.diff_btns]
            for btn in buttons:
                if btn.handle_click(event.pos):
                    return
        if event.type != pygame.KEYDOWN:
            return

        key = event.key
        # Стартовый экран: запуск пробелом/Enter, 1-2-3 — сложность
        if not self.started:
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.start_game()
            elif key in (pygame.K_1, pygame.K_KP1):
                self.set_difficulty("easy")
            elif key in (pygame.K_2, pygame.K_KP2):
                self.set_difficulty("normal")
            elif key in (pygame.K_3, pygame.K_KP3):
                self.set_difficulty("hard")
            elif key == pygame.K_ESCAPE:
                self.quit()
            return

        if key == pygame.K_ESCAPE:
            self.quit()
        if self.game_over:
            if key in (pygame.K_r, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.reset()
            elif key == pygame.K_m:
                self.to_menu()
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
            nd = directions[key]
            # Очередь поворотов: быстрые нажатия «вверх-влево» не теряются,
            # разворот на 180 градусов по-прежнему запрещён
            last = self.dir_queue[-1] if self.dir_queue else self.direction
            if nd != last and nd != (-last[0], -last[1]):
                if len(self.dir_queue) < 3:
                    self.dir_queue.append(nd)

    # --- Логика ---
    def update(self, now, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
        self.texts = [t for t in self.texts if t.update(dt)]
        if not self.started or self.paused or self.game_over:
            return
        if self.bonus and now >= self.bonus["until"]:
            self.bonus = None
        if self.rotten and now >= self.rotten["until"]:
            self.rotten = None
        if self.mouse:
            if now >= self.mouse["until"]:
                self.mouse = None
            elif now - self.mouse["moved_at"] >= c.MOUSE_MOVE_MS:
                self.move_mouse(now)
        if now - self.last_step >= self.step_interval():
            self.last_step = now
            self.step(now)

    def step(self, now):
        if self.dir_queue:
            self.direction = self.dir_queue.pop(0)
        self.prev_snake = list(self.snake)
        hx, hy = self.snake[0]
        dx, dy = self.direction
        nx, ny = hx + dx, hy + dy

        if self.diff()["walls"]:
            # На сложном уровне стены смертельны
            if not (0 <= nx < c.COLS and 0 <= ny < c.ROWS):
                self.end_game(now)
                return
            new_head = (nx, ny)
        else:
            # Проход сквозь стены: выход за край переносит на другую сторону
            new_head = (nx % c.COLS, ny % c.ROWS)

        # Столкновение с телом (если не активен «призрак»)
        if new_head in self.snake and now >= self.ghost_until:
            self.end_game(now)
            return

        self.snake.insert(0, new_head)
        ate = False
        if new_head == self.food:
            ate = True
            self.eat_food(new_head, now)
        elif self.bonus and new_head == self.bonus["cell"]:
            ate = True
            self.eat_bonus(new_head, now)
        elif self.mouse and new_head == self.mouse["cell"]:
            ate = True
            self.eat_mouse(new_head, now)
        if not ate:
            self.snake.pop()  # двигаемся: убираем хвост
        if self.rotten and new_head == self.rotten["cell"]:
            self.eat_rotten(new_head, now)

    def eat_food(self, cell, now):
        # Комбо: успел за отведённое время — множитель растёт
        if now <= self.combo_until:
            self.combo = min(self.combo + 1, c.COMBO_MAX)
        else:
            self.combo = 1
        self.combo_until = now + c.COMBO_WINDOW_MS

        gained = self.combo
        self.score += gained
        self.eaten += 1
        self.sounds.play_eat()
        color = c.FOOD_COLOR if self.combo == 1 else c.BONUS_COLOR
        self.burst(cell, color, 14)
        self.pop_text(cell, f"+{gained}", color)
        # Каждые BONUS_EVERY яблок появляется случайный бонус
        if self.eaten % c.BONUS_EVERY == 0:
            self.spawn_bonus(now)
        # Иногда на поле подбрасывает гнилое яблоко или выбегает мышка
        if not self.rotten and random.random() < c.ROTTEN_CHANCE:
            self.spawn_rotten(now)
        if not self.mouse and random.random() < c.MOUSE_CHANCE:
            self.spawn_mouse(now)
        self.place_food()

    def eat_bonus(self, cell, now):
        kind = self.bonus["kind"]
        color = BONUS_KINDS[kind]["color"]
        self.bonus = None
        self.sounds.play_bonus()
        self.burst(cell, color, 24)

        if kind == "star":
            self.score += c.STAR_POINTS
            self.snake.append(self.snake[-1])  # растит сразу на 2 клетки
            self.pop_text(cell, f"+{c.STAR_POINTS}", color)
            return

        self.score += c.EFFECT_POINTS
        if kind == "turtle":
            self.slow_until = now + c.SLOW_MS
            self.pop_text(cell, "Замедление!", color)
        elif kind == "scissors":
            keep = max(3, len(self.snake) // 2)
            cut = len(self.snake) - keep
            if cut > 0:
                self.burst(self.snake[keep], color, 16)
                self.snake = self.snake[:keep]
                # Подгоняем прежние клетки, чтобы хвост дорисовался плавно
                self.prev_snake = self.prev_snake[:keep]
            self.pop_text(cell, f"−{cut} хвоста!", color)
        elif kind == "ghost":
            self.ghost_until = now + c.GHOST_MS
            self.pop_text(cell, "Призрак!", color)

    def eat_mouse(self, cell, now):
        self.mouse = None
        self.score += c.MOUSE_POINTS
        self.sounds.play_squeak()
        self.burst(cell, c.MOUSE_COLOR, 18)
        self.pop_text(cell, f"+{c.MOUSE_POINTS} Поймал!", c.MOUSE_COLOR)

    def eat_rotten(self, cell, now):
        self.rotten = None
        self.score = max(0, self.score - c.ROTTEN_PENALTY)
        self.combo = 1
        self.combo_until = 0  # комбо сгорает
        keep = max(3, len(self.snake) - c.ROTTEN_SHRINK)
        if keep < len(self.snake):
            self.snake = self.snake[:keep]
            self.prev_snake = self.prev_snake[:keep]
        self.sounds.play_rotten()
        self.burst(cell, c.ROTTEN_COLOR, 16)
        self.pop_text(cell, f"Фу! −{c.ROTTEN_PENALTY}", c.ROTTEN_COLOR)

    def end_game(self, now):
        self.game_over = True
        self.death_at = now
        self.shake_until = now + 400
        self.burst(self.snake[0], c.DANGER_COLOR, 26)
        self.sounds.play_crash()
        self.scores = save_score(self.score, self.diff()["label"])
        self.best = self.scores[0]["score"] if self.scores else 0

    # --- Эффекты ---
    def burst(self, cell, color, count):
        x, y = self.cell_center(cell)
        self.particles += [Particle(x, y, color) for _ in range(count)]

    def pop_text(self, cell, text, color):
        x, y = self.cell_center(cell)
        self.texts.append(FloatingText(x, y, text, color, self.pop_font))

    # --- Отрисовка ---
    @staticmethod
    def cell_center(cell):
        return (cell[0] * c.CELL + c.CELL / 2, cell[1] * c.CELL + c.CELL / 2)

    def draw(self, now):
        field = self.field
        field.blit(self.bg, (0, 0))
        if self.started:
            if self.diff()["walls"]:
                pygame.draw.rect(
                    field, c.WALL_COLOR, (0, 0, c.WIDTH, c.HEIGHT), 3
                )
            self.draw_food(field, now)
            self.draw_rotten(field, now)
            self.draw_mouse(field, now)
            self.draw_bonus(field, now)
            self.draw_snake(field, now)
            for p in self.particles:
                p.draw(field)
            for t in self.texts:
                t.draw(field)
            if not self.paused and not self.game_over:
                self.draw_hud(field, now)

        if not self.started:
            self.draw_start(field, now)
        elif self.paused:
            self.draw_overlay(field, "ПАУЗА", "Пробел или «Продолжить»")
        elif self.game_over:
            self.draw_gameover(field)
            self.draw_death_flash(field, now)

        self.screen.fill(c.BG_COLOR)
        ox = oy = 0.0
        if now < self.shake_until:
            amp = 6 * (self.shake_until - now) / 400
            ox = random.uniform(-amp, amp)
            oy = random.uniform(-amp, amp)
        self.screen.blit(field, (ox, c.TOPBAR + oy))
        self.draw_topbar()
        if not self.started:
            # Кнопки сложности и «Начать» — поверх, в координатах окна
            mouse = pygame.mouse.get_pos()
            for _, btn in self.diff_btns:
                btn.draw(self.screen, self.small_font, mouse)
            desc = self.small_font.render(
                self.diff()["desc"], True,
                c.DANGER_COLOR if self.diff()["walls"] else c.MUTED_COLOR,
            )
            self.screen.blit(
                desc,
                (c.WIDTH // 2 - desc.get_width() // 2,
                 self.diff_btns[0][1].rect.bottom + 8),
            )
            self.start_btn.draw(self.screen, self.font, mouse)
            hint = self.small_font.render(
                "или нажмите Пробел", True, c.TEXT_COLOR
            )
            hint.set_alpha(150 + int(90 * math.sin(now * 0.004)))
            self.screen.blit(
                hint,
                (c.WIDTH // 2 - hint.get_width() // 2,
                 self.start_btn.rect.bottom + 12),
            )
        pygame.display.flip()

    def draw_topbar(self):
        mouse = pygame.mouse.get_pos()
        pygame.draw.rect(self.screen, c.BAR_COLOR, (0, 0, c.WIDTH, c.TOPBAR))
        pygame.draw.line(
            self.screen, c.BAR_BORDER, (0, c.TOPBAR), (c.WIDTH, c.TOPBAR), 2
        )
        cy = c.TOPBAR // 2

        def put(surface, x):
            self.screen.blit(surface, (x, cy - surface.get_height() // 2))

        # Мини-змейка вместо эмодзи (эмодзи в SysFont не рендерятся)
        for k in range(6, -1, -1):
            px = 16 + (6 - k) * 5
            py = cy + math.sin(k * 0.9) * 4
            color = (c.SNAKE_HEAD if k == 0
                     else _lerp_color(c.SNAKE_BODY, c.SNAKE_TAIL, k / 6))
            pygame.draw.circle(
                self.screen, color, (px, py), 6 if k == 0 else 5
            )
        put(self.bar_font.render("Змейка", True, c.ACCENT_COLOR), 60)
        put(self.bar_font.render(f"Счёт: {self.score}", True, c.TEXT_COLOR), 150)
        put(self.small_font.render(f"Рекорд: {self.best}", True, c.MUTED_COLOR), 270)
        speed = self.diff()["step_ms"] / self.step_interval()
        speed_color = c.TURTLE_COLOR if speed < 1 else c.BONUS_RING
        put(self.small_font.render(f"×{speed:.1f}", True, speed_color), 390)

        for btn in self.topbar_buttons():
            btn.draw(self.screen, self.small_font, mouse)
        self._draw_speaker_icon(
            self.screen, self.sound_btn.rect, self.sounds.enabled
        )
        self._draw_note_icon(
            self.screen, self.music_btn.rect, self.music.enabled
        )

    @staticmethod
    def _draw_speaker_icon(surf, rect, on):
        """Динамик: с волнами — звук включён, перечёркнут — выключен."""
        x, y = rect.center
        color = c.TEXT_COLOR if on else c.MUTED_COLOR
        pygame.draw.polygon(surf, color, [
            (x - 9, y - 3), (x - 5, y - 3), (x, y - 8),
            (x, y + 8), (x - 5, y + 3), (x - 9, y + 3),
        ])
        if on:
            pygame.draw.arc(surf, color, (x - 1, y - 5, 8, 10), -0.9, 0.9, 2)
            pygame.draw.arc(surf, color, (x + 1, y - 8, 11, 16), -1.0, 1.0, 2)
        else:
            pygame.draw.line(
                surf, c.DANGER_COLOR, (x - 10, y + 9), (x + 10, y - 9), 2
            )

    @staticmethod
    def _draw_note_icon(surf, rect, on):
        """Нота: музыка включена; перечёркнута — выключена."""
        x, y = rect.center
        color = c.TEXT_COLOR if on else c.MUTED_COLOR
        pygame.draw.circle(surf, color, (x - 3, y + 5), 4)
        pygame.draw.line(surf, color, (x + 1, y + 5), (x + 1, y - 7), 2)
        pygame.draw.line(surf, color, (x + 1, y - 7), (x + 8, y - 4), 3)
        if not on:
            pygame.draw.line(
                surf, c.DANGER_COLOR, (x - 10, y + 9), (x + 10, y - 9), 2
            )

    def draw_hud(self, surf, now):
        """Чипы активных эффектов (слева) и комбо (справа) поверх поля."""
        y = 8
        for kind, until in (
            ("turtle", self.slow_until), ("ghost", self.ghost_until)
        ):
            if now >= until:
                continue
            chip = pygame.Surface((86, 28), pygame.SRCALPHA)
            pygame.draw.rect(
                chip, (*c.BAR_COLOR, 200), chip.get_rect(), border_radius=8
            )
            self.draw_bonus_icon(chip, kind, 17, 14, 9, now)
            label = self.small_font.render(
                f"{(until - now) / 1000:.0f} с", True, c.TEXT_COLOR
            )
            chip.blit(label, (36, 14 - label.get_height() // 2))
            surf.blit(chip, (8, y))
            y += 34

        if self.combo >= 2 and now < self.combo_until:
            label = self.pop_font.render(
                f"Комбо ×{self.combo}", True, c.BONUS_COLOR
            )
            w = label.get_width() + 20
            chip = pygame.Surface((w, 32), pygame.SRCALPHA)
            pygame.draw.rect(
                chip, (*c.BAR_COLOR, 200), chip.get_rect(), border_radius=8
            )
            chip.blit(label, (10, 5))
            # Полоска-таймер: сколько осталось, чтобы удержать комбо
            frac = (self.combo_until - now) / c.COMBO_WINDOW_MS
            pygame.draw.rect(
                chip, c.BONUS_COLOR, (10, 26, int((w - 20) * frac), 3),
                border_radius=2,
            )
            surf.blit(chip, (c.WIDTH - 8 - w, 8))

    # --- Змейка ---
    @staticmethod
    def _wrap_delta(a, b):
        """Кратчайший сдвиг между клетками с учётом прохода сквозь стены."""
        dx = ((b[0] - a[0] + c.COLS // 2) % c.COLS) - c.COLS // 2
        dy = ((b[1] - a[1] + c.ROWS // 2) % c.ROWS) - c.ROWS // 2
        return dx, dy

    def _snake_path(self, now):
        """Точки тела в пикселях (голова — первая), без разрывов на краях.

        Тело лежит на «рельсах» из клеток предыдущего шага: между шагами
        двигаются только кончик головы и кончик хвоста. Поэтому на
        поворотах углы не срезаются и тело не дёргается.
        """
        if self.started and not self.paused and not self.game_over:
            t = min(1.0, (now - self.last_step) / self.step_interval())
        else:
            t = 1.0

        if self.snake[0] == self.prev_snake[0]:
            # Шага ещё не было (старт/рестарт) — статичная поза
            cells = self.snake
            retract = 0
        else:
            cells = [self.snake[0]] + self.prev_snake
            retract = len(self.prev_snake) + 1 - len(self.snake)

        # Разворачиваем путь в непрерывные координаты: соседние точки
        # всегда рядом, даже если между ними край поля
        ux, uy = float(cells[0][0]), float(cells[0][1])
        u = [(ux, uy)]
        for k in range(1, len(cells)):
            dx, dy = self._wrap_delta(cells[k - 1], cells[k])
            ux, uy = ux + dx, uy + dy
            u.append((ux, uy))

        pts = list(u)
        if cells is not self.snake:
            # Кончик головы выдвигается из первой клетки тела
            pts[0] = (
                u[1][0] + (u[0][0] - u[1][0]) * t,
                u[1][1] + (u[0][1] - u[1][1]) * t,
            )
        if retract > 0:
            # Кончик хвоста втягивается к предыдущей клетке
            pts[-1] = (
                u[-1][0] + (u[-2][0] - u[-1][0]) * t,
                u[-1][1] + (u[-2][1] - u[-1][1]) * t,
            )
        return [
            (x * c.CELL + c.CELL / 2, y * c.CELL + c.CELL / 2)
            for x, y in pts
        ]

    def draw_snake(self, surf, now):
        ghost = now < self.ghost_until
        if ghost:
            # «Призрак»: тело рисуется полупрозрачным, в конце — мигает
            target = pygame.Surface((c.WIDTH, c.HEIGHT), pygame.SRCALPHA)
            self._render_snake(target, now, shadow=False)
            left = self.ghost_until - now
            alpha = 150
            if left < 1500:
                alpha = 150 + int(70 * math.sin(now * 0.02))
            target.set_alpha(alpha)
            surf.blit(target, (0, 0))
        else:
            self._render_snake(surf, now, shadow=True)

    @staticmethod
    def _chaikin(pts, iterations):
        """Срезание углов (алгоритм Чайкина): ломаная становится плавной
        кривой, змейка огибает повороты дугой, а не прямым углом."""
        for _ in range(iterations):
            if len(pts) < 3:
                break
            out = [pts[0]]
            for i in range(len(pts) - 1):
                (px, py), (qx, qy) = pts[i], pts[i + 1]
                out.append((px * 0.75 + qx * 0.25, py * 0.75 + qy * 0.25))
                out.append((px * 0.25 + qx * 0.75, py * 0.25 + qy * 0.75))
            out.append(pts[-1])
            pts = out
        return pts

    def _render_snake(self, surf, now, shadow=True):
        raw = self._snake_path(now)
        iters = 2 if len(raw) <= 120 else 1  # для очень длинной — экономнее
        pts = self._chaikin(raw, iters)
        moving = self.started and not self.paused and not self.game_over
        self._draw_body(
            surf, pts, (c.CELL - 8) / 2, now,
            wrap=True, shadow=shadow,
            fallback_dir=self.direction,
            wiggle=1.6 if moving else 0.0,
        )

    def _draw_body(self, surf, pts, body_r, now, wrap=True, shadow=True,
                   fallback_dir=(1, 0), wiggle=0.0):
        """Тело змейки по цепочке точек (голова — первая).

        Ширина сужается к хвосту, цвет переливается от головы к хвосту,
        снизу мягкая тень, на морде — глаза и язычок.
        """
        n = len(pts)
        if n < 2:
            return

        # Лёгкое извивание при движении (кончики не трогаем)
        if wiggle:
            waved = [pts[0]]
            for k in range(1, n - 1):
                x, y = pts[k]
                tx = pts[k + 1][0] - pts[k - 1][0]
                ty = pts[k + 1][1] - pts[k - 1][1]
                d = math.hypot(tx, ty)
                if d > 1e-6:
                    fade = min(1.0, k / 6, (n - 1 - k) / 6)
                    off = math.sin(k * 0.45 + now * 0.006) * wiggle * fade
                    x, y = x - ty / d * off, y + tx / d * off
                waved.append((x, y))
            waved.append(pts[-1])
            pts = waved

        # Профиль: радиус и цвет каждой точки от головы к хвосту
        samples = []
        for k, (x, y) in enumerate(pts):
            frac = k / (n - 1)
            if frac < 0.12:
                r = body_r * (1.18 - 0.18 * frac / 0.12)  # голова шире
            elif frac < 0.6:
                r = body_r
            else:
                r = body_r * (1 - 0.62 * (frac - 0.6) / 0.4)  # хвост тоньше
            if frac < 0.15:
                color = _lerp_color(c.SNAKE_HEAD, c.SNAKE_BODY, frac / 0.15)
            else:
                color = _lerp_color(
                    c.SNAKE_BODY, c.SNAKE_TAIL, (frac - 0.15) / 0.85
                )
            samples.append((x, y, r, color))

        # Раскладываем по экрану: часть, пересекающую край, дублируем
        # с противоположной стороны (проход сквозь стены без обрывов)
        draws = []
        margin = body_r * 2.5
        for i in range(n - 1, -1, -1):
            x, y, r, color = samples[i]
            if wrap:
                sx = -math.floor(x / c.WIDTH) * c.WIDTH
                sy = -math.floor(y / c.HEIGHT) * c.HEIGHT
            else:
                sx = sy = 0.0
            x, y = x + sx, y + sy
            if i + 1 < n:
                qx = samples[i + 1][0] + sx
                qy = samples[i + 1][1] + sy
                w = max(2, int(min(r, samples[i + 1][2]) * 2))
            else:
                qx, qy, w = x, y, 0
            offsets = {(0.0, 0.0)}
            if wrap:
                if min(x, qx) < margin:
                    offsets.add((c.WIDTH, 0.0))
                if max(x, qx) > c.WIDTH - margin:
                    offsets.add((-c.WIDTH, 0.0))
                if min(y, qy) < margin:
                    offsets.add((0.0, c.HEIGHT))
                if max(y, qy) > c.HEIGHT - margin:
                    offsets.add((0.0, -c.HEIGHT))
            draws.append((i, x, y, qx, qy, w, r, color, offsets))

        # Мягкая тень под телом
        if shadow:
            sh = self.shadow_surf
            sh.fill((0, 0, 0, 0))
            for i, x, y, qx, qy, w, r, _color, offsets in draws:
                for ox, oy in offsets:
                    if w:
                        pygame.draw.line(
                            sh, (12, 12, 22),
                            (x + ox + 3, y + oy + 4),
                            (qx + ox + 3, qy + oy + 4), w,
                        )
                    pygame.draw.circle(
                        sh, (12, 12, 22), (x + ox + 3, y + oy + 4), r
                    )
            sh.set_alpha(60)
            surf.blit(sh, (0, 0))

        # Тело: от хвоста к голове, чтобы голова оказалась сверху
        heads = []
        for i, x, y, qx, qy, w, r, color, offsets in draws:
            for ox, oy in offsets:
                if w:
                    pygame.draw.line(
                        surf, color, (x + ox, y + oy), (qx + ox, qy + oy), w
                    )
                pygame.draw.circle(surf, color, (x + ox, y + oy), r)
                if i == 0:
                    heads.append((x + ox, y + oy, r))

        # Взгляд — куда фактически движется кончик головы
        j = min(3, n - 1)
        hdx, hdy = pts[0][0] - pts[j][0], pts[0][1] - pts[j][1]
        d = math.hypot(hdx, hdy)
        if d < 1e-6:
            hdx, hdy = fallback_dir
        else:
            hdx, hdy = hdx / d, hdy / d
        for hx, hy, hr in heads:
            self._draw_face(surf, hx, hy, hr, hdx, hdy, now)

    def _draw_face(self, surf, hx, hy, r, dx, dy, now):
        px, py = -dy, dx  # перпендикуляр к направлению взгляда
        # Язычок периодически высовывается и прячется
        phase = now % 2800
        if phase < 340:
            k = math.sin(math.pi * phase / 340)
            bx, by = hx + dx * r * 0.9, hy + dy * r * 0.9
            tx, ty = hx + dx * (r * 0.9 + 8 * k), hy + dy * (r * 0.9 + 8 * k)
            pygame.draw.line(surf, c.TONGUE_COLOR, (bx, by), (tx, ty), 2)
            for side in (-1, 1):
                pygame.draw.line(
                    surf, c.TONGUE_COLOR, (tx, ty),
                    (tx + (dx + px * side) * 3 * k,
                     ty + (dy + py * side) * 3 * k), 2,
                )
        # Глаза (изредка моргают)
        blink = (now % 4300) < 140
        for side in (-1, 1):
            ex = hx + dx * r * 0.35 + px * r * 0.5 * side
            ey = hy + dy * r * 0.35 + py * r * 0.5 * side
            if blink:
                pygame.draw.line(
                    surf, c.EYE_PUPIL,
                    (ex - px * 2.5, ey - py * 2.5),
                    (ex + px * 2.5, ey + py * 2.5), 2,
                )
            else:
                pygame.draw.circle(surf, c.EYE_WHITE, (ex, ey), r * 0.32)
                pygame.draw.circle(
                    surf, c.EYE_PUPIL,
                    (ex + dx * 1.5, ey + dy * 1.5), max(1.5, r * 0.17),
                )

    # --- Еда и бонусы ---
    _glow_cache = {}

    @classmethod
    def _glow(cls, surf, pos, color, radius):
        """Мягкое свечение: плавно гаснет к краю и добавляется к фону
        (аддитивно), поэтому не перекрывает клетчатую подложку."""
        radius = max(4, int(radius))
        key = (color, radius)
        glow = cls._glow_cache.get(key)
        if glow is None:
            glow = pygame.Surface((radius * 2, radius * 2))
            for i in range(radius, 0, -2):
                k = 0.30 * (1 - i / radius) ** 2
                col = tuple(int(ch * k) for ch in color)
                pygame.draw.circle(glow, col, (radius, radius), i)
            cls._glow_cache[key] = glow
        surf.blit(
            glow, (pos[0] - radius, pos[1] - radius),
            special_flags=pygame.BLEND_RGB_ADD,
        )

    def draw_food(self, surf, now):
        if not self.food:
            return
        x, y = self.cell_center(self.food)
        r = c.CELL * 0.36 + math.sin(now * 0.006) * 1.5  # «дыхание» яблока
        self._glow(surf, (x, y), c.FOOD_COLOR, int(r * 2.1))
        pygame.draw.circle(surf, c.FOOD_COLOR, (x, y + 1), r)
        pygame.draw.circle(
            surf, c.FOOD_SHINE,
            (x - r * 0.35, y - r * 0.3), max(2, int(r * 0.28)),
        )
        pygame.draw.line(surf, c.STEM_COLOR, (x, y - r), (x + 2, y - r - 5), 2)
        leaf = pygame.Rect(0, 0, 10, 6)
        leaf.center = (x + 7, y - r - 4)
        pygame.draw.ellipse(surf, c.LEAF_COLOR, leaf)

    @staticmethod
    def _star_points(x, y, r, rot):
        pts = []
        for k in range(10):
            ang = rot + k * math.pi / 5 - math.pi / 2
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
        return pts

    def draw_bonus_icon(self, surf, kind, x, y, r, now):
        """Иконка бонуса/добычи: поле, чипы эффектов и легенда в меню."""
        color = BONUS_KINDS[kind]["color"] if kind in BONUS_KINDS else None
        if kind == "star":
            pygame.draw.polygon(
                surf, color, self._star_points(x, y, r, now * 0.002)
            )
        elif kind == "turtle":
            # Панцирь с узором, голова и лапки
            for side in (-1, 1):
                pygame.draw.circle(
                    surf, color, (x - r * 0.45 * side, y + r * 0.75), r * 0.28
                )
            pygame.draw.circle(surf, color, (x + r * 0.95, y - r * 0.1), r * 0.38)
            pygame.draw.circle(surf, _lerp_color(color, c.BG_COLOR, 0.25),
                               (x, y), r * 0.95)
            pygame.draw.circle(surf, color, (x, y), r * 0.55)
        elif kind == "scissors":
            # Два лезвия крест-накрест и кольца-ручки
            pygame.draw.line(
                surf, color,
                (x - r * 0.75, y - r), (x + r * 0.45, y + r * 0.5), 3,
            )
            pygame.draw.line(
                surf, color,
                (x + r * 0.75, y - r), (x - r * 0.45, y + r * 0.5), 3,
            )
            for side in (-1, 1):
                pygame.draw.circle(
                    surf, color,
                    (x + r * 0.6 * side, y + r * 0.72), r * 0.3, 2,
                )
        elif kind == "ghost":
            # Привидение: купол, юбка с волнами и глаза
            gr = r * 0.78
            pygame.draw.circle(surf, color, (x, y - r * 0.18), gr)
            pygame.draw.rect(
                surf, color, (x - gr, y - r * 0.18, gr * 2, r * 0.75)
            )
            for k in (-1, 0, 1):
                pygame.draw.circle(
                    surf, color, (x + k * gr * 0.66, y + r * 0.55), gr * 0.34
                )
            for side in (-1, 1):
                pygame.draw.circle(
                    surf, c.EYE_PUPIL,
                    (x + side * gr * 0.4, y - r * 0.25), r * 0.16,
                )
        elif kind == "apple":
            pygame.draw.circle(surf, c.FOOD_COLOR, (x, y + 1), r * 0.9)
            pygame.draw.circle(
                surf, c.FOOD_SHINE,
                (x - r * 0.3, y - r * 0.2), max(1, int(r * 0.25)),
            )
            leaf = pygame.Rect(0, 0, r * 0.8, r * 0.5)
            leaf.center = (x + r * 0.45, y - r * 0.85)
            pygame.draw.ellipse(surf, c.LEAF_COLOR, leaf)
        elif kind == "rotten":
            # Мятое яблоко болотного цвета с пятнами
            pygame.draw.circle(surf, c.ROTTEN_COLOR, (x, y + 1), r * 0.9)
            pygame.draw.circle(
                surf, c.ROTTEN_DARK, (x - r * 0.35, y - r * 0.1), r * 0.25
            )
            pygame.draw.circle(
                surf, c.ROTTEN_DARK, (x + r * 0.3, y + r * 0.4), r * 0.2
            )
            pygame.draw.line(
                surf, c.STEM_COLOR, (x, y - r * 0.8), (x + 1, y - r * 1.2), 2
            )
        elif kind == "mouse":
            # Мышка: тельце, уши, глаза и хвостик
            for side in (-1, 1):
                pygame.draw.circle(
                    surf, c.MOUSE_COLOR,
                    (x + side * r * 0.45, y - r * 0.55), r * 0.4,
                )
                pygame.draw.circle(
                    surf, c.MOUSE_EAR,
                    (x + side * r * 0.45, y - r * 0.55), r * 0.22,
                )
            body = pygame.Rect(0, 0, r * 1.9, r * 1.4)
            body.center = (x, y + r * 0.1)
            pygame.draw.ellipse(surf, c.MOUSE_COLOR, body)
            pygame.draw.line(
                surf, c.MOUSE_COLOR,
                (x + r * 0.9, y + r * 0.3), (x + r * 1.7, y - r * 0.15), 2,
            )
            for side in (-1, 1):
                pygame.draw.circle(
                    surf, c.EYE_PUPIL,
                    (x + side * r * 0.35, y - r * 0.1), max(1, r * 0.13),
                )
            pygame.draw.circle(
                surf, c.FOOD_COLOR, (x, y + r * 0.25), max(1, r * 0.12)
            )

    def draw_rotten(self, surf, now):
        if not self.rotten:
            return
        left = self.rotten["until"] - now
        if left < 1500 and (now // 160) % 2 == 0:
            return
        x, y = self.cell_center(self.rotten["cell"])
        self.draw_bonus_icon(surf, "rotten", x, y, c.CELL * 0.42, now)
        # Муха кружит над яблоком
        ang = now * 0.008
        fx = x + math.cos(ang) * c.CELL * 0.55
        fy = y - c.CELL * 0.35 + math.sin(ang * 1.7) * c.CELL * 0.2
        pygame.draw.circle(surf, c.FLY_COLOR, (fx, fy), 2)

    def draw_mouse(self, surf, now):
        if not self.mouse:
            return
        left = self.mouse["until"] - now
        if left < 1500 and (now // 160) % 2 == 0:
            return
        # Плавное перемещение между клетками
        t = min(1.0, (now - self.mouse["moved_at"]) / 150)
        px, py = self.mouse["prev"]
        dx, dy = self._wrap_delta(self.mouse["prev"], self.mouse["cell"])
        fx = (px + dx * t) % c.COLS
        fy = (py + dy * t) % c.ROWS
        x = fx * c.CELL + c.CELL / 2
        y = fy * c.CELL + c.CELL / 2 + math.sin(now * 0.02)  # дрожит
        self.draw_bonus_icon(surf, "mouse", x, y, c.CELL * 0.4, now)

    def draw_bonus(self, surf, now):
        if not self.bonus:
            return
        left = self.bonus["until"] - now
        # Последние 1.5 секунды бонус мигает
        if left < 1500 and (now // 160) % 2 == 0:
            return
        x, y = self.cell_center(self.bonus["cell"])
        kind = self.bonus["kind"]
        color = BONUS_KINDS[kind]["color"]
        big_r = c.CELL * 0.42 * (1 + 0.12 * math.sin(now * 0.012))
        self._glow(surf, (x, y), color, int(big_r * 2))
        self.draw_bonus_icon(surf, kind, x, y, big_r, now)
        # Кольцо-таймер: показывает, сколько бонусу осталось жить
        frac = max(0.0, left / c.BONUS_TIME_MS)
        ring = pygame.Rect(0, 0, c.CELL * 1.5, c.CELL * 1.5)
        ring.center = (x, y)
        pygame.draw.arc(
            surf, c.BONUS_RING, ring,
            math.pi / 2, math.pi / 2 + 2 * math.pi * frac, 3,
        )

    # --- Экраны-оверлеи ---
    @staticmethod
    def _dim(surf, alpha=205):
        overlay = pygame.Surface((c.WIDTH, c.HEIGHT), pygame.SRCALPHA)
        overlay.fill((24, 24, 37, alpha))
        surf.blit(overlay, (0, 0))

    def draw_death_flash(self, surf, now):
        elapsed = now - self.death_at
        if elapsed < 400:
            flash = pygame.Surface((c.WIDTH, c.HEIGHT), pygame.SRCALPHA)
            alpha = int(110 * (1 - elapsed / 400))
            flash.fill((*c.DANGER_COLOR, alpha))
            surf.blit(flash, (0, 0))

    def _keycap(self, surf, text, x, y, w):
        """Клавиша в виде «кнопки» клавиатуры."""
        rect = pygame.Rect(x, y, w, 24)
        pygame.draw.rect(surf, c.BTN_COLOR, rect, border_radius=6)
        pygame.draw.rect(surf, c.BAR_BORDER, rect, 1, border_radius=6)
        label = self.small_font.render(text, True, c.TEXT_COLOR)
        surf.blit(label, (rect.centerx - label.get_width() // 2,
                          rect.centery - label.get_height() // 2))

    def _draw_demo_snake(self, surf, cx, y, now):
        """Волнистая змейка-заставка под заголовком."""
        pts = []
        for k in range(36):
            px = cx + 174 - k * 10
            py = y + math.sin(now * 0.003 + k * 0.5) * 9
            pts.append((px, py))
        self._draw_body(surf, pts, 8, now, wrap=False, shadow=True)

    def _panel(self, surf, rect, heading):
        pygame.draw.rect(surf, c.BAR_COLOR, rect, border_radius=14)
        pygame.draw.rect(surf, c.BAR_BORDER, rect, 2, border_radius=14)
        h = self.font.render(heading, True, c.TEXT_COLOR)
        surf.blit(h, (rect.centerx - h.get_width() // 2, rect.top + 12))

    def draw_start(self, surf, now):
        self._dim(surf)
        cx = c.WIDTH // 2

        # Заголовок с тенью
        title = self.title_font.render("Змейка", True, c.ACCENT_COLOR)
        shadow = self.title_font.render("Змейка", True, (18, 18, 28))
        tx = cx - title.get_width() // 2
        surf.blit(shadow, (tx + 3, 19))
        surf.blit(title, (tx, 16))

        self._draw_demo_snake(surf, cx, 102, now)

        pw, ph, gap = 372, 240, 16
        left = pygame.Rect(cx - pw - gap // 2, 132, pw, ph)
        right = pygame.Rect(cx + gap // 2, 132, pw, ph)

        # Левая панель: управление
        self._panel(surf, left, "Управление")
        rows = [
            (["W", "A", "S", "D"], "движение (или стрелки)"),
            (["Пробел"], "пауза"),
            (["R"], "рестарт после проигрыша"),
            (["M"], "выход в меню"),
            (["Esc"], "выход"),
        ]
        row_y = left.top + 48
        anchor = left.x + 150
        for keys, action in rows:
            widths = [
                max(26, self.small_font.size(k)[0] + 12) for k in keys
            ]
            kx = anchor - (sum(widths) + 6 * (len(keys) - 1))
            for key, w in zip(keys, widths):
                self._keycap(surf, key, kx, row_y, w)
                kx += w + 6
            a = self.small_font.render(action, True, c.MUTED_COLOR)
            surf.blit(a, (anchor + 12, row_y + 4))
            row_y += 34

        # Правая панель: легенда добычи и бонусов
        self._panel(surf, right, "Добыча и бонусы")
        legend = [
            ("apple", "яблоко — +1, серия подряд даёт комбо", c.TEXT_COLOR),
            ("mouse", f"мышка — +{c.MOUSE_POINTS}, убегает!", c.TEXT_COLOR),
            ("rotten", f"гнилое — −{c.ROTTEN_PENALTY} и −хвост, объезжай",
             c.ROTTEN_COLOR),
            ("star", f"звезда — +{c.STAR_POINTS} и рост", c.TEXT_COLOR),
            ("turtle", "черепаха — замедление", c.TEXT_COLOR),
            ("scissors", "ножницы — минус половина хвоста", c.TEXT_COLOR),
            ("ghost", "призрак — проход сквозь себя", c.TEXT_COLOR),
        ]
        row_y = right.top + 48
        for kind, text, color in legend:
            self.draw_bonus_icon(surf, kind, right.x + 30, row_y + 9, 9, now)
            label = self.small_font.render(text, True, color)
            surf.blit(label, (right.x + 52, row_y + 1))
            row_y += 27

    def draw_overlay(self, surf, title, subtitle):
        self._dim(surf)
        cy = c.HEIGHT // 2
        t = self.big_font.render(title, True, c.TEXT_COLOR)
        s = self.font.render(subtitle, True, c.MUTED_COLOR)
        surf.blit(t, (c.WIDTH // 2 - t.get_width() // 2, cy - 30))
        surf.blit(s, (c.WIDTH // 2 - s.get_width() // 2, cy + 12))

    def draw_gameover(self, surf):
        self._dim(surf, alpha=236)
        top = 40

        title = self.big_font.render(
            f"Игра окончена! Счёт: {self.score}", True, c.TEXT_COLOR
        )
        surf.blit(title, (c.WIDTH // 2 - title.get_width() // 2, top))

        hint = self.small_font.render(
            "R — рестарт   ·   M — меню", True, c.MUTED_COLOR
        )
        surf.blit(hint, (c.WIDTH // 2 - hint.get_width() // 2, top + 40))

        # Таблица рекордов
        heading = self.font.render("Таблица рекордов", True, c.ACCENT_COLOR)
        hy = top + 80
        hx0 = c.WIDTH // 2 - (heading.get_width() + 24) // 2
        self.draw_bonus_icon(
            surf, "star", hx0 + 9, hy + heading.get_height() // 2, 9, 0
        )
        surf.blit(heading, (hx0 + 24, hy))

        col_x = c.WIDTH // 2 - 190
        row_y = hy + 36
        head_dt = self.small_font.render("Дата / время", True, c.MUTED_COLOR)
        head_df = self.small_font.render("Режим", True, c.MUTED_COLOR)
        head_sc = self.small_font.render("Счёт", True, c.MUTED_COLOR)
        surf.blit(head_dt, (col_x, row_y))
        surf.blit(head_df, (col_x + 230, row_y))
        surf.blit(head_sc, (col_x + 340, row_y))
        row_y += 26

        for i, entry in enumerate(self.scores[:8], start=1):
            color = c.ACCENT_COLOR if i == 1 else c.TEXT_COLOR
            dt = self.small_font.render(
                f"{i}.  {entry['datetime']}", True, color
            )
            df = self.small_font.render(
                entry.get("difficulty") or "—", True, color
            )
            sc = self.small_font.render(str(entry["score"]), True, color)
            surf.blit(dt, (col_x, row_y))
            surf.blit(df, (col_x + 230, row_y))
            surf.blit(sc, (col_x + 340, row_y))
            row_y += 24

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            dt = self.clock.tick(c.FPS) / 1000
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(now, dt)
            self.draw(now)
