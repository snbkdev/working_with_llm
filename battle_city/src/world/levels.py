"""Хранилище карт уровней и загрузчик.

Карты лежат в каталоге `battle_city/levels/` как `*.txt`, по одному
символу на клетку (см. формат в `level.py`). Файлы загружаются в
алфавитном порядке имён: 01.txt, 02.txt, … — это и есть порядок уровней.
Каждая карта проверяется на корректность при загрузке.
"""

from pathlib import Path

from .. import config as c

LEVELS_DIR = Path(__file__).resolve().parents[2] / "levels"
# . пусто · B кирпич · S сталь · A база · P игрок · E спавн врага
# W вода · F лес · I лёд
VALID_CHARS = set(".BSAPEWFI")

_files_cache = None     # карты не меняются во время игры — глобим один раз


def _level_files():
    global _files_cache
    if _files_cache is None:
        _files_cache = sorted(LEVELS_DIR.glob("*.txt"))
    return _files_cache


def level_count():
    return len(_level_files())


def load_level(index):
    """Возвращает карту уровня (список строк). index с 0.

    Индекс зажимается в границы [0, level_count-1]. Карта валидируется;
    при ошибке формата бросается ValueError, чтобы баг было видно сразу.
    """
    files = _level_files()
    if not files:
        raise FileNotFoundError(f"Нет карт уровней в {LEVELS_DIR}")
    index = max(0, min(index, len(files) - 1))
    path = files[index]
    rows = path.read_text(encoding="utf-8").splitlines()
    while rows and not rows[-1].strip():     # отбрасываем хвостовые пустые строки
        rows.pop()
    validate(rows, path.name)
    return rows


def validate(rows, name=""):
    """Проверяет размер 13×13, допустимые символы и наличие базы/игрока/врагов."""
    if len(rows) != c.ROWS:
        raise ValueError(f"{name}: ожидается {c.ROWS} строк, получено {len(rows)}")
    for i, line in enumerate(rows):
        if len(line) != c.COLS:
            raise ValueError(
                f"{name}: строка {i} длиной {len(line)}, нужно {c.COLS}")
        bad = set(line) - VALID_CHARS
        if bad:
            raise ValueError(f"{name}: недопустимые символы {sorted(bad)} в строке {i}")
    text = "".join(rows)
    if text.count("A") != 1:
        raise ValueError(f"{name}: должна быть ровно одна база 'A'")
    if text.count("P") != 1:
        raise ValueError(f"{name}: должна быть ровно одна точка игрока 'P'")
    if text.count("E") < 1:
        raise ValueError(f"{name}: нужна хотя бы одна точка появления врага 'E'")
