"""Сохранение рекорда (лучшего счёта) между запусками.

Рекорд лежит в `battle_city/highscore.json`. Любая ошибка чтения/записи
тихо игнорируется (рекорд просто считается равным 0) — игра не должна
падать из-за повреждённого или недоступного файла.
"""

import json
from pathlib import Path

SAVE_PATH = Path(__file__).resolve().parent.parent / "highscore.json"


def load_highscore():
    """Возвращает сохранённый рекорд (int). При любой проблеме — 0."""
    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        return max(0, int(data.get("highscore", 0)))
    except (OSError, ValueError, TypeError):
        return 0


def save_highscore(value):
    """Записывает рекорд. Возвращает True при успехе, False при ошибке."""
    try:
        SAVE_PATH.write_text(
            json.dumps({"highscore": int(value)}), encoding="utf-8")
        return True
    except (OSError, ValueError, TypeError):
        return False
