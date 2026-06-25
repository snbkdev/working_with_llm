"""Battle City на pygame — точка входа.

Запуск:
    python battle_city/main.py

Структура (см. PLAN.md):
    config.py — настройки и цвета
    level.py  — карта поля, стены, база
    bullet.py — пуля
    tank.py   — танк (игрок/враг)
    game.py   — игровой цикл
    main.py   — точка входа (этот файл)
"""

from game import Game


def main():
    Game().run()


if __name__ == "__main__":
    main()
