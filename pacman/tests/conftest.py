"""Общая настройка тестов (headless).

Логика лабиринта и движения не требует pygame (импорт pygame — только в
`draw`), поэтому тесты идут без окна и без установленного pygame.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
