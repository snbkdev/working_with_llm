"""Бот: уклонение от пламени, решение о бомбе, движение к цели."""

from src import config as c
from src.entities.bomb import Bomb
from src.entities.bot import Bot
from src.world.arena import Arena


def open_arena():
    return Arena(seed=1, density=0.0)


class _Enemy:
    def __init__(self, cell):
        self.cell_ = cell
        self.alive = True

    @property
    def cell(self):
        return self.cell_


def test_bot_flees_when_in_danger():
    a = open_arena()
    bot = Bot(1, 1, index=1, difficulty=c.DIFF_MEDIUM, seed=0)
    bomb = Bomb(1, 1, owner=0, fire=2, now=0)          # прямо под ботом
    d, want = bot.action(a, [], [bomb], [], now=0)
    assert d is not None                                # шагает прочь
    assert want is False                                # в опасности не бомбит


def test_bot_bombs_adjacent_block_with_escape():
    a = open_arena()
    a.grid[1][3] = c.BLOCK                              # ящик рядом с (2,1)? нет — сделаем у (1,1)
    a.grid[1][2] = c.FLOOR
    a.grid[2][1] = c.BLOCK                              # ящик-сосед (2,1)... (2,1) пол? заменим
    # надёжнее: ящик прямо справа от бота на (2,1) невозможен (это пол); берём (1,2)
    a.grid[2][1] = c.FLOOR
    a.grid[1][2] = c.BLOCK                              # ящик снизу от (1,1)
    bot = Bot(1, 1, index=1, difficulty=c.DIFF_HARD, seed=0)
    d, want = bot.action(a, [], [], [], now=0)
    assert want is True                                 # рядом ящик и есть куда убежать


def test_bot_no_bomb_when_boxed():
    a = open_arena()
    a.grid[1][2] = c.BLOCK                              # (1,2) блок
    a.grid[2][1] = c.BLOCK                              # (2,1) блок → угол замурован
    bot = Bot(1, 1, index=1, difficulty=c.DIFF_HARD, seed=0)
    d, want = bot.action(a, [], [], [], now=0)
    assert want is False                                # убежать некуда — не бомбим


def test_bot_moves_toward_powerup():
    a = open_arena()
    bot = Bot(1, 1, index=1, difficulty=c.DIFF_MEDIUM, seed=3)
    bot.goal_powerups = {(1, 5)}
    d, want = bot.action(a, [], [], [], now=0)
    assert d == c.DOWN                                  # идёт к бонусу по коридору
    assert want is False


def test_bot_hunts_enemy_in_line():
    a = open_arena()
    bot = Bot(1, 1, index=1, difficulty=c.DIFF_HARD, seed=0)
    enemy = _Enemy((1, 3))                              # на луче вниз, в пределах огня
    bot.fire = 3
    d, want = bot.action(a, [enemy], [], [], now=0)
    assert want is True                                 # враг в зоне — закладывает бомбу


def test_dead_bot_is_idle():
    a = open_arena()
    bot = Bot(1, 1, index=1, seed=0)
    bot.kill(now=0)
    assert bot.action(a, [], [], [], now=10) == (None, False)
