"""Общая настройка тестов.

Часть модулей игры импортирует pygame (tank/enemy/boss/level/game). Чтобы
тесты шли headless (без окна и звука), выставляем «пустые» драйверы SDL и
инициализируем pygame один раз за сессию. Модули, где pygame нужен, берут
фикстуру `pg` (или сами делают `pytest.importorskip("pygame")`), поэтому при
отсутствии pygame такие тесты аккуратно пропускаются, а чистые (валидатор
карт) всё равно выполняются.
"""

import os
import sys
from pathlib import Path

import pytest

# Headless-режим SDL до любого импорта pygame
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Каталог battle_city в путь, чтобы работало `from src...`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def pg():
    """Инициализированный pygame или skip, если он не установлен."""
    pygame = pytest.importorskip("pygame")
    pygame.init()
    yield pygame
    pygame.quit()
