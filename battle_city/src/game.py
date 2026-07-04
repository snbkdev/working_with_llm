"""Игровой цикл Battle City.

Этап 3: бой и правила — пули уничтожают врагов (+очки) и игрока (жизни,
респаун с неуязвимостью), разрушение базы = поражение, уничтожение всех
врагов = победа. Состояния: меню, игра, пауза, управление, финал.
"""

import math
import random
import sys

import pygame

from . import config as c
from .entities.enemy import Enemy
from .entities.explosion import Explosion
from .entities import particle
from .entities.powerup import PowerUp
from .entities.tank import Tank
from . import storage
from .menu import Menu
from .sound import Sounds
from .world import levels
from .world.level import Level

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_CONTROLS = "controls"
STATE_SETTINGS = "settings"
STATE_LEVELSTART = "levelstart"
STATE_NAME_ENTRY = "name_entry"
STATE_SCORES = "scores"
STATE_LEVELCLEAR = "levelclear"
STATE_GAMEOVER = "gameover"

MAIN_MENU_ITEMS = [
    ("Новая игра", "new_game", True),
    ("Загрузка", "load", False),        # активируется, если есть сохранение
    ("Рекорды", "scores", True),
    ("Настройки", "settings", True),
    ("Выход", "quit", True),
]
PAUSE_MENU_ITEMS = [
    ("Продолжить", "resume", True),
    ("Сохранить игру", "save", True),
    ("Загрузить игру", "load", False),  # активируется, если есть сохранение
    ("Управление", "controls", True),
    ("Выйти", "exit", True),
]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
        # Промежуточный холст: сцена рисуется на него, затем блиттится на экран
        # со смещением — так реализуется тряска экрана без правки всех вызовов.
        self.canvas = pygame.Surface((c.WIDTH, c.HEIGHT))
        pygame.display.set_caption("Battle City")

        # Геймпад (если подключён): движение + огонь + пауза
        self.joy = None
        try:
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joy = pygame.joystick.Joystick(0)
                self.joy.init()
        except pygame.error:
            self.joy = None

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Helvetica", 18, bold=True)
        self.small = pygame.font.SysFont("Helvetica", 13)
        # Крупные шрифты финальных экранов — создаём один раз, не покадрово
        self.big = pygame.font.SysFont("Helvetica", 44, bold=True)
        self.big2 = pygame.font.SysFont("Helvetica", 40, bold=True)
        self.sounds = Sounds(c.SOUND_ENABLED)

        # Рекорд из файла; new_record — побит ли он в текущей партии
        self.highscore = storage.load_highscore()
        self.new_record = False

        # Начинаем с главного меню; уровень создаётся при «Новой игре»
        self.state = STATE_MENU
        self.menu = Menu(MAIN_MENU_ITEMS, title="BATTLE CITY",
                         subtitle="Tank 1990 · pygame")
        self.pause_menu = Menu(PAUSE_MENU_ITEMS, title="ПАУЗА", overlay=True)
        self.toast = ""               # короткое уведомление (сохранено/загружено)
        self.toast_until = 0

        # Настройки (звук/громкость/сложность) — из файла, затем применяем
        self.sound_on = c.SOUND_ENABLED
        self.volume = c.DEFAULT_VOLUME
        self.difficulty = c.DEFAULT_DIFFICULTY
        self.settings_index = 0
        self.pending_name = ""        # ввод имени при новом рекорде
        self.new_score_rank = -1      # место нового результата в таблице (для подсветки)
        self.level_start_until = 0    # до какого момента показываем заставку «Уровень N»
        self.fade_until = 0           # затемнение-переход в бой
        self._load_settings()
        self._apply_settings()
        self._sync_menu_saves()

    def reset(self):
        """Новая игра с первого уровня: сбрасываются очки и жизни."""
        self.lives = c.PLAYER_LIVES
        self.score = 0
        self.new_record = False
        self.load_level(0)

    def load_level(self, index, carry_level=0):
        """Загружает уровень index и сбрасывает поле.

        Очки и жизни сохраняются между уровнями (их обнуляет только reset).
        carry_level — апгрейд танка (звёзды), переносимый со следующего уровня.
        """
        self.level_index = index
        self.level = Level(levels.load_level(index))
        col, row = self.level.player_spawn
        self.player = Tank(col, row, c.UP, is_player=True)
        if carry_level:
            self.player.set_level(carry_level)      # звезда сохраняется между уровнями
        self.bullets = []
        self.explosions = []
        self.powerups = []
        self.steel_until = None       # пока активна стальная броня базы («сталь»)
        self.freeze_until = None      # пока враги заморожены («часы»)
        self.last_shot = 0
        self.result = None
        # Кратковременная неуязвимость на старте
        self.player_invuln_until = (
            pygame.time.get_ticks() + c.PLAYER_INVULN_MS
        )

        # Тряска экрана и вспышка
        self.shake_until = 0
        self.shake_mag = 0
        self.shake_dur = 1
        self.flash_until = 0

        # Предупреждения базы
        self.base_alert = False       # враг в опасной близости от базы
        self.last_alarm = 0           # когда последний раз пикнула тревога

        # Враги: случайное число за уровень (10–15)
        self.enemies = []
        self.spawns_pending = []      # «порталы»: враг вот-вот появится (анимация)
        self.enemies_to_spawn = random.randint(*self.enemy_count)
        self.spawn_index = 0
        # Пауза перед первым врагом (~6 сек после старта)
        self.next_spawn_at = pygame.time.get_ticks() + c.ENEMY_START_DELAY

    # --- Переходы состояний ---
    def start_new_game(self):
        self.reset()
        self._show_stage()

    def _show_stage(self):
        """Заставка «Уровень N» перед боем."""
        self.level_start_until = pygame.time.get_ticks() + c.LEVELSTART_MS
        self.state = STATE_LEVELSTART

    def _begin_play(self):
        """Старт боя после заставки — с плавным появлением из затемнения."""
        self.fade_until = pygame.time.get_ticks() + c.FADE_MS
        self.state = STATE_PLAYING

    def back_to_menu(self):
        self.sounds.engine_stop()
        self._sync_menu_saves()
        self.state = STATE_MENU

    def pause(self):
        self.sounds.engine_stop()
        self._sync_menu_saves()
        self.pause_menu.index = 0
        self.state = STATE_PAUSED

    def _sync_menu_saves(self):
        """Пункты «Загрузка/Загрузить игру» активны только при наличии сейва."""
        has = storage.has_save()
        self.menu.items[1] = (self.menu.items[1][0], "load", has)
        self.pause_menu.items[2] = (self.pause_menu.items[2][0], "load", has)
        if not self.menu.items[self.menu.index][2]:
            self.menu.index = self.menu._first_active()

    def _toast(self, text, ms=1500):
        self.toast = text
        self.toast_until = pygame.time.get_ticks() + ms

    # --- Настройки ---
    def _load_settings(self):
        data = storage.load_settings()
        if not data:
            return
        self.sound_on = bool(data.get("sound", self.sound_on))
        try:
            self.volume = max(0.0, min(1.0, float(data.get("volume", self.volume))))
        except (TypeError, ValueError):
            pass
        d = data.get("difficulty", self.difficulty)
        if d in c.DIFFICULTIES:
            self.difficulty = d

    def _apply_settings(self):
        """Пробрасывает настройки в звук и параметры сложности."""
        self.sounds.set_enabled(self.sound_on)
        self.sounds.set_volume(self.volume)
        if self.sound_on:
            self.sounds.music_start()
        else:
            self.sounds.music_stop()
        preset = c.DIFFICULTIES[self.difficulty]
        self.enemy_count = tuple(preset["count"])
        self.spawn_interval = preset["spawn_interval"]
        self.max_active = preset["max_active"]

    def _save_settings(self):
        storage.save_settings({
            "sound": self.sound_on,
            "volume": round(self.volume, 2),
            "difficulty": self.difficulty,
        })

    def resume(self):
        self.state = STATE_PLAYING

    # --- Бой и исходы ---
    def spawn_explosion(self, pos, big=True):
        self.explosions.append(Explosion(pos[0], pos[1], big))

    # --- Бонусы (power-ups) ---
    def spawn_powerup(self):
        """Роняет случайный бонус на свободную клетку поля."""
        kind = random.choice(c.POWERUP_KINDS)
        for _ in range(40):
            col = random.randint(0, c.COLS - 1)
            row = random.randint(0, c.ROWS - 1)
            if ((col, row) in self.level.bricks or (col, row) in self.level.steels
                    or (col, row) in self.level.water):
                continue
            if (col, row) == self.level.base_cell:
                continue
            cell = pygame.Rect(col * c.TILE, row * c.TILE, c.TILE, c.TILE)
            if cell.colliderect(self.player.rect):
                continue
            if any(cell.colliderect(e.rect) for e in self.enemies):
                continue
            self.powerups.append(PowerUp(col, row, kind))
            return

    def apply_powerup(self, kind):
        now = pygame.time.get_ticks()
        if kind == "star":
            # Звезда: апгрейд танка — крупнее корпус + огневая мощь (см. shoot)
            self.player.set_level(min(self.player.level + 1, c.PLAYER_MAX_LEVEL))
        elif kind == "clock":
            # Часы: заморозить всех врагов на время
            self.freeze_until = now + c.FREEZE_DURATION
        elif kind == "bomb":
            # Бомбочка: мгновенно взорвать всех врагов на поле
            killed = False
            for e in self.enemies:
                if e.alive:
                    self.spawn_explosion(e.rect.center, big=True)
                    e.alive = False
                    self.score += e.score
                    killed = True
            if killed:
                self.sounds.play_explosion()
                self._shake(c.SHAKE_BIG)
                self._flash()
        elif kind == "steel":
            # Сталь: одеть базу в стальную броню на время
            self.level.set_base_walls("steel")
            self.steel_until = now + c.STEEL_DURATION
        elif kind == "life":
            # Орёл: +1 жизнь (с потолком)
            self.lives = min(self.lives + 1, c.PLAYER_MAX_LIVES)

    def respawn_player(self):
        col, row = self.level.player_spawn
        self.player = Tank(col, row, c.UP, is_player=True)
        self.player_invuln_until = (
            pygame.time.get_ticks() + c.PLAYER_INVULN_MS
        )

    def player_hit(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over("lose")
        else:
            self.respawn_player()

    def game_over(self, result):
        if self.state != STATE_PLAYING:
            return
        self.result = result
        self.sounds.engine_stop()
        # Счёт попал в таблицу рекордов? Просим имя, затем показываем таблицу
        if storage.qualifies(self.score):
            self.new_record = True
            self.pending_name = ""
            self.state = STATE_NAME_ENTRY
        else:
            self.new_record = False
            self.state = STATE_GAMEOVER

    def level_cleared(self):
        """Уровень зачищен: следующий уровень либо финальная победа."""
        if self.state != STATE_PLAYING:
            return
        self.sounds.engine_stop()
        if self.level_index + 1 < levels.level_count():
            self.state = STATE_LEVELCLEAR     # ждём подтверждения игрока
        else:
            self.game_over("win")             # пройден последний уровень

    def next_level(self):
        self.load_level(self.level_index + 1, carry_level=self.player.level)
        self._show_stage()

    # --- Сохранение / загрузка партии ---
    def serialize(self):
        """Снапшот текущей партии для сохранения в JSON."""
        now = pygame.time.get_ticks()
        return {
            "level_index": self.level_index,
            "score": self.score,
            "lives": self.lives,
            "player_level": self.player.level,
            "enemies_to_spawn": self.enemies_to_spawn,
            "spawn_index": self.spawn_index,
            "bricks": [list(cell) for cell in self.level.bricks],
            "steels": [list(cell) for cell in self.level.steels],
            "enemies": [{
                "x": e.x, "y": e.y, "dir": list(e.dir), "kind": e.kind,
                "hp": e.hp, "bonus": e.bonus, "reinforced": e.reinforced,
            } for e in self.enemies],
            "freeze_remaining": max(0, self.freeze_until - now) if self.freeze_until else 0,
            "steel_remaining": max(0, self.steel_until - now) if self.steel_until else 0,
        }

    def apply_save(self, data):
        """Восстанавливает партию из снапшота (см. serialize)."""
        now = pygame.time.get_ticks()
        self.load_level(int(data["level_index"]),
                        carry_level=int(data.get("player_level", 0)))
        self.score = int(data["score"])
        self.lives = int(data["lives"])
        self.enemies_to_spawn = int(data["enemies_to_spawn"])
        self.spawn_index = int(data["spawn_index"])
        self.level.bricks = {tuple(cell) for cell in data["bricks"]}
        self.level.steels = {tuple(cell) for cell in data["steels"]}

        self.enemies = []
        for es in data.get("enemies", []):
            e = Enemy(0, 0, bonus=es["bonus"], kind=es["kind"],
                      reinforced=es["reinforced"])
            e.x, e.y = float(es["x"]), float(es["y"])
            e.dir = tuple(es["dir"])
            e.hp = int(es["hp"])
            if e.max_hp > 1:
                e.body_color = e._armor_color()
            self.enemies.append(e)

        fr = int(data.get("freeze_remaining", 0))
        self.freeze_until = now + fr if fr > 0 else None
        sr = int(data.get("steel_remaining", 0))
        self.steel_until = now + sr if sr > 0 else None

    def _save_game(self):
        if storage.save_game(self.serialize()):
            self._toast("Игра сохранена")
        else:
            self._toast("Не удалось сохранить")

    def _load_game(self):
        data = storage.load_game()
        if not data:
            return False
        try:
            self.apply_save(data)
        except (KeyError, ValueError, TypeError):
            return False           # повреждённый сейв — молча игнорируем
        self._toast("Игра загружена")
        self.state = STATE_PLAYING
        return True

    # --- Стрельба ---
    def player_bullets(self):
        return [b for b in self.bullets if b.owner == "player"]

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot < c.PLAYER_SHOOT_COOLDOWN:
            return
        lvl = self.player.level
        max_bullets = 2 if lvl >= 2 else c.PLAYER_MAX_BULLETS   # звезда: 2 пули
        if len(self.player_bullets()) >= max_bullets:
            return
        b = self.player.shoot()
        if lvl >= 1:
            b.speed = c.BULLET_SPEED + 3        # звезда: пуля быстрее
        b.power = lvl >= 3                       # звезда: пробивает сталь
        self.bullets.append(b)
        self.sounds.play_shoot()
        self.last_shot = now

    # --- Появление врагов ---
    def _roll_enemy_kind(self):
        """Выбирает тип врага по составу текущего уровня (взвешенный рандом)."""
        level = self.level_index + 1
        weights = c.ENEMY_SPAWN_TABLE[0][1]
        for min_lvl, table in c.ENEMY_SPAWN_TABLE:
            if level >= min_lvl:
                weights = table
        return random.choices(list(weights), list(weights.values()))[0]

    def _cell_rect(self, cell):
        return pygame.Rect(cell[0] * c.TILE, cell[1] * c.TILE, c.TILE, c.TILE)

    def try_spawn_enemy(self, now):
        if self.enemies_to_spawn <= 0:
            return
        # Активные + уже «прорастающие» порталы не превышают лимит на поле
        if len(self.enemies) + len(self.spawns_pending) >= self.max_active:
            return
        if now < self.next_spawn_at:
            return

        spawns = self.level.enemy_spawns           # лево / центр / право
        occupied = ([t.rect for t in self.enemies] + [self.player.rect]
                    + [self._cell_rect(s["cell"]) for s in self.spawns_pending])

        # Берём первую свободную точку, перебирая по кругу от текущего индекса
        n = len(spawns)
        reinforced = self.level_index + 1 >= c.TOUGH_ENEMY_FROM_LEVEL  # после 10 уровня
        for k in range(n):
            cell = spawns[(self.spawn_index + k) % n]
            if any(self._cell_rect(cell).colliderect(o) for o in occupied):
                continue
            # Ставим «портал»: враг появится после анимации (даём игроку среагировать)
            self.spawns_pending.append({
                "cell": cell,
                "kind": self._roll_enemy_kind(),
                "bonus": random.random() < c.BONUS_ENEMY_CHANCE,
                "reinforced": reinforced,
                "start": now,
            })
            self.enemies_to_spawn -= 1
            self.spawn_index = (self.spawn_index + k + 1) % n
            self.next_spawn_at = now + self.spawn_interval
            return
        # Все точки заняты — попробуем в следующий раз

    def _resolve_spawns(self, now):
        """Дозревшие «порталы» превращает во врагов, если клетка свободна."""
        still = []
        for s in self.spawns_pending:
            if now - s["start"] < c.SPAWN_ANIM_MS:
                still.append(s)
                continue
            enemy = Enemy(*s["cell"], bonus=s["bonus"], kind=s["kind"],
                          reinforced=s["reinforced"])
            blockers = [t.rect for t in self.enemies] + [self.player.rect]
            if any(enemy.rect.colliderect(b) for b in blockers):
                still.append(s)            # клетка занята — ждём следующий кадр
            else:
                self.enemies.append(enemy)
        self.spawns_pending = still

    # --- Тряска экрана и вспышка ---
    def _shake(self, mag, dur=c.SHAKE_MS):
        now = pygame.time.get_ticks()
        # Не гасим более сильную тряску слабой
        if now < self.shake_until and mag < self.shake_mag:
            return
        self.shake_mag = mag
        self.shake_dur = dur
        self.shake_until = now + dur

    def _flash(self):
        self.flash_until = pygame.time.get_ticks() + c.FLASH_MS

    def _shake_offset(self, now):
        if now >= self.shake_until:
            return (0, 0)
        frac = (self.shake_until - now) / self.shake_dur   # затухание к нулю
        mag = max(1, int(self.shake_mag * frac))
        return (random.randint(-mag, mag), random.randint(-mag, mag))

    # --- Ввод ---
    def handle_game_event(self, e):
        """Дискретные события в режиме игры (стрельба, пауза, рестарт)."""
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                self.pause()
            elif e.key == pygame.K_ESCAPE:
                self.back_to_menu()
            elif e.key == pygame.K_r:
                self.reset()
            elif e.key == pygame.K_SPACE:
                self.shoot()
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button in (6, 7, 9):        # select/start — пауза
                self.pause()
            else:                            # любая другая кнопка — огонь
                self.shoot()

    def read_direction(self, keys):
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            return c.UP
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            return c.DOWN
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            return c.LEFT
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            return c.RIGHT
        return self._joy_direction()

    def _joy_direction(self):
        """Направление с геймпада: крестовина (hat) или левый стик."""
        if not self.joy:
            return None
        hx = hy = 0
        try:
            if self.joy.get_numhats() > 0:
                hx, hy = self.joy.get_hat(0)
            ax = self.joy.get_axis(0) if self.joy.get_numaxes() > 0 else 0.0
            ay = self.joy.get_axis(1) if self.joy.get_numaxes() > 1 else 0.0
        except pygame.error:
            return None
        dead = 0.5
        dx = hx if hx else (1 if ax > dead else -1 if ax < -dead else 0)
        # hat: вверх = +1; ось Y: вверх = отрицательна — приводим к «вниз = +1»
        dy = (-hy) if hy else (1 if ay > dead else -1 if ay < -dead else 0)
        if dx == 0 and dy == 0:
            return None
        if abs(dx) >= abs(dy):
            return c.RIGHT if dx > 0 else c.LEFT
        return c.DOWN if dy > 0 else c.UP

    # --- Логика ---
    def update(self):
        now = pygame.time.get_ticks()
        self.try_spawn_enemy(now)
        self._resolve_spawns(now)      # дозревшие «порталы» → враги

        keys = pygame.key.get_pressed()
        direction = self.read_direction(keys)
        solids = self.level.solid_rects()

        # Игрок (враги — препятствия). На льду — скольжение по инерции.
        enemy_rects = [e.rect for e in self.enemies]
        on_ice = self.level.is_ice(self.player.rect.center)
        moved = False
        if direction is not None:
            self.player.face(direction)
            moved = self.player.try_move(solids, enemy_rects)
            if moved and on_ice:                     # запоминаем инерцию
                self.player.glide_dir = direction
                self.player.glide_until = now + c.ICE_SLIDE_MS
        elif on_ice and now < self.player.glide_until and self.player.glide_dir:
            self.player.dir = self.player.glide_dir  # скользим по льду после отпускания
            moved = self.player.try_move(solids, enemy_rects)
            if not moved:
                self.player.glide_until = 0          # упёрлись — стоп

        # Звук двигателя — пока игрок реально едет
        if moved:
            self.sounds.engine_start()
        else:
            self.sounds.engine_stop()

        # Подбор бонусов наездом
        for p in self.powerups:
            if p.alive and self.player.rect.colliderect(p.rect):
                self.apply_powerup(p.kind)
                p.alive = False
                self.score += c.POWERUP_SCORE
                self.sounds.play_pickup()

        # Истечение стальной брони базы («сталь»)
        if self.steel_until is not None and now >= self.steel_until:
            self.level.set_base_walls("brick")
            self.steel_until = None

        # Истечение заморозки врагов («часы»)
        if self.freeze_until is not None and now >= self.freeze_until:
            self.freeze_until = None

        # Враги (ИИ). Пока действуют «часы» — стоят на месте и не стреляют.
        frozen = self.freeze_until is not None and now < self.freeze_until
        if not frozen:
            for e in self.enemies:
                blockers = [o.rect for o in self.enemies if o is not e]
                blockers.append(self.player.rect)
                bullet = e.update_ai(solids, blockers)
                if bullet is not None:
                    self.bullets.append(bullet)

        # Пули
        for b in self.bullets:
            b.update()
            if not (0 <= b.x <= c.FIELD_W and 0 <= b.y <= c.FIELD_H):
                b.alive = False
                continue
            # Попадание в стену/базу. Пуля танка 3-го уровня пробивает всё:
            # разрушает и кирпич, и сталь и летит дальше, не гаснет.
            piercing = b.owner == "player" and b.power
            res = self.level.hit(b.rect, pierce_steel=piercing)
            if res:
                if res == "base":
                    b.alive = False
                    self.spawn_explosion(b.rect.center, big=True)
                    self.sounds.play_explosion()
                    self._shake(c.SHAKE_BIG, int(c.SHAKE_MS * 1.5))
                    self._flash()
                    self.game_over("lose")
                    continue
                self.spawn_explosion(b.rect.center, big=False)
                self.sounds.play_hit()
                if not piercing:
                    b.alive = False
                    continue
                # прокачанная пуля прошивает стену насквозь — не убиваем её
            # Попадание в танк
            self._bullet_vs_tanks(b, now)

        # Взаимное уничтожение встречных пуль
        self._bullets_cancel()

        # Взрывы гаснут по истечении анимации, бонусы — по таймауту
        for ex in self.explosions:
            ex.update(now)
        for p in self.powerups:
            p.update(now)

        # Убираем уничтоженных врагов, погасшие пули, взрывы и бонусы
        self.enemies = [e for e in self.enemies if e.alive]
        self.bullets = [b for b in self.bullets if b.alive]
        self.explosions = [ex for ex in self.explosions if ex.alive]
        self.powerups = [p for p in self.powerups if p.alive]

        # Тревога «враг у базы»: мигание + периодический сигнал
        self._update_base_alert(now)

        # Уровень зачищен: все враги уничтожены, порталов нет и больше не появятся
        if self.enemies_to_spawn == 0 and not self.enemies and not self.spawns_pending:
            self.level_cleared()

    def _bullet_vs_tanks(self, b, now):
        if b.owner == "player":
            for e in self.enemies:
                if e.alive and b.rect.colliderect(e.rect):
                    b.alive = False
                    if not e.damage():
                        # броневой враг выдержал попадание — только «тик» и вспышка
                        self.spawn_explosion(e.rect.center, big=False)
                        self.sounds.play_hit()
                        return
                    e.alive = False
                    self.score += e.score
                    self.spawn_explosion(e.rect.center, big=True)
                    self.sounds.play_explosion()
                    if e.bonus:
                        self.spawn_powerup()
                    return
        else:  # пуля врага
            if b.rect.colliderect(self.player.rect):
                b.alive = False
                if now >= self.player_invuln_until:
                    self.spawn_explosion(self.player.rect.center, big=True)
                    self.sounds.play_explosion()
                    self._shake(c.SHAKE_SMALL)
                    self.player_hit()
                else:
                    self.sounds.play_hit()      # щит поглотил пулю — лёгкий «тик»

    def _update_base_alert(self, now):
        """Тревога, если враг в опасной близости от базы: мигание + сигнал."""
        if not self.level.base_alive:
            self.base_alert = False
            return
        bx, by = self.level.base_rect().center
        self.base_alert = any(
            abs(e.rect.centerx - bx) <= c.BASE_ALERT_RADIUS
            and abs(e.rect.centery - by) <= c.BASE_ALERT_RADIUS
            for e in self.enemies
        )
        if self.base_alert and now - self.last_alarm >= c.BASE_ALERT_SOUND_MS:
            self.sounds.play_alarm()
            self.last_alarm = now

    def _bullets_cancel(self):
        pb = [b for b in self.bullets if b.alive and b.owner == "player"]
        eb = [b for b in self.bullets if b.alive and b.owner == "enemy"]
        for p in pb:
            for e in eb:
                if p.alive and e.alive and p.rect.colliderect(e.rect):
                    p.alive = False
                    e.alive = False
                    break

    # --- Отрисовка ---
    def draw(self):
        if self.state == STATE_MENU:
            self.menu.draw(self.screen)
            rec = self.font.render(
                f"РЕКОРД   {self.highscore:05d}", True, c.BASE_COLOR)
            self.screen.blit(rec, (c.WIDTH // 2 - rec.get_width() // 2, 36))
            pygame.display.flip()
            return
        if self.state == STATE_SETTINGS:
            self.draw_settings()
            pygame.display.flip()
            return
        if self.state == STATE_NAME_ENTRY:
            self.draw_name_entry()
            pygame.display.flip()
            return
        if self.state == STATE_SCORES:
            self.draw_scores()
            pygame.display.flip()
            return
        if self.state == STATE_LEVELSTART:
            self.draw_levelstart()
            pygame.display.flip()
            return

        # Сцену и оверлеи рисуем на холст, затем блиттим на экран со сдвигом-тряской
        now = pygame.time.get_ticks()
        display = self.screen
        self.screen = self.canvas
        self._draw_scene()
        if self.state == STATE_PAUSED:
            self.pause_menu.draw(self.screen)
        elif self.state == STATE_CONTROLS:
            self.draw_controls()
        elif self.state == STATE_LEVELCLEAR:
            self.draw_levelclear()
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover()
        self.screen = display

        ox, oy = self._shake_offset(now)
        if ox or oy:
            display.fill(c.BG_COLOR)
        display.blit(self.canvas, (ox, oy))

        # Белая вспышка поверх поля (разрушение базы / бомба)
        if now < self.flash_until:
            frac = (self.flash_until - now) / c.FLASH_MS
            flash = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(150 * frac)))
            display.blit(flash, (ox, oy))

        # Затемнение-переход: плавное появление боя из черноты
        if now < self.fade_until:
            fade = pygame.Surface((c.WIDTH, c.HEIGHT))
            fade.set_alpha(int(255 * (self.fade_until - now) / c.FADE_MS))
            display.blit(fade, (0, 0))
        pygame.display.flip()

    def _draw_scene(self):
        self.screen.fill(c.BG_COLOR)
        pygame.draw.rect(self.screen, c.FIELD_COLOR, (0, 0, c.FIELD_W, c.FIELD_H))
        self.draw_grid()
        self.level.draw(self.screen)
        now = pygame.time.get_ticks()
        self._draw_base_warnings(now)                # тревога/мигание брони базы
        for p in self.powerups:
            p.draw(self.screen)
        self._draw_spawns(now)                       # «порталы» появления врагов
        self.player.draw(self.screen)
        if now < self.player_invuln_until:          # щит: респаун или каска
            self._draw_shield(self.player.rect, now)
        frozen = self.freeze_until is not None and now < self.freeze_until
        for e in self.enemies:
            e.draw(self.screen)
            if e.armored:                            # броневой/усиленный — стальная окантовка
                pygame.draw.rect(self.screen, c.STEEL_COLOR, e.rect, 2, border_radius=5)
            if frozen:                               # заморожены «часами» — ледяной налёт
                ice = pygame.Surface((e.rect.width, e.rect.height), pygame.SRCALPHA)
                ice.fill((*c.FREEZE_TINT, 90))
                self.screen.blit(ice, e.rect.topleft)
                pygame.draw.rect(self.screen, c.FREEZE_TINT, e.rect, 1, border_radius=5)
            if e.bonus and (now // 250) % 2 == 0:    # носитель бонуса мигает рамкой
                pygame.draw.rect(self.screen, c.STAR_COLOR, e.rect, 2, border_radius=5)
        for b in self.bullets:
            b.draw(self.screen)
        for ex in self.explosions:
            ex.draw(self.screen)
        self.level.draw_forest(self.screen)         # листва поверх танков — засады
        pygame.draw.rect(self.screen, c.FIELD_BORDER, (0, 0, c.FIELD_W, c.FIELD_H), 2)
        self.draw_hud()
        self._draw_toast(now)

    def _draw_toast(self, now):
        """Короткое уведомление вверху поля (сохранено/загружено)."""
        if now >= self.toast_until or not self.toast:
            return
        surf = self.font.render(self.toast, True, c.WHITE)
        pad = 10
        bw, bh = surf.get_width() + pad * 2, surf.get_height() + pad
        bx = (c.FIELD_W - bw) // 2
        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        box.fill((20, 24, 30, 220))
        self.screen.blit(box, (bx, 16))
        pygame.draw.rect(self.screen, c.PLAYER_COLOR, (bx, 16, bw, bh), 1)
        self.screen.blit(surf, (bx + pad, 16 + pad // 2))

    def _draw_shield(self, rect, now):
        """Пульсирующее кольцо-щит вокруг танка (неуязвимость)."""
        radius = rect.width // 2 + 4 + (now // 80) % 3
        pygame.draw.circle(self.screen, c.SHIELD_COLOR, rect.center, radius, 2)

    def _draw_base_warnings(self, now):
        """Пульсирующая рамка тревоги у базы и мигание брони на исходе «стали»."""
        if not self.level.base_alive:
            return
        blink = (now // 250) % 2 == 0
        if self.base_alert and blink:               # враг близко — красная рамка
            r = self.level.base_rect().inflate(6, 6)
            pygame.draw.rect(self.screen, c.BASE_ALERT_COLOR, r, 3, border_radius=4)
        if self.steel_until is not None:            # «сталь» вот-вот кончится — мигает броня
            left = self.steel_until - now
            if 0 < left <= c.STEEL_WARN_MS and blink:
                for col, row in self.level.base_wall:
                    rr = pygame.Rect(col * c.TILE, row * c.TILE, c.TILE, c.TILE)
                    pygame.draw.rect(self.screen, c.BASE_WARN_COLOR, rr, 2)

    def _draw_spawns(self, now):
        """Мигающая звезда-портал на месте скорого появления врага."""
        for s in self.spawns_pending:
            cx = s["cell"][0] * c.TILE + c.TILE // 2
            cy = s["cell"][1] * c.TILE + c.TILE // 2
            phase = (now // 70) % 2
            pulse = abs(math.sin((now - s["start"]) / 130.0))
            r = int(c.TILE * 0.18 + c.TILE * 0.22 * pulse)
            self._mini_star(cx, cy, r, c.SPAWN_COLOR_A if phase else c.SPAWN_COLOR_B)
            self._mini_star(cx, cy, max(2, r // 2),
                            c.SPAWN_COLOR_B if phase else c.SPAWN_COLOR_A)

    def draw_grid(self):
        for x in range(c.TILE, c.FIELD_W, c.TILE):
            pygame.draw.line(self.screen, c.GRID_LINE, (x, 0), (x, c.FIELD_H))
        for y in range(c.TILE, c.FIELD_H, c.TILE):
            pygame.draw.line(self.screen, c.GRID_LINE, (0, y), (c.FIELD_W, y))

    def _mini_tank(self, x, y, size, body, track):
        """Маленькая иконка танка для панели."""
        pygame.draw.rect(self.screen, track, (x, y, size, size), border_radius=2)
        pygame.draw.rect(self.screen, body,
                         (x + 3, y + 2, size - 6, size - 4), border_radius=2)
        pygame.draw.rect(self.screen, track,
                         (x + size // 2 - 1, y - 2, 2, size // 2 + 2))

    def _mini_star(self, cx, cy, r, color):
        """Маленькая звезда для индикатора апгрейда танка."""
        pts = []
        for i in range(10):
            rad = r if i % 2 == 0 else r * 0.42
            ang = -math.pi / 2 + math.pi * i / 5
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        pygame.draw.polygon(self.screen, color, pts)

    def _draw_active_effects(self, x, y):
        """Иконки активных бонусов с убывающей полоской времени."""
        now = pygame.time.get_ticks()
        effects = []
        if self.freeze_until and now < self.freeze_until:
            effects.append(("Заморозка", c.CLOCK_COLOR,
                            (self.freeze_until - now) / c.FREEZE_DURATION))
        if self.steel_until and now < self.steel_until:
            effects.append(("Броня базы", c.STEEL_ITEM_COLOR,
                            (self.steel_until - now) / c.STEEL_DURATION))
        if now < self.player_invuln_until:
            effects.append(("Щит", c.SHIELD_COLOR,
                            (self.player_invuln_until - now) / c.PLAYER_INVULN_MS))
        if not effects:
            return

        lbl = self.small.render("ЭФФЕКТЫ", True, c.HUD_TEXT)
        self.screen.blit(lbl, (x + 14, y))
        y += 20
        for name, color, frac in effects:
            frac = max(0.0, min(1.0, frac))
            pygame.draw.rect(self.screen, color, (x + 14, y + 2, 10, 10), border_radius=2)
            self.screen.blit(self.small.render(name, True, c.HUD_TEXT), (x + 30, y))
            bw, by = c.HUD_W - 44, y + 16
            pygame.draw.rect(self.screen, (70, 70, 70), (x + 14, by, bw, 4), border_radius=2)
            pygame.draw.rect(self.screen, color, (x + 14, by, int(bw * frac), 4), border_radius=2)
            y += 28

    def draw_hud(self):
        x = c.FIELD_W
        pygame.draw.rect(self.screen, c.HUD_BG, (x, 0, c.HUD_W, c.HEIGHT))

        title = self.font.render("BATTLE CITY", True, c.HUD_TEXT)
        self.screen.blit(title, (x + (c.HUD_W - title.get_width()) // 2, 18))

        # --- Очки и рекорд ---
        slbl = self.small.render("ОЧКИ", True, c.HUD_TEXT)
        self.screen.blit(slbl, (x + 14, 44))
        snum = self.font.render(str(self.score), True, (40, 60, 90))
        self.screen.blit(snum, (x + c.HUD_W - 14 - snum.get_width(), 40))
        # Рекорд растёт «вживую», как только очки его превышают
        rec = max(self.score, self.highscore)
        rlbl = self.small.render("РЕКОРД", True, c.HUD_TEXT)
        self.screen.blit(rlbl, (x + 14, 64))
        rnum = self.small.render(f"{rec:05d}", True, (110, 90, 30))
        self.screen.blit(rnum, (x + c.HUD_W - 14 - rnum.get_width(), 64))
        pygame.draw.line(self.screen, (70, 70, 70),
                         (x + 12, 84), (x + c.HUD_W - 12, 84), 1)

        # --- Жизни игрока ---
        lbl = self.small.render("ЖИЗНИ", True, c.HUD_TEXT)
        self.screen.blit(lbl, (x + 14, 88))
        num = self.font.render(str(self.lives), True, (60, 90, 40))
        self.screen.blit(num, (x + c.HUD_W - 32, 82))
        for i in range(min(self.lives, 5)):          # иконок — до 5, число рядом точнее
            self._mini_tank(x + 16 + i * 24, 110, 16, c.PLAYER_COLOR, c.PLAYER_TRACK)

        pygame.draw.line(self.screen, (70, 70, 70),
                         (x + 12, 138), (x + c.HUD_W - 12, 138), 1)

        # --- Враги (осталось за уровень) ---
        remaining = (self.enemies_to_spawn + len(self.enemies)
                     + len(self.spawns_pending))
        lbl2 = self.small.render("ВРАГИ", True, c.HUD_TEXT)
        self.screen.blit(lbl2, (x + 14, 152))
        num2 = self.font.render(str(remaining), True, (70, 30, 30))
        self.screen.blit(num2, (x + c.HUD_W - 32, 146))
        # Сетка иконок оставшихся врагов
        ix, iy = x + 16, 176
        for i in range(remaining):
            col = i % 6
            row = i // 6
            self._mini_tank(ix + col * 21, iy + row * 22, 15,
                            c.ENEMY_COLOR, c.ENEMY_TRACK)

        # --- Активные бонусы (с таймером) ---
        self._draw_active_effects(x, 300)

        # --- Апгрейд танка (звёзды) ---
        tlbl = self.small.render("ТАНК", True, c.HUD_TEXT)
        self.screen.blit(tlbl, (x + 14, c.HEIGHT - 102))
        for i in range(c.PLAYER_MAX_LEVEL):
            sx = x + 56 + i * 18
            sy = c.HEIGHT - 96
            color = c.STAR_COLOR if i < self.player.level else (90, 90, 90)
            self._mini_star(sx, sy, 7, color)

        # --- Уровень и подсказки ---
        lvl = self.small.render(
            f"Уровень {self.level_index + 1}/{levels.level_count()}",
            True, c.HUD_TEXT)
        self.screen.blit(lvl, (x + 14, c.HEIGHT - 76))

        hints = ["P — пауза", "Esc — в меню"]
        y = c.HEIGHT - 50
        for line in hints:
            surf = self.small.render(line, True, c.HUD_TEXT)
            self.screen.blit(surf, (x + 14, y))
            y += 20

    # --- Экран настроек ---
    SETTINGS_ROWS = 4                        # Звук, Громкость, Сложность, Назад

    def open_settings(self):
        self.settings_index = 0
        self.state = STATE_SETTINGS

    def _close_settings(self):
        self._save_settings()
        self.state = STATE_MENU

    def _adjust_setting(self, d):
        if self.settings_index == 0:         # Звук вкл/выкл
            self.sound_on = not self.sound_on
        elif self.settings_index == 1:       # Громкость (±20%)
            self.volume = max(0.0, min(1.0, round(self.volume + 0.2 * d, 2)))
        elif self.settings_index == 2:       # Сложность
            order = c.DIFFICULTY_ORDER
            i = (order.index(self.difficulty) + d) % len(order)
            self.difficulty = order[i]
        self._apply_settings()
        if self.sounds.enabled:              # звуковой отклик на изменение
            self.sounds.play_pickup()

    def handle_settings_event(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key in (pygame.K_UP, pygame.K_w):
            self.settings_index = (self.settings_index - 1) % self.SETTINGS_ROWS
        elif e.key in (pygame.K_DOWN, pygame.K_s):
            self.settings_index = (self.settings_index + 1) % self.SETTINGS_ROWS
        elif e.key in (pygame.K_LEFT, pygame.K_a):
            self._adjust_setting(-1)
        elif e.key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust_setting(1)
        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.settings_index == self.SETTINGS_ROWS - 1:
                self._close_settings()
            else:
                self._adjust_setting(1)
        elif e.key == pygame.K_ESCAPE:
            self._close_settings()

    def draw_settings(self):
        self.screen.fill(c.BG_COLOR)
        cx = c.WIDTH // 2
        title = self.big.render("НАСТРОЙКИ", True, c.PLAYER_COLOR)
        self.screen.blit(title, (cx - title.get_width() // 2, 70))

        rows = [
            ("Звук", "Вкл" if self.sound_on else "Выкл", True),
            ("Громкость", f"{int(self.volume * 100)}%", True),
            ("Сложность", self.difficulty, True),
            ("Назад", "", False),
        ]
        y = 190
        for i, (label, val, adjustable) in enumerate(rows):
            sel = i == self.settings_index
            color = c.ACCENT if sel else c.TEXT_COLOR
            lab = self.font.render(label, True, color)
            self.screen.blit(lab, (cx - 170, y))
            if val:
                vsurf = self.font.render(val, True, color)
                vx = cx + 150 - vsurf.get_width() // 2
                self.screen.blit(vsurf, (vx, y))
                if sel and adjustable:       # стрелки ‹ ›
                    my = y + vsurf.get_height() // 2
                    pygame.draw.polygon(self.screen, color,
                                        [(cx + 66, my), (cx + 78, my - 7), (cx + 78, my + 7)])
                    pygame.draw.polygon(self.screen, color,
                                        [(cx + 234, my), (cx + 222, my - 7), (cx + 222, my + 7)])
            if sel:
                ty = y + lab.get_height() // 2
                pygame.draw.polygon(self.screen, color,
                                    [(cx - 190, ty - 7), (cx - 178, ty), (cx - 190, ty + 7)])
            y += 60

        hint = self.small.render(
            "↑↓ — выбор · ←→ — изменить · Enter/Esc — назад", True, (150, 150, 150))
        self.screen.blit(hint, (cx - hint.get_width() // 2, c.HEIGHT - 56))

    # --- Заставка «Уровень N» ---
    def handle_levelstart_event(self, e):
        if e.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
            self._begin_play()               # пропустить заставку

    def draw_levelstart(self):
        self.screen.fill(c.BG_COLOR)
        cx, cy = c.WIDTH // 2, c.HEIGHT // 2
        t = self.big.render("УРОВЕНЬ", True, c.PLAYER_COLOR)
        self.screen.blit(t, (cx - t.get_width() // 2, cy - 90))
        num = self.big.render(
            f"{self.level_index + 1} / {levels.level_count()}", True, c.WHITE)
        self.screen.blit(num, (cx - num.get_width() // 2, cy - 30))
        # Пара танков-иконок навстречу друг другу
        self._mini_tank(cx - 60, cy + 44, 20, c.PLAYER_COLOR, c.PLAYER_TRACK)
        self._mini_tank(cx + 40, cy + 44, 20, c.ENEMY_COLOR, c.ENEMY_TRACK)
        hint = self.small.render("Пробел — начать", True, (150, 150, 150))
        self.screen.blit(hint, (cx - hint.get_width() // 2, c.HEIGHT - 70))

    # --- Ввод имени и таблица рекордов ---
    def handle_name_entry_event(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
            self.new_score_rank = storage.add_score(self.pending_name, self.score)
            self.highscore = storage.load_highscore()
            self.state = STATE_SCORES
        elif e.key == pygame.K_BACKSPACE:
            self.pending_name = self.pending_name[:-1]
        else:
            ch = e.unicode
            if ch and ch.isprintable() and ch not in "\r\n\t" and len(self.pending_name) < 12:
                self.pending_name += ch

    def handle_scores_event(self, e):
        if (e.type == pygame.KEYDOWN and e.key in (
                pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_SPACE)
                ) or e.type == pygame.JOYBUTTONDOWN:
            self.back_to_menu()

    def draw_name_entry(self):
        self.screen.fill(c.BG_COLOR)
        cx = c.WIDTH // 2
        t = self.big.render("НОВЫЙ РЕКОРД!", True, c.BASE_COLOR)
        self.screen.blit(t, (cx - t.get_width() // 2, 120))
        sc = self.font.render(f"Очки: {self.score}", True, c.TEXT_COLOR)
        self.screen.blit(sc, (cx - sc.get_width() // 2, 200))
        lbl = self.small.render("Введите имя:", True, c.STEEL_COLOR)
        self.screen.blit(lbl, (cx - lbl.get_width() // 2, 252))

        box = pygame.Rect(cx - 140, 278, 280, 44)
        pygame.draw.rect(self.screen, (30, 34, 40), box, border_radius=4)
        pygame.draw.rect(self.screen, c.PLAYER_COLOR, box, 2, border_radius=4)
        cursor = "_" if (pygame.time.get_ticks() // 400) % 2 else " "
        name = self.font.render(self.pending_name + cursor, True, c.WHITE)
        self.screen.blit(name, (box.x + 12, box.centery - name.get_height() // 2))

        hint = self.small.render(
            "Enter — сохранить · Esc — без имени", True, (150, 150, 150))
        self.screen.blit(hint, (cx - hint.get_width() // 2, c.HEIGHT - 70))

    def draw_scores(self):
        self.screen.fill(c.BG_COLOR)
        cx = c.WIDTH // 2
        t = self.big.render("РЕКОРДЫ", True, c.PLAYER_COLOR)
        self.screen.blit(t, (cx - t.get_width() // 2, 40))

        scores = storage.load_scores()
        if not scores:
            empty = self.font.render("Пока пусто — сыграйте!", True, c.STEEL_COLOR)
            self.screen.blit(empty, (cx - empty.get_width() // 2, 220))
        else:
            y = 120
            for i, s in enumerate(scores):
                color = c.BASE_COLOR if i == self.new_score_rank else c.TEXT_COLOR
                self.screen.blit(self.font.render(f"{i + 1:2d}.", True, color), (cx - 200, y))
                self.screen.blit(self.font.render(s["name"], True, color), (cx - 150, y))
                num = self.font.render(str(s["score"]), True, color)
                self.screen.blit(num, (cx + 70 - num.get_width(), y))
                if s["date"]:
                    self.screen.blit(self.small.render(s["date"], True, (140, 140, 140)),
                                     (cx + 100, y + 4))
                y += 34

        hint = self.small.render("Enter/Esc — назад", True, (150, 150, 150))
        self.screen.blit(hint, (cx - hint.get_width() // 2, c.HEIGHT - 46))

    def draw_controls(self):
        dim = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
        dim.fill((10, 10, 14, 215))
        self.screen.blit(dim, (0, 0))
        cx = c.FIELD_W // 2

        title = self.font.render("УПРАВЛЕНИЕ", True, c.PLAYER_COLOR)
        self.screen.blit(title, (cx - title.get_width() // 2, 80))

        rows = [
            ("Движение", "Стрелки / W A S D"),
            ("Огонь", "Пробел"),
            ("Пауза", "P"),
            ("Рестарт", "R"),
            ("В меню", "Esc"),
        ]
        y = 150
        for action, key in rows:
            a = self.small.render(action, True, c.STEEL_COLOR)
            k = self.small.render(key, True, c.TEXT_COLOR)
            self.screen.blit(a, (cx - 120, y))
            self.screen.blit(k, (cx + 20, y))
            y += 34

        back = self.small.render("Esc или Enter — назад", True, (150, 150, 150))
        self.screen.blit(back, (cx - back.get_width() // 2, c.FIELD_H - 60))

    def draw_gameover(self):
        dim = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
        dim.fill((10, 10, 14, 210))
        self.screen.blit(dim, (0, 0))
        cx = c.FIELD_W // 2

        if self.result == "win":
            text, color = "ПОБЕДА!", c.PLAYER_COLOR
        else:
            text, color = "ПОРАЖЕНИЕ", c.ACCENT
        t = self.big.render(text, True, color)
        self.screen.blit(t, (cx - t.get_width() // 2, c.FIELD_H // 2 - 80))

        score = self.font.render(f"Очки: {self.score}", True, c.TEXT_COLOR)
        self.screen.blit(score, (cx - score.get_width() // 2, c.FIELD_H // 2 - 22))

        if self.new_record:
            nr = self.font.render("НОВЫЙ РЕКОРД!", True, c.BASE_COLOR)
        else:
            nr = self.small.render(f"Рекорд: {self.highscore}", True, c.STEEL_COLOR)
        self.screen.blit(nr, (cx - nr.get_width() // 2, c.FIELD_H // 2 + 8))

        for i, line in enumerate(["R — играть заново", "Esc — в меню"]):
            s = self.small.render(line, True, (170, 170, 170))
            self.screen.blit(s, (cx - s.get_width() // 2, c.FIELD_H // 2 + 40 + i * 24))

    def draw_levelclear(self):
        dim = pygame.Surface((c.FIELD_W, c.FIELD_H), pygame.SRCALPHA)
        dim.fill((10, 10, 14, 210))
        self.screen.blit(dim, (0, 0))
        cx = c.FIELD_W // 2

        t = self.big2.render("УРОВЕНЬ ПРОЙДЕН", True, c.PLAYER_COLOR)
        self.screen.blit(t, (cx - t.get_width() // 2, c.FIELD_H // 2 - 90))

        stage = self.font.render(
            f"{self.level_index + 1} / {levels.level_count()}", True, c.STEEL_COLOR)
        self.screen.blit(stage, (cx - stage.get_width() // 2, c.FIELD_H // 2 - 34))

        score = self.font.render(f"Очки: {self.score}", True, c.TEXT_COLOR)
        self.screen.blit(score, (cx - score.get_width() // 2, c.FIELD_H // 2 + 2))

        hint = self.small.render("Enter / Пробел — следующий уровень", True, (180, 180, 180))
        self.screen.blit(hint, (cx - hint.get_width() // 2, c.FIELD_H // 2 + 44))

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.quit()
                elif self.state == STATE_MENU:
                    self.handle_menu_event(e)
                elif self.state == STATE_PAUSED:
                    self.handle_pause_event(e)
                elif self.state == STATE_CONTROLS:
                    self.handle_controls_event(e)
                elif self.state == STATE_SETTINGS:
                    self.handle_settings_event(e)
                elif self.state == STATE_LEVELSTART:
                    self.handle_levelstart_event(e)
                elif self.state == STATE_NAME_ENTRY:
                    self.handle_name_entry_event(e)
                elif self.state == STATE_SCORES:
                    self.handle_scores_event(e)
                elif self.state == STATE_LEVELCLEAR:
                    self.handle_levelclear_event(e)
                elif self.state == STATE_GAMEOVER:
                    self.handle_gameover_event(e)
                else:
                    self.handle_game_event(e)

            # Заставка «Уровень N» сама сменяется боем по таймеру
            if (self.state == STATE_LEVELSTART
                    and pygame.time.get_ticks() >= self.level_start_until):
                self._begin_play()

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()
            self.clock.tick(c.FPS)

    def handle_menu_event(self, e):
        action = self.menu.handle_event(e)
        if action == "new_game":
            self.start_new_game()
        elif action == "load":
            self._load_game()
        elif action == "settings":
            self.open_settings()
        elif action == "scores":
            self.new_score_rank = -1
            self.state = STATE_SCORES
        elif action == "quit":
            self.quit()

    def handle_pause_event(self, e):
        # P или Esc — быстро снять паузу
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_p, pygame.K_ESCAPE):
            self.resume()
            return
        action = self.pause_menu.handle_event(e)
        if action == "resume":
            self.resume()
        elif action == "save":
            self._save_game()
            self._sync_menu_saves()      # активируем «Загрузить игру»
            self.resume()
        elif action == "load":
            if self._load_game():        # переводит в STATE_PLAYING
                pass
        elif action == "controls":
            self.state = STATE_CONTROLS
        elif action == "exit":
            self.back_to_menu()

    def handle_controls_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (
            pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE,
        ):
            self.state = STATE_PAUSED
        elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN):
            self.state = STATE_PAUSED

    def handle_levelclear_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.next_level()
            elif e.key == pygame.K_ESCAPE:
                self.back_to_menu()
        elif e.type == pygame.JOYBUTTONDOWN:
            self.next_level()

    def handle_gameover_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_r:
                self.start_new_game()
            elif e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.back_to_menu()
        elif e.type == pygame.JOYBUTTONDOWN:
            self.back_to_menu()
