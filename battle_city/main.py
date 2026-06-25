"""Battle City на pygame — точка входа.

Запуск:
    python battle_city/main.py

Структура (см. PLAN.md):
    src/config.py        — настройки и цвета
    src/game.py          — игровой цикл
    src/world/level.py   — карта поля, стены, база
    src/entities/        — bullet.py, tank.py, enemy.py
    main.py              — точка входа (этот файл)
"""

from src.game import Game


def main():
    Game().run()


if __name__ == "__main__":
    main()
