"""Редактор схем карт Bomberman — dev-инструмент.

Запуск (из каталога bomberman):
    python editor.py            # новая карта или первая сохранённая
    python editor.py mymap      # открыть карту maps/mymap.json

Управление:
    ЛКМ / зажать   — рисовать выбранной кистью
    ПКМ            — стереть (сделать полом)
    1–7            — выбрать кисть из палитры
    R              — повернуть направление конвейера
    [ / ]          — предыдущая / следующая сохранённая карта
    N              — новая пустая карта
    S              — сохранить (в текущий файл или maps/mapN.json)
    V              — проверить карту (рамка/спавны/связность)
    G              — сетка вкл/выкл
    Esc / Q        — выход

Превью рисуется движком игры (`world.arena.Arena`), поэтому пол, стены, ящики и
спец-тайлы выглядят ровно как в бою. Точки спавна — подписанные маркеры поверх.
"""

import sys

import pygame

from src import config as c
from src import storage
from src.world.arena import Arena, is_border

PANEL_X = c.FIELD_W
PANEL_W = c.HUD_W

# Кисти палитры: (тайл/спец, подпись, цвет-образец)
B_FLOOR, B_WALL, B_BLOCK, B_SPAWN, B_TP, B_CONV, B_TRAMP = range(7)
PALETTE = [
    (B_FLOOR, "Пол (стереть)", c.FLOOR_A),
    (B_WALL, "Стена", c.WALL_COLOR),
    (B_BLOCK, "Ящик", c.BLOCK_COLOR),
    (B_SPAWN, "Спавн", c.PLAYER_COLORS[0]),
    (B_TP, "Телепорт", c.SPEC_COLORS[c.SPEC_TELEPORT]),
    (B_CONV, "Конвейер", c.SPEC_COLORS[c.SPEC_CONVEYOR]),
    (B_TRAMP, "Батут", c.SPEC_COLORS[c.SPEC_TRAMPOLINE]),
]
_CONV_DIRS = [c.RIGHT, c.DOWN, c.LEFT, c.UP]


