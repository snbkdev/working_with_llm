"""Настройки игры и цветовая палитра."""

from pathlib import Path

# --- Размеры поля ---
CELL = 28            # размер одной клетки в пикселях
COLS = 28            # количество клеток по горизонтали
ROWS = 21            # количество клеток по вертикали
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL
TOPBAR = 56          # высота верхней панели (меню)
FPS = 60             # частота отрисовки (движение плавное, шаги — отдельно)

# --- Уровни сложности ---
# step_ms — начальный интервал шага; accel_ms — ускорение за каждую еду;
# min_step_ms — предел ускорения; walls — смертельны ли стены
DIFFICULTIES = {
    "easy": {
        "label": "Лёгкий",
        "desc": "медленный темп  ·  стены проходимы",
        "step_ms": 175, "accel_ms": 2, "min_step_ms": 90, "walls": False,
    },
    "normal": {
        "label": "Средний",
        "desc": "классика  ·  стены проходимы",
        "step_ms": 150, "accel_ms": 3, "min_step_ms": 65, "walls": False,
    },
    "hard": {
        "label": "Сложный",
        "desc": "быстрый темп  ·  стены смертельны!",
        "step_ms": 130, "accel_ms": 4, "min_step_ms": 55, "walls": True,
    },
}
DEFAULT_DIFFICULTY = "normal"

# --- Бонусы ---
BONUS_EVERY = 5        # каждые N съеденных яблок появляется бонус
BONUS_TIME_MS = 6000   # сколько миллисекунд бонус остаётся на поле
STAR_POINTS = 5        # очков за звезду
EFFECT_POINTS = 2      # очков за бонус-эффект (черепаха/ножницы/призрак)
SLOW_MS = 10000        # длительность замедления от черепахи
SLOW_FACTOR = 1.6      # во сколько раз замедляется шаг
GHOST_MS = 6000        # длительность «призрака» (проход сквозь себя)
SCISSORS_MIN_LEN = 10  # ножницы появляются, только если змейка длиннее

# --- Гнилое яблоко ---
ROTTEN_CHANCE = 0.25   # шанс появления после каждого съеденного яблока
ROTTEN_TIME_MS = 8000  # сколько лежит на поле
ROTTEN_PENALTY = 3     # штраф к счёту
ROTTEN_SHRINK = 2      # на сколько клеток укорачивает змейку

# --- Мышка ---
MOUSE_CHANCE = 0.18    # шанс появления после каждого съеденного яблока
MOUSE_TIME_MS = 12000  # сколько бегает по полю
MOUSE_POINTS = 4       # очков за поимку
MOUSE_MOVE_MS = 450    # как часто перебегает на соседнюю клетку

# --- Комбо ---
COMBO_WINDOW_MS = 4000  # успей съесть следующее яблоко, чтобы поднять комбо
COMBO_MAX = 9           # максимальный множитель

# --- Рекорды ---
SCORES_FILE = Path(__file__).with_name("scores.json")
MAX_SCORES = 20      # сколько рекордов хранить в файле

# --- Звук ---
SOUND_ENABLED = True
MUSIC_ENABLED = True   # фоновая чиптюн-музыка (требует SOUND_ENABLED)
MUSIC_VOLUME = 0.35

# --- Цвета (R, G, B) ---
BG_COLOR = (30, 30, 46)
BG_CHECKER = (35, 36, 54)     # клетки «шахматной» подложки
BAR_COLOR = (24, 24, 37)
BAR_BORDER = (49, 50, 68)
WALL_COLOR = (170, 92, 110)   # рамка смертельных стен
SNAKE_HEAD = (148, 226, 213)
SNAKE_BODY = (166, 227, 161)
SNAKE_TAIL = (92, 152, 122)
EYE_WHITE = (245, 245, 255)
EYE_PUPIL = (24, 24, 37)
TONGUE_COLOR = (238, 105, 125)
FOOD_COLOR = (243, 139, 168)
FOOD_SHINE = (255, 205, 220)
STEM_COLOR = (148, 108, 76)
LEAF_COLOR = (166, 227, 161)
BONUS_COLOR = (249, 226, 175)
BONUS_RING = (250, 179, 135)
TURTLE_COLOR = (137, 220, 235)
SCISSORS_COLOR = (186, 194, 222)
GHOST_COLOR = (203, 166, 247)
ROTTEN_COLOR = (154, 170, 92)
ROTTEN_DARK = (104, 116, 58)
MOUSE_COLOR = (165, 173, 203)
MOUSE_EAR = (214, 190, 208)
FLY_COLOR = (45, 45, 60)
TEXT_COLOR = (205, 214, 244)
MUTED_COLOR = (127, 132, 156)
ACCENT_COLOR = (166, 227, 161)
DANGER_COLOR = (243, 139, 168)
BTN_COLOR = (49, 50, 68)
BTN_HOVER = (69, 71, 90)
BTN_EXIT = (243, 139, 168)
