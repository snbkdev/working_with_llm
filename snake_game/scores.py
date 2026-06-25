"""Хранение таблицы рекордов (дата/время + счёт) в JSON-файле."""

import json
from datetime import datetime

from config import MAX_SCORES, SCORES_FILE


def load_scores():
    """Читает рекорды из файла; возвращает список словарей."""
    try:
        data = json.loads(SCORES_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def save_score(score):
    """Добавляет рекорд с текущей датой/временем и сохраняет топ-N.

    Возвращает обновлённый и отсортированный список рекордов.
    """
    scores = load_scores()
    scores.append({
        "score": score,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    scores.sort(key=lambda s: s["score"], reverse=True)
    scores = scores[:MAX_SCORES]
    SCORES_FILE.write_text(
        json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return scores