class Editor:
    def __init__(self, start=None):
        pygame.init()
        self.screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
        pygame.display.set_caption("Bomberman — редактор карт")
        self.font = pygame.font.SysFont("Helvetica", 15, bold=True)
        self.small = pygame.font.SysFont("Helvetica", 12)
        self.tiny = pygame.font.SysFont("Helvetica", 11, bold=True)
        self.clock = pygame.time.Clock()
        self.arena = Arena(seed=0)          # только для отрисовки превью

        self.files = storage.list_maps()
        self.file_index = 0
        self.name = None
        self.brush = B_WALL
        self.conv_i = 0                     # индекс направления конвейера
        self.show_grid = True
        self.status = "N — новая, S — сохранить, V — проверить"

        if start:
            data = storage.load_map(start)
            self._set_map(data or storage.blank_map(), name=str(start))
        elif self.files:
            self._load_index(0)
        else:
            self._set_map(storage.blank_map(), name=None)

    # --- Модель карты ---
    def _set_map(self, data, name):
        self.grid = [list(row) for row in data["grid"]]
        self.specials = {
            tuple(int(v) for v in k.split(",")):
                (kind, tuple(d) if d else None)
            for k, (kind, d) in data.get("specials", {}).items()
        }
        self.spawns = [tuple(s) for s in data.get("spawns", [])]
        self.name = name

    def to_data(self):
        return {
            "cols": c.COLS, "rows": c.ROWS,
            "grid": [list(row) for row in self.grid],
            "specials": {f"{col},{row}": [kind, list(d) if d else None]
                         for (col, row), (kind, d) in self.specials.items()},
            "spawns": [list(s) for s in self.spawns],
        }

    def _load_index(self, i):
        if not self.files:
            return
        self.file_index = i % len(self.files)
        path = self.files[self.file_index]
        data = storage.load_map(path)
        if data:
            self._set_map(data, name=path.stem)
            self.status = f"Открыта {path.name}"
        else:
            self.status = f"Битый файл {path.name}"

    # --- Правка клеток ---
    def paint(self, cell, erase=False):
        col, row = cell
        if not self.arena.in_bounds(col, row) or is_border(col, row):
            return                          # рамку не трогаем
        brush = B_FLOOR if erase else self.brush
        self.specials.pop(cell, None)       # любая кисть сначала очищает спец-тайл
        if cell in self.spawns and brush != B_SPAWN:
            self.spawns.remove(cell)
        if brush == B_FLOOR:
            self.grid[row][col] = c.FLOOR
        elif brush == B_WALL:
            self.grid[row][col] = c.WALL
        elif brush == B_BLOCK:
            self.grid[row][col] = c.BLOCK
        elif brush == B_SPAWN:
            self.grid[row][col] = c.FLOOR
            if cell not in self.spawns:
                self.spawns.append(cell)
                while len(self.spawns) > c.MAX_FIGHTERS:
                    self.spawns.pop(0)
        else:                               # спец-тайлы — всегда на полу
            self.grid[row][col] = c.FLOOR
            if brush == B_TP:
                self.specials[cell] = (c.SPEC_TELEPORT, None)
            elif brush == B_CONV:
                self.specials[cell] = (c.SPEC_CONVEYOR, _CONV_DIRS[self.conv_i])
            elif brush == B_TRAMP:
                self.specials[cell] = (c.SPEC_TRAMPOLINE, None)

    def erase(self, cell):
        self.paint(cell, erase=True)

    # --- Проверка карты ---
    def validate(self):
        problems = []
        for col in range(c.COLS):
            if self.grid[0][col] != c.WALL or self.grid[c.ROWS - 1][col] != c.WALL:
                problems.append("рамка не сплошная")
                break
        if len(self.spawns) < 2:
            problems.append("нужно ≥2 спавнов")
        if len(self.teleports()) % 2 != 0:
            problems.append("телепорты — только парами")
        if self.spawns and not self._spawns_connected():
            problems.append("спавны не связаны")
        self.status = "Карта корректна ✓" if not problems else "; ".join(problems)
        return not problems

    def teleports(self):
        return [cell for cell, (k, _d) in self.specials.items() if k == c.SPEC_TELEPORT]

    def _spawns_connected(self):
        start = self.spawns[0]
        seen, stack = {start}, [start]
        while stack:
            col, row = stack.pop()
            for dc, dr in (c.UP, c.DOWN, c.LEFT, c.RIGHT):
                nc, nr = col + dc, row + dr
                if (nc, nr) not in seen and self.arena.in_bounds(nc, nr) \
                        and self.grid[nr][nc] != c.WALL:
                    seen.add((nc, nr))
                    stack.append((nc, nr))
        return all(sp in seen for sp in self.spawns)

    # --- Файлы ---
    def save(self):
        if not self.name:
            n = 1
            while storage.map_path(f"map{n}").exists():
                n += 1
            self.name = f"map{n}"
        storage.save_map(self.to_data(), self.name)
        self.files = storage.list_maps()
        self.status = f"Сохранено: {self.name}.json"

    def new_map(self):
        self._set_map(storage.blank_map(), name=None)
        self.status = "Новая карта"

    # --- Ввод ---
    def handle(self, e):
        if e.type == pygame.QUIT:
            return False
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
            elif pygame.K_1 <= e.key <= pygame.K_7:
                self.brush = e.key - pygame.K_1
            elif e.key == pygame.K_r:
                self.conv_i = (self.conv_i + 1) % len(_CONV_DIRS)
                self.status = "Направление конвейера повёрнуто"
            elif e.key == pygame.K_g:
                self.show_grid = not self.show_grid
            elif e.key == pygame.K_n:
                self.new_map()
            elif e.key == pygame.K_s:
                self.save()
            elif e.key == pygame.K_v:
                self.validate()
            elif e.key == pygame.K_LEFTBRACKET:
                self._load_index(self.file_index - 1)
            elif e.key == pygame.K_RIGHTBRACKET:
                self._load_index(self.file_index + 1)
        elif e.type == pygame.MOUSEBUTTONDOWN:
            self._paint_at_mouse(e.pos, e.button)
        elif e.type == pygame.MOUSEMOTION and e.buttons != (0, 0, 0):
            self._paint_at_mouse(e.pos, 1 if e.buttons[0] else 3)
        return True

    def _paint_at_mouse(self, pos, button):
        x, y = pos
        if x >= c.FIELD_W:
            self._click_palette(y)
            return
        cell = (x // c.TILE, y // c.TILE)
        if button == 3:
            self.erase(cell)
        else:
            self.paint(cell)

    def _click_palette(self, y):
        idx = (y - 40) // 30
        if 0 <= idx < len(PALETTE):
            self.brush = PALETTE[idx][0]

    # --- Отрисовка ---
    def draw(self):
        self.arena.grid = self.grid
        self.arena.specials = self.specials
        self.arena.draw(self.screen)
        if self.show_grid:
            for col in range(c.COLS + 1):
                pygame.draw.line(self.screen, (0, 0, 0, 40),
                                 (col * c.TILE, 0), (col * c.TILE, c.FIELD_H), 1)
            for row in range(c.ROWS + 1):
                pygame.draw.line(self.screen, (0, 0, 0, 40),
                                 (0, row * c.TILE), (c.FIELD_W, row * c.TILE), 1)
        for i, (col, row) in enumerate(self.spawns):   # маркеры спавна
            cx, cy = col * c.TILE + c.TILE // 2, row * c.TILE + c.TILE // 2
            pygame.draw.circle(self.screen, c.PLAYER_COLORS[i % 4], (cx, cy), 11)
            pygame.draw.circle(self.screen, (20, 20, 24), (cx, cy), 11, 2)
            lbl = self.tiny.render(f"P{i + 1}", True, (20, 20, 24))
            self.screen.blit(lbl, (cx - lbl.get_width() // 2, cy - 6))
        self._draw_panel()
        pygame.display.flip()

    def _draw_panel(self):
        pygame.draw.rect(self.screen, c.HUD_BG, (PANEL_X, 0, PANEL_W, c.HEIGHT))
        self.screen.blit(self.font.render("Редактор", True, c.ACCENT), (PANEL_X + 12, 10))
        y = 40
        for kind, label, sample in PALETTE:
            sel = kind == self.brush
            box = pygame.Rect(PANEL_X + 8, y, PANEL_W - 16, 26)
            pygame.draw.rect(self.screen, (46, 50, 64) if sel else (30, 32, 40),
                             box, border_radius=5)
            if sel:
                pygame.draw.rect(self.screen, c.ACCENT, box, 2, border_radius=5)
            pygame.draw.rect(self.screen, sample, (box.x + 6, box.y + 6, 14, 14),
                             border_radius=3)
            self.screen.blit(self.tiny.render(label, True, c.HUD_TEXT),
                             (box.x + 26, box.y + 7))
            y += 30
        dname = {(1, 0): "→", (0, 1): "↓", (-1, 0): "←", (0, -1): "↑"}[_CONV_DIRS[self.conv_i]]
        lines = [
            f"конвейер: {dname} (R)",
            f"файл: {self.name or 'новый'}",
            "ЛКМ рисует, ПКМ стереть",
            "1-7 кисть  [ ] карты",
            "N нов  S сохр  V пров",
        ]
        y += 6
        for ln in lines:
            self.screen.blit(self.tiny.render(ln, True, (180, 184, 196)), (PANEL_X + 12, y))
            y += 18
        st = self.small.render(self.status, True, c.WHITE)
        self.screen.blit(st, (PANEL_X + 12, c.HEIGHT - 26))

    def run(self):
        running = True
        while running:
            for e in pygame.event.get():
                if not self.handle(e):
                    running = False
            self.draw()
            self.clock.tick(c.FPS)
        pygame.quit()


if __name__ == "__main__":
    Editor(sys.argv[1] if len(sys.argv) > 1 else None).run()
