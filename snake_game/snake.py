"""Игра «Змейка» на pygame — точка входа.

Запуск:
    python snake_game/snake.py

Структура проекта:
    config.py  — настройки и цвета
    scores.py  — таблица рекордов (сохранение в scores.json)
    button.py  — UI-кнопка
    game.py    — логика и отрисовка игры
    snake.py   — точка входа (этот файл)

Управление:
    - Стрелки или WASD — движение
    - Пробел или кнопка «Пауза» — пауза
    - R — рестарт после проигрыша
    - Esc / кнопка «Выход» / закрытие окна — выход
"""

from game import SnakeGame


def main():
    SnakeGame().run()


if __name__ == "__main__":
    main()
