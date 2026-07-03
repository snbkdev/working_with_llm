"""Пользовательские настройки (звук, музыка) — сохраняются между запусками."""

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).with_name("settings.json")


def load_settings():
    """Читает настройки; возвращает словарь (пустой, если файла нет)."""
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def save_settings(**values):
    """Обновляет и сохраняет настройки (сливает с уже сохранёнными)."""
    data = load_settings()
    data.update(values)
    try:
        SETTINGS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass  # не смогли записать — просто не сохранится
