"""Схемы карт: узор несокрушимых стен + плотность ящиков.

Каждая «схема» — это предикат `wall(col, row)` для ВНУТРЕННИХ клеток (рамку и
безопасные углы арена расставляет сама) и доля ящиков `density`. Из восьми
базовых узоров и нарастающей плотности собираем список из 20 уровней, по
которым игра идёт по кругу.

Узоры подобраны так, чтобы поле всегда оставалось связным: либо стены — это
подмножество классических столбов (чёт/чёт), удаление которых связность лишь
улучшает, либо у «полос» открыты кромочные ряды/столбцы, соединяющие коридоры.
Связность всех схем проверяется тестом (`tests/test_schemes.py`). Модуль без
pygame — чистая геометрия, тестируется headless.
"""

from collections import namedtuple

from .. import config as c

Scheme = namedtuple("Scheme", "name wall density")

# Середина поля — для «ромба» и центральных узоров
_CX, _CY = c.COLS // 2, c.ROWS // 2


# --- Базовые узоры стен (col, row — внутренняя клетка 1..COLS-2 / 1..ROWS-2) ---
def _classic(col, row):
    """Классические столбы в каждой чёт/чёт клетке."""
    return col % 2 == 0 and row % 2 == 0


def _open(col, row):
    """Пусто: только рамка по краю, простор внутри."""
    return False


def _checker(col, row):
    """Половина столбов в шахматном порядке — реже классики."""
    return col % 2 == 0 and row % 2 == 0 and (col // 2 + row // 2) % 2 == 0


def _sparse(col, row):
    """Редкие вертикальные ряды столбов (каждый четвёртый столбец)."""
    return col % 4 == 0 and row % 2 == 0


def _ring(col, row):
    """Столбы только по внутреннему кольцу — центр открыт."""
    return (col % 2 == 0 and row % 2 == 0
            and (col in (2, c.COLS - 3) or row in (2, c.ROWS - 3)))


def _diamond(col, row):
    """Столбы складываются в ромб к центру арены."""
    return (col % 2 == 0 and row % 2 == 0
            and abs(col - _CX) + abs(row - _CY) * 2 <= 6)


def _vbars(col, row):
    """Сплошные вертикальные колонны с проходами по верхней и нижней кромке."""
    return col % 2 == 0 and 2 <= row <= c.ROWS - 3


def _hbars(col, row):
    """Сплошные горизонтальные балки с проходами по левой и правой кромке."""
    return row % 2 == 0 and 2 <= col <= c.COLS - 3


# Классический узор нужен арене как значение по умолчанию
CLASSIC = Scheme("Классика", _classic, c.BLOCK_DENSITY)

# Порядок чередования узоров по уровням (для разнообразия подряд)
_CYCLE = [
    ("Классика", _classic), ("Открытая", _open), ("Шахматы", _checker),
    ("Колонны", _vbars), ("Разрежённая", _sparse), ("Балки", _hbars),
    ("Кольцо", _ring), ("Ромб", _diamond),
]

LEVELS = 20
_D_MIN, _D_MAX = 0.42, 0.78            # плотность ящиков растёт от уровня к уровню


def _build_schemes():
    schemes = []
    for i in range(LEVELS):
        base_name, wall = _CYCLE[i % len(_CYCLE)]
        density = round(_D_MIN + (_D_MAX - _D_MIN) * i / (LEVELS - 1), 3)
        schemes.append(Scheme(f"Ур. {i + 1}: {base_name}", wall, density))
    return schemes


SCHEMES = _build_schemes()


def scheme_for(level):
    """Схема для 1-based номера уровня (по кругу за пределами списка)."""
    return SCHEMES[(level - 1) % LEVELS]
