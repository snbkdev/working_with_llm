"""Настройки Bomberman: размеры сетки, тайлы, тайминги, цвета.

Модуль намеренно без pygame — чистые константы, чтобы логику (генерацию
арены, взрыв, ИИ) можно было тестировать headless.
"""

# --- Сетка и окно ---
COLS = 15                       # ширина арены в клетках (как в Atomic Bomberman)
ROWS = 11                       # высота арены в клетках
TILE = 40                       # размер клетки в пикселях

FIELD_W = COLS * TILE           # 600
FIELD_H = ROWS * TILE           # 440
HUD_W = 160                     # правая панель (очки/статы)
WIDTH = FIELD_W + HUD_W         # 760
HEIGHT = FIELD_H                # 440
FPS = 60

# --- Типы клеток ---
FLOOR = 0                       # пол — проходим
WALL = 1                        # несокрушимый столб/рамка
BLOCK = 2                       # разрушаемый ящик (прячет бонус)

# --- Направления (dx, dy) ---
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# --- Бомба ---
FUSE_MS = 2500                  # фитиль ~2.5 сек до взрыва
BOMB_COLOR = (36, 38, 46)
BOMB_DARK = (14, 14, 18)
BOMB_LIGHT = (120, 128, 150)
BOMB_FUSE = (200, 170, 90)
BOMB_SPARK = (250, 220, 90)
BOMB_SPARK2 = (250, 140, 40)

# --- Взрыв (крестообразное пламя) ---
FLAME_MS = 450                  # сколько держится пламя на экране
FLAME_CORE = (255, 248, 220)    # белёсое ядро
FLAME_HOT = (255, 210, 90)      # оранжево-жёлтое
FLAME_EDGE = (240, 120, 40)     # красно-оранжевые края

# --- Раунд ---
RESPAWN_MS = 1000               # пауза после гибели до рестарта раунда
DEAD_COLOR = (150, 150, 158)    # обесцвеченный спрайт погибшего

# --- Бонусы и проклятия (power-ups) ---
POW_BOMB = 0                    # +1 к запасу бомб
POW_FIRE = 1                    # +1 к длине пламени
POW_SPEED = 2                   # +1 к скорости
POW_KICK = 3                    # пинать бомбы
POW_FULLFIRE = 4               # максимальный огонь
POW_DETON = 5                   # детонатор (ручной подрыв клавишей E)
POW_SKULL = 6                   # проклятие-череп (случайная болезнь)

POWERUP_KINDS = (POW_BOMB, POW_FIRE, POW_SPEED, POW_KICK,
                 POW_FULLFIRE, POW_DETON, POW_SKULL)
# Веса выпадения (сумма произвольна). Черепов и «полного огня» — поменьше.
POWERUP_WEIGHTS = {
    POW_BOMB: 26, POW_FIRE: 26, POW_SPEED: 16, POW_KICK: 10,
    POW_FULLFIRE: 5, POW_DETON: 8, POW_SKULL: 9,
}
POWERUP_DROP = 0.45            # доля разрушаемых блоков, прячущих бонус

MAX_BOMBS = 8                  # потолок запаса бомб
MAX_FIRE = 6                  # потолок длины пламени (умеренно, чтобы не «на пол-арены»)
MAX_SPEED_LVL = 3             # +к базовой скорости от бонусов «Скорость»
KICK_SPEED = 4                # пикселей/кадр — скольжение пиннутой бомбы

# Цвета плиток-бонусов (рисуем процедурно)
POW_COLORS = {
    POW_BOMB: (232, 96, 88),
    POW_FIRE: (240, 150, 50),
    POW_SPEED: (96, 190, 120),
    POW_KICK: (110, 170, 235),
    POW_FULLFIRE: (240, 90, 60),
    POW_DETON: (200, 130, 235),
    POW_SKULL: (170, 176, 190),
}

