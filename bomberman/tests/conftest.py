"""Общая настройка тестов (headless).

Логика арены не требует pygame (импорт pygame — только в `Arena.draw`),
поэтому эти тесты идут без окна и без установленного pygame.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
