"""Настройки игры и цветовая палитра."""

from pathlib import Path

# --- Размеры поля ---
CELL = 25            # размер одной клетки в пикселях
COLS = 24            # количество клеток по горизонтали
ROWS = 20            # количество клеток по вертикали
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL
TOPBAR = 52          # высота верхней панели (меню)
FPS = 12             # скорость игры (кадров/шагов в секунду)

# --- Рекорды ---
SCORES_FILE = Path(__file__).with_name("scores.json")
MAX_SCORES = 20      # сколько рекордов хранить в файле

# --- Цвета (R, G, B) ---
BG_COLOR = (30, 30, 46)
BAR_COLOR = (24, 24, 37)
BAR_BORDER = (49, 50, 68)
GRID_COLOR = (39, 41, 61)
SNAKE_COLOR = (166, 227, 161)
HEAD_COLOR = (148, 226, 213)
FOOD_COLOR = (243, 139, 168)
TEXT_COLOR = (205, 214, 244)
MUTED_COLOR = (127, 132, 156)
ACCENT_COLOR = (166, 227, 161)
BTN_COLOR = (49, 50, 68)
BTN_HOVER = (69, 71, 90)
BTN_EXIT = (243, 139, 168)