# --- Проклятия-черепа ---
CURSE_REVERSE = 0             # реверс управления
CURSE_SLOW = 1               # слишком медленно
CURSE_FAST = 2               # слишком быстро (труднее управлять)
CURSE_MINI = 3               # мини-радиус пламени (огонь = 1)
CURSE_AUTOBOMB = 4           # авто-сброс бомб
CURSE_NOBOMB = 5             # нельзя ставить бомбы
CURSES = (CURSE_REVERSE, CURSE_SLOW, CURSE_FAST,
          CURSE_MINI, CURSE_AUTOBOMB, CURSE_NOBOMB)
CURSE_MS = 8000              # длительность болезни
CURSE_NAMES = {
    CURSE_REVERSE: "реверс", CURSE_SLOW: "медленно", CURSE_FAST: "быстро",
    CURSE_MINI: "мини-огонь", CURSE_AUTOBOMB: "авто-бомбы", CURSE_NOBOMB: "без бомб",
}
CURSE_SPEED_SLOW = 1         # скорость при болезни «медленно»
CURSE_SPEED_FAST = 5         # скорость при болезни «быстро»
AUTOBOMB_MS = 700            # период авто-сброса при болезни

# --- ИИ-боты ---
DIFF_EASY = 0
DIFF_MEDIUM = 1
DIFF_HARD = 2
DIFF_NAMES = {DIFF_EASY: "Лёгкий", DIFF_MEDIUM: "Средний", DIFF_HARD: "Сложный"}
# Параметры на уровень: период «раздумий» (мс), шанс реально поставить бомбу,
# охотится ли за врагом, дальность просчёта пути.
DIFF_PARAMS = {
    DIFF_EASY:   {"think_ms": 360, "bomb_chance": 0.5, "hunt": False, "reach": 8},
    DIFF_MEDIUM: {"think_ms": 200, "bomb_chance": 0.85, "hunt": True, "reach": 14},
    DIFF_HARD:   {"think_ms": 110, "bomb_chance": 1.0, "hunt": True, "reach": 20},
}
DEFAULT_BOTS = 3             # ботов в превью по умолчанию
DEFAULT_DIFFICULTY = DIFF_MEDIUM

# --- Игрок ---
PLAYER_SIZE = 30                # габарит < TILE, чтобы проходить в проёмы
PLAYER_SPEED = 2                # пикселей/кадр (база; ускоряется бонусом)
PLAYER_OUTLINE = (22, 22, 28)
# Цвета 4 игроков (1-й — классический белый бомбермен)
PLAYER_COLORS = (
    (238, 240, 248),            # белый
    (228, 88, 80),             # красный
    (92, 148, 232),            # синий
    (108, 196, 108),           # зелёный
)

# --- Генерация арены ---
BLOCK_DENSITY = 0.62            # доля свободных клеток, занятых ящиками
# Стартовые углы игроков (клетки). Порядок: ЛВ, ПВ, ЛН, ПН.
SPAWN_CELLS = (
    (1, 1),
    (COLS - 2, 1),
    (1, ROWS - 2),
    (COLS - 2, ROWS - 2),
)

# --- Цвета ---
BG_COLOR = (16, 20, 16)

# Пол — травяная «шахматка» из двух зелёных
FLOOR_A = (58, 128, 52)
FLOOR_B = (50, 116, 46)
FLOOR_EDGE = (40, 96, 38)

# Несокрушимая стена — каменно-синий блок с фаской
WALL_COLOR = (96, 108, 130)
WALL_LIGHT = (142, 154, 176)
WALL_DARK = (54, 62, 82)

# Разрушаемый ящик — деревянный, с фаской и доской
BLOCK_COLOR = (176, 124, 74)
BLOCK_LIGHT = (210, 158, 102)
BLOCK_DARK = (118, 78, 42)

HUD_BG = (28, 30, 36)
HUD_TEXT = (220, 220, 220)
WHITE = (236, 236, 236)
ACCENT = (230, 180, 60)
