"""Настройки игры Battle City и цветовая палитра."""

# --- Поле ---
TILE = 40                      # размер одной клетки (кирпич/сталь) в пикселях
COLS = 13                      # ширина поля в клетках
ROWS = 13                      # высота поля в клетках
FIELD_W = COLS * TILE          # 520
FIELD_H = ROWS * TILE          # 520
HUD_W = 150                    # ширина боковой панели справа
WIDTH = FIELD_W + HUD_W
HEIGHT = FIELD_H
FPS = 60

# --- Танки ---
TANK_SIZE = 32                 # габарит танка (меньше клетки — проходит в проёмы)
TANK_OFFSET = (TILE - TANK_SIZE) // 2   # центрирование танка в полосе
PLAYER_SPEED = 2               # пикселей за кадр
ENEMY_SPEED = 2
PLAYER_LIVES = 3
PLAYER_INVULN_MS = 2000        # неуязвимость после респауна

# --- Пули ---
BULLET_SPEED = 6
BULLET_SIZE = 8
PLAYER_SHOOT_COOLDOWN = 350    # мс между выстрелами игрока
PLAYER_MAX_BULLETS = 1         # сколько пуль игрока одновременно на поле

# --- Враги ---
TOTAL_ENEMIES = 10             # всего врагов за уровень
MAX_ACTIVE_ENEMIES = 4         # одновременно на поле
ENEMY_SPAWN_INTERVAL = 2500    # мс между появлениями
ENEMY_SHOOT_CHANCE = 0.012     # вероятность выстрела за кадр
ENEMY_TURN_CHANCE = 0.02       # вероятность смены направления за кадр

# --- Направления (dx, dy) ---
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# --- Цвета (R, G, B) ---
BG_COLOR = (20, 20, 20)
FIELD_COLOR = (0, 0, 0)
HUD_BG = (99, 99, 99)
HUD_TEXT = (33, 33, 33)
WHITE = (236, 236, 236)
BRICK_COLOR = (150, 75, 35)
BRICK_DARK = (110, 50, 20)
STEEL_COLOR = (160, 160, 160)
STEEL_DARK = (90, 90, 90)
PLAYER_COLOR = (220, 190, 60)
PLAYER_TRACK = (180, 150, 40)
ENEMY_COLOR = (210, 210, 210)
ENEMY_TRACK = (150, 150, 150)
BULLET_COLOR = (240, 240, 240)
BASE_COLOR = (210, 180, 40)
BASE_DARK = (120, 100, 20)
TEXT_COLOR = (236, 236, 236)
ACCENT = (220, 80, 60)
