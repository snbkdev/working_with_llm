"""Сохранение настроек и рекорда в JSON рядом с игрой.

Хранится немного: рекорд (`high`), тумблер звука (`sound`), громкость
(`volume`). Ошибки чтения/записи проглатываются — игра не должна падать из-за
недоступного или битого файла сохранения.
"""

import json
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "save.json"

_DEFAULTS = {"high": 0, "sound": True, "volume": 0.7, "enemies": 4,
             "difficulty": 1, "ms_mode": False, "maze_choice": 0}


def load():
    """Прочитать сохранение; вернуть словарь с дефолтами для отсутствующих ключей."""
    data = dict(_DEFAULTS)
    try:
        with open(_PATH, encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            data.update({k: saved[k] for k in _DEFAULTS if k in saved})
    except Exception:
        pass
    return data


def save(data):
    """Записать словарь настроек (только известные ключи)."""
    try:
        out = {k: data[k] for k in _DEFAULTS if k in data}
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f)
    except Exception:
        pass
