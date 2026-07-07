"""ИИ-бот: наследует движение/статы игрока, добавляет принятие решений.

Каждый кадр бот получает `action(...)` — направление шага и флаг «ставить
бомбу». Приоритеты: сначала выжить (уйти из-под будущего взрыва), затем — при
удобном случае — заложить бомбу под врага или ящик (только если есть куда
убежать), иначе собрать бонус / разрушить ящик / идти к врагу.

Вся «мыслительная» логика опирается на чистый `src.ai`, поэтому решения бота
проверяемы headless. pygame наследуется от `Player` только для отрисовки.
"""

import random

from .. import config as c
from .. import ai
from .player import Player


class Bot(Player):
    def __init__(self, col, row, index, difficulty=c.DIFF_MEDIUM, seed=None):
        super().__init__(col, row, index)
        self.is_bot = True
        self.difficulty = difficulty
        self.rng = random.Random(seed)
        self._next_think = 0                 # когда пора пересчитать план
        self._plan_dir = None                # цель движения (обновляется по «раздумьям»)
        self._move_dir = None                # зафиксированный курс до клетки-цели
        self._target = None                  # клетка, к центру которой едем
        self._travel = 0                     # кадров в пути (сторож от застревания)
        self._want_bomb = False              # намерение поставить бомбу

    @property
    def params(self):
        return c.DIFF_PARAMS[self.difficulty]

    def _reached(self, cell):
        """Дошёл ли бот до центра клетки cell (в пределах шага)."""
        cx, cy = self.center
        tx = cell[0] * c.TILE + c.TILE // 2
        ty = cell[1] * c.TILE + c.TILE // 2
        return abs(cx - tx) <= self.speed and abs(cy - ty) <= self.speed

    def action(self, arena, enemies, bombs, explosions, now):
        """Возвращает (direction, place_bomb) для этого кадра.

        Схема движения не зависит от скорости: бот едет к соседней клетке-цели
        и решает заново только по прибытии в её центр (там же выравнивается по
        сетке). Так он не «дёргается» на границе клеток и не застревает при
        нестандартной скорости после бонуса.
        """
        if not self.alive:
            return None, False

        # Ещё едем к цели — держим курс (сторож обрывает застревание)
        if self._target is not None and not self._reached(self._target):
            self._travel += 1
            ahead_solid = arena.is_solid(*self._target) or \
                any(b.cell == self._target for b in bombs)
            if self._travel < c.TILE and not ahead_solid:
                return self._move_dir, False
        # Прибыли (или путь перекрыт) — выравниваемся и принимаем решение
        self.snap_to_center()
        self._target = None
        self._travel = 0

        bomb_cells = frozenset(b.cell for b in bombs)
        danger = ai.danger_map(arena, bombs, explosions, now)
        here = self.cell

        # 1) В опасности — бежим к безопасной клетке, бомбу не ставим
        if not ai.is_safe(here, danger):
            return self._commit(ai.flee_step(arena, here, danger, bomb_cells), here)

        # 2) Периодически пересчитываем план (движение + желание бомбить)
        if now >= self._next_think:
            self._next_think = now + self.params["think_ms"]
            self._replan(arena, enemies, bombs, explosions, now, bomb_cells)

        # 3) Решили бомбить — ставим (мы в центре) и на след. кадрах убегаем
        if self._want_bomb:
            self._want_bomb = False
            return None, True

        # Двигаемся по плану, но не шагаем в клетку под будущим взрывом
        d = self._plan_dir
        if d is not None:
            nxt = (here[0] + d[0], here[1] + d[1])
            if not ai.is_safe(nxt, danger):
                d = None
        return self._commit(d, here)

    def _commit(self, direction, here):
        """Фиксирует направление и клетку-цель на путь до следующего центра."""
        self._move_dir = direction
        if direction is not None:
            self._target = (here[0] + direction[0], here[1] + direction[1])
        return direction, False

    def _replan(self, arena, enemies, bombs, explosions, now, bomb_cells):
        self._plan_dir = None
        self._want_bomb = False
        p = self.params
        here = self.cell
        alive_enemies = [e.cell for e in enemies if e.alive]

        # Проверяем, не выгодно ли поставить бомбу прямо сейчас.
        # Держим не больше ОДНОЙ своей активной бомбы — так бот не загоняет
        # себя в собственные пламёна (даже если запас бомб больше).
        own_active = sum(1 for b in bombs
                         if b.owner == self.index and not b.exploded)
        if own_active == 0:
            targets = set()
            if p["hunt"]:
                targets |= set(alive_enemies)
            adj_block = any(arena.is_block(*nb) for nb in ai.neighbors(here))
            hit_enemy = ai.hits_from(arena, here, self.flame, targets)
            if (hit_enemy or adj_block) and self.rng.random() < p["bomb_chance"]:
                hypo = bombs + [_Ghost(here, self.index, self.flame, now)]
                if ai.escape_exists(arena, here, hypo, explosions, now,
                                    max_dist=p["reach"]):
                    self._want_bomb = True
                    return

        # Иначе выбираем цель движения: бонус → ящик → враг → блуждание
        goal_cells = self._goal_cells(arena, enemies, bombs, explosions, now)
        for goals in goal_cells:
            step = ai.nearest(arena, here, goals, bomb_cells)[1]
            if step is not None:
                self._plan_dir = step
                return
        # Ничего — случайный безопасный сосед
        self._plan_dir = self._random_step(arena, here, bomb_cells,
                                           ai.danger_map(arena, bombs, explosions, now))

    def _goal_cells(self, arena, enemies, bombs, explosions, now):
        """Наборы клеток-целей в порядке приоритета (бонусы, ящики, враги)."""
        p = self.params
        # 1) Бонусы (координаты берём от вызова — их знает игровой цикл через .goals_powerups)
        pu = getattr(self, "goal_powerups", set())
        goals = []
        if pu:
            goals.append(pu)
        # 2) Клетки у разрушаемых ящиков
        goals.append(ai.block_targets(arena, self.cell))
        # 3) Клетки рядом с врагами (охота)
        if p["hunt"]:
            near = set()
            for e in enemies:
                if e.alive:
                    near |= {nb for nb in ai.neighbors(e.cell)
                             if arena.in_bounds(*nb) and arena.is_floor(*nb)}
            goals.append(near)
        return goals

    def _random_step(self, arena, here, bomb_cells, danger):
        dirs = list(ai._DIRS)
        self.rng.shuffle(dirs)
        for d in dirs:
            nb = (here[0] + d[0], here[1] + d[1])
            if (arena.in_bounds(*nb) and arena.is_floor(*nb)
                    and nb not in bomb_cells and ai.is_safe(nb, danger)):
                return d
        return None


class _Ghost:
    """Лёгкая «виртуальная» бомба для проверки пути отхода (без pygame-полей)."""

    def __init__(self, cell, owner, fire, now):
        self.col, self.row = cell
        self.owner = owner
        self.fire = fire
        self.remote = False
        self.exploded = False
        self._placed = now

    @property
    def cell(self):
        return self.col, self.row

    def time_left(self, now):
        return c.FUSE_MS
