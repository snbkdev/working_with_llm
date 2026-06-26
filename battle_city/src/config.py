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
ENEMY_COUNT_MIN = 10           # минимум врагов за уровень (рандом)
ENEMY_COUNT_MAX = 15           # максимум врагов за уровень (рандом)
MAX_ACTIVE_ENEMIES = 4         # одновременно на поле
ENEMY_START_DELAY = 6000       # пауза перед первым врагом (мс), ~6 сек
ENEMY_SPAWN_INTERVAL = 2500    # мс между появлениями
ENEMY_SHOOT_CHANCE = 0.012     # вероятность выстрела за кадр
ENEMY_TURN_CHANCE = 0.02       # вероятность смены направления за кадр
ENEMY_SCORE = 100              # очков за уничтоженного врага
BONUS_ENEMY_CHANCE = 0.25      # доля врагов-носителей бонуса (мигают)

# --- Бонусы (power-ups) ---
POWERUP_KINDS = ("star", "helmet", "grenade", "shovel")
POWERUP_LIFETIME = 12000       # сколько висит на поле, если не подобрали (мс)
POWERUP_BLINK_MS = 350         # период мигания иконки на поле
POWERUP_SCORE = 200            # очков за подбор
PLAYER_MAX_LEVEL = 3           # уровней апгрейда танка от звезды (0..3)
HELMET_DURATION = 8000         # неуязвимость от каски (мс)
SHOVEL_DURATION = 12000        # укреплённая база от лопаты (мс)

# --- Звук ---
SOUND_ENABLED = True

# --- Направления (dx, dy) ---
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# --- Цвета (R, G, B) ---
BG_COLOR = (20, 20, 20)
FIELD_COLOR = (8, 8, 8)
GRID_LINE = (26, 26, 26)        # еле заметная сетка полос
FIELD_BORDER = (70, 70, 70)
HUD_BG = (99, 99, 99)
HUD_TEXT = (28, 28, 28)
WHITE = (236, 236, 236)

BRICK_COLOR = (178, 92, 42)
BRICK_DARK = (92, 44, 22)       # «раствор» между кирпичами
STEEL_COLOR = (190, 195, 205)
STEEL_DARK = (95, 100, 110)

TANK_OUTLINE = (18, 18, 18)
PLAYER_COLOR = (180, 214, 92)   # игрок — зелёный
PLAYER_TRACK = (120, 150, 60)
ENEMY_COLOR = (208, 212, 216)   # враг — серебристый
ENEMY_TRACK = (130, 134, 138)
ENEMY_CORE = (200, 70, 60)      # красный «глаз» врага

BULLET_COLOR = (245, 240, 220)

# Взрыв: от яркой вспышки к огню и дыму
EXPLOSION_FLASH = (255, 248, 220)
EXPLOSION_CORE = (255, 220, 90)
EXPLOSION_MID = (245, 150, 50)
EXPLOSION_OUTER = (210, 70, 40)
EXPLOSION_SMOKE = (110, 92, 80)

BASE_COLOR = (224, 196, 64)
BASE_DARK = (90, 78, 28)
BASE_GROUND = (60, 60, 60)

# Бонусы: рамка-подложка и иконки
POWERUP_BG = (38, 40, 48)
POWERUP_FRAME = (236, 236, 236)
STAR_COLOR = (245, 210, 70)
HELMET_COLOR = (150, 205, 235)
GRENADE_COLOR = (96, 100, 104)
SHOVEL_COLOR = (205, 150, 72)
SHIELD_COLOR = (120, 210, 240)

TEXT_COLOR = (236, 236, 236)
ACCENT = (220, 80, 60)
