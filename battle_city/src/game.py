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
STATE_LEVELCLEAR = "levelclear"
STATE_GAMEOVER = "gameover"

MAIN_MENU_ITEMS = [
    ("Новая игра", "new_game", True),
    ("Загрузка", "load", False),
    ("Настройки", "settings", False),
    ("Выход", "quit", True),
]
PAUSE_MENU_ITEMS = [
    ("Продолжить", "resume", True),
    ("Сохранить/Загрузить", "saveload", False),
    ("Управление", "controls", True),
    ("Выйти", "exit", True),
]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
        pygame.display.set_caption("Battle City")
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

    def reset(self):
        """Новая игра с первого уровня: сбрасываются очки и жизни."""
        self.lives = c.PLAYER_LIVES
        self.score = 0
        self.new_record = False
        self.load_level(0)

    def load_level(self, index):
        """Загружает уровень index и сбрасывает поле.

        Очки и жизни сохраняются между уровнями (их обнуляет только reset).
        """
        self.level_index = index
        self.level = Level(levels.load_level(index))
        col, row = self.level.player_spawn
        self.player = Tank(col, row, c.UP, is_player=True)
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

        # Враги: случайное число за уровень (10–15)
        self.enemies = []
        self.enemies_to_spawn = random.randint(
            c.ENEMY_COUNT_MIN, c.ENEMY_COUNT_MAX
        )
        self.spawn_index = 0
        # Пауза перед первым врагом (~6 сек после старта)
        self.next_spawn_at = pygame.time.get_ticks() + c.ENEMY_START_DELAY

    # --- Переходы состояний ---
    def start_new_game(self):
        self.reset()
        self.state = STATE_PLAYING

    def back_to_menu(self):
        self.sounds.engine_stop()
        self.state = STATE_MENU

    def pause(self):
        self.sounds.engine_stop()
        self.pause_menu.index = 0
        self.state = STATE_PAUSED

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
            if (col, row) in self.level.bricks or (col, row) in self.level.steels:
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
                    self.score += c.ENEMY_TOUGH_SCORE if e.tough else c.ENEMY_SCORE
                    killed = True
            if killed:
                self.sounds.play_explosion()
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
        # Новый рекорд? Сохраняем на диск
        if self.score > self.highscore:
            self.highscore = self.score
            self.new_record = True
            storage.save_highscore(self.highscore)
        self.sounds.engine_stop()
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
        self.load_level(self.level_index + 1)
        self.state = STATE_PLAYING

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
    def try_spawn_enemy(self, now):
        if self.enemies_to_spawn <= 0:
            return
        if len(self.enemies) >= c.MAX_ACTIVE_ENEMIES:
            return
        if now < self.next_spawn_at:
            return

        spawns = self.level.enemy_spawns           # лево / центр / право
        occupied = [t.rect for t in self.enemies] + [self.player.rect]

        # Берём первую свободную точку, перебирая по кругу от текущего индекса
        n = len(spawns)
        tough = self.level_index + 1 >= c.TOUGH_ENEMY_FROM_LEVEL  # после 10 уровня
        for k in range(n):
            cell = spawns[(self.spawn_index + k) % n]
            bonus = random.random() < c.BONUS_ENEMY_CHANCE
            enemy = Enemy(*cell, bonus=bonus, tough=tough)
            if not any(enemy.rect.colliderect(o) for o in occupied):
                self.enemies.append(enemy)
                self.enemies_to_spawn -= 1
                self.spawn_index = (self.spawn_index + k + 1) % n
                self.next_spawn_at = now + c.ENEMY_SPAWN_INTERVAL
                return
        # Все точки заняты — попробуем в следующий раз

    # --- Ввод ---
    def handle_game_event(self, e):
        """Дискретные клавиши в режиме игры (стрельба, пауза, рестарт)."""
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p:
                self.pause()
            elif e.key == pygame.K_ESCAPE:
                self.back_to_menu()
            elif e.key == pygame.K_r:
                self.reset()
            elif e.key == pygame.K_SPACE:
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
        return None

    # --- Логика ---
    def update(self):
        now = pygame.time.get_ticks()
        self.try_spawn_enemy(now)

        keys = pygame.key.get_pressed()
        direction = self.read_direction(keys)
        solids = self.level.solid_rects()

        # Игрок (враги — препятствия)
        enemy_rects = [e.rect for e in self.enemies]
        moved = False
        if direction is not None:
            self.player.face(direction)
            moved = self.player.try_move(solids, enemy_rects)

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

        # Уровень зачищен: все враги уничтожены и больше не появятся
        if self.enemies_to_spawn == 0 and not self.enemies:
            self.level_cleared()

    def _bullet_vs_tanks(self, b, now):
        if b.owner == "player":
            for e in self.enemies:
                if e.alive and b.rect.colliderect(e.rect):
                    b.alive = False
                    e.hp -= 1
                    if e.hp > 0:
                        # тяжёлый враг выдержал попадание — только «тик» и вспышка
                        self.spawn_explosion(e.rect.center, big=False)
                        self.sounds.play_hit()
                        return
                    e.alive = False
                    self.score += c.ENEMY_TOUGH_SCORE if e.tough else c.ENEMY_SCORE
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
                    self.player_hit()
                else:
                    self.sounds.play_hit()      # щит поглотил пулю — лёгкий «тик»

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

        self._draw_scene()
        if self.state == STATE_PAUSED:
            self.pause_menu.draw(self.screen)
        elif self.state == STATE_CONTROLS:
            self.draw_controls()
        elif self.state == STATE_LEVELCLEAR:
            self.draw_levelclear()
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover()
        pygame.display.flip()

    def _draw_scene(self):
        self.screen.fill(c.BG_COLOR)
        pygame.draw.rect(self.screen, c.FIELD_COLOR, (0, 0, c.FIELD_W, c.FIELD_H))
        self.draw_grid()
        self.level.draw(self.screen)
        now = pygame.time.get_ticks()
        for p in self.powerups:
            p.draw(self.screen)
        self.player.draw(self.screen)
        if now < self.player_invuln_until:          # щит: респаун или каска
            self._draw_shield(self.player.rect, now)
        frozen = self.freeze_until is not None and now < self.freeze_until
        for e in self.enemies:
            e.draw(self.screen)
            if e.tough:                              # тяжёлый враг — стальная окантовка
                pygame.draw.rect(self.screen, c.STEEL_COLOR, e.rect, 2, border_radius=5)
                if e.hp <= 1:                        # пробит один раз — «трещина»
                    pygame.draw.line(self.screen, c.ACCENT,
                                     e.rect.topleft, e.rect.bottomright, 2)
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
        pygame.draw.rect(self.screen, c.FIELD_BORDER, (0, 0, c.FIELD_W, c.FIELD_H), 2)
        self.draw_hud()

    def _draw_shield(self, rect, now):
        """Пульсирующее кольцо-щит вокруг танка (неуязвимость)."""
        radius = rect.width // 2 + 4 + (now // 80) % 3
        pygame.draw.circle(self.screen, c.SHIELD_COLOR, rect.center, radius, 2)

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
        remaining = self.enemies_to_spawn + len(self.enemies)
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
                elif self.state == STATE_LEVELCLEAR:
                    self.handle_levelclear_event(e)
                elif self.state == STATE_GAMEOVER:
                    self.handle_gameover_event(e)
                else:
                    self.handle_game_event(e)

            if self.state == STATE_PLAYING:
                self.update()
            self.draw()
            self.clock.tick(c.FPS)

    def handle_menu_event(self, e):
        action = self.menu.handle_event(e)
        if action == "new_game":
            self.start_new_game()
        elif action == "quit":
            self.quit()
        # «load» и «settings» пока без действия

    def handle_pause_event(self, e):
        # P или Esc — быстро снять паузу
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_p, pygame.K_ESCAPE):
            self.resume()
            return
        action = self.pause_menu.handle_event(e)
        if action == "resume":
            self.resume()
        elif action == "controls":
            self.state = STATE_CONTROLS
        elif action == "exit":
            self.back_to_menu()
        # «saveload» пока без действия

    def handle_controls_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (
            pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE,
        ):
            self.state = STATE_PAUSED
        elif e.type == pygame.MOUSEBUTTONDOWN:
            self.state = STATE_PAUSED

    def handle_levelclear_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.next_level()
            elif e.key == pygame.K_ESCAPE:
                self.back_to_menu()

    def handle_gameover_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_r:
                self.start_new_game()
            elif e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.back_to_menu()
