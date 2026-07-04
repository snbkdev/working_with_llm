"""Сохранение рекорда (лучшего счёта) между запусками.

Рекорд лежит в `battle_city/highscore.json`. Любая ошибка чтения/записи
тихо игнорируется (рекорд просто считается равным 0) — игра не должна
падать из-за повреждённого или недоступного файла.
"""

import json
from datetime import datetime
from pathlib import Path

SAVE_PATH = Path(__file__).resolve().parent.parent / "highscore.json"
GAME_SAVE_PATH = Path(__file__).resolve().parent.parent / "savegame.json"
SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.json"
SCORES_PATH = Path(__file__).resolve().parent.parent / "scores.json"
MAX_SCORES = 10


def _legacy_highscore():
    """Старый формат: одиночный рекорд в highscore.json (для миграции)."""
    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        return max(0, int(data.get("highscore", 0)))
    except (OSError, ValueError, TypeError):
        return 0


def load_highscore():
    """Лучший счёт (для HUD): максимум из таблицы рекордов."""
    scores = load_scores()
    return scores[0]["score"] if scores else 0


def save_highscore(value):
    """Записывает рекорд. Возвращает True при успехе, False при ошибке."""
    try:
        SAVE_PATH.write_text(
            json.dumps({"highscore": int(value)}), encoding="utf-8")
        return True
    except (OSError, ValueError, TypeError):
        return False


# --- Сохранение партии ---
def has_save():
    """Есть ли сохранённая партия."""
    return GAME_SAVE_PATH.exists()


def save_game(data):
    """Сохраняет снапшот партии (dict) в JSON. True при успехе."""
    try:
        GAME_SAVE_PATH.write_text(json.dumps(data), encoding="utf-8")
        return True
    except (OSError, ValueError, TypeError):
        return False


def load_game():
    """Возвращает снапшот партии (dict) или None, если его нет/повреждён."""
    try:
        return json.loads(GAME_SAVE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


# --- Настройки (звук/громкость/сложность) ---
def load_settings():
    """Возвращает настройки (dict) или None, если файла нет/повреждён."""
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def save_settings(data):
    """Сохраняет настройки (dict). True при успехе."""
    try:
        SETTINGS_PATH.write_text(json.dumps(data), encoding="utf-8")
        return True
    except (OSError, ValueError, TypeError):
        return False


# --- Таблица рекордов (топ-10) ---
def load_scores():
    """Топ-10 рекордов [{name, score, date}], по убыванию очков.

    При отсутствии файла мигрирует старый одиночный рекорд из highscore.json.
    """
    try:
        data = json.loads(SCORES_PATH.read_text(encoding="utf-8"))
        raw = data.get("scores", [])
    except (OSError, ValueError, TypeError):
        old = _legacy_highscore()
        raw = [{"name": "—", "score": old, "date": ""}] if old > 0 else []
    scores = []
    for s in raw:
        try:
            scores.append({
                "name": str(s.get("name", "—"))[:12] or "—",
                "score": max(0, int(s.get("score", 0))),
                "date": str(s.get("date", "")),
            })
        except (ValueError, TypeError, AttributeError):
            continue
    scores.sort(key=lambda s: s["score"], reverse=True)
    return scores[:MAX_SCORES]


def save_scores(scores):
    try:
        SCORES_PATH.write_text(json.dumps({"scores": scores}), encoding="utf-8")
        return True
    except (OSError, ValueError, TypeError):
        return False


def qualifies(score):
    """Попадает ли счёт в таблицу (список неполон или счёт выше последнего)."""
    if score <= 0:
        return False
    scores = load_scores()
    return len(scores) < MAX_SCORES or score > scores[-1]["score"]


def add_score(name, score):
    """Добавляет результат в таблицу, обрезает до топ-10. Возвращает место (0-based) или -1."""
    entry = {
        "name": (str(name).strip() or "—")[:12],
        "score": int(score),
        "date": datetime.now().strftime("%d.%m.%Y"),
    }
    scores = load_scores()
    scores.append(entry)
    scores.sort(key=lambda s: s["score"], reverse=True)
    scores = scores[:MAX_SCORES]
    save_scores(scores)
    return scores.index(entry) if entry in scores else -1
