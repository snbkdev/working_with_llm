"""Правила XP/уровней (из docs.md).

+10 XP за квиз, +100 XP за код-челлендж, +1 уровень за каждые 100 XP,
максимум — уровень 50. Уровень и XP считаются здесь, чтобы бэкенд оставался
единственным источником правды: фронтенд лишь показывает то, что вернули
эти функции.
"""
from .config import MAX_LEVEL, MAX_XP, XP_PER_LEVEL, XP_REWARDS
from .models import User


def level_for_xp(xp: int) -> int:
    """Уровень = XP // 100, но не выше MAX_LEVEL."""
    return min(MAX_LEVEL, xp // XP_PER_LEVEL)


def award_xp(user: User, action: str) -> dict:
    """Начислить XP за завершённое действие ('quiz' / 'challenge').

    XP не превышает MAX_XP (уровень 50). Меняет пользователя на месте —
    коммит сессии остаётся на вызывающей стороне. Возвращает сводку изменения.
    """
    reward = XP_REWARDS.get(action)
    if reward is None:
        raise ValueError(f"Unknown XP action: {action!r}")

    before_xp, before_level = user.xp, user.level
    user.xp = min(MAX_XP, user.xp + reward)
    user.level = level_for_xp(user.xp)
    return {
        "action": action,
        "awarded": user.xp - before_xp,   # 0, когда достигнут потолок
        "xp": user.xp,
        "level": user.level,
        "leveled_up": user.level > before_level,
    }
