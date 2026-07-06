"""Редактор карт Battle City — dev-инструмент.

Запуск (из каталога battle_city):
    python editor.py            # открыть первый уровень
    python editor.py 07.txt     # открыть конкретную карту

Управление:
    ЛКМ / зажать      — рисовать выбранным тайлом
    ПКМ               — стереть (сделать пусто)
    1–9               — выбрать тайл из палитры
    ← →               — предыдущая / следующая карта (с диска)
    S                 — сохранить текущую карту
    V                 — проверить карту (валидатор игры)
    N                 — новая пустая карта (рамка стали + база)
    G                 — сетка вкл/выкл
    Esc / Q           — выход

Превью рисуется движком игры (`world.level.Level`), поэтому кирпич, вода,
лёд и база выглядят ровно как в бою. Точки игрока (P) и врага (E) —
подписанные маркеры поверх поля.
"""

import sys
from pathlib import Path

import pygame

from src import config as c
from src.world import levels
from src.world.level import Level

PANEL_W = 210
WIN_W = c.FIELD_W + PANEL_W
WIN_H = c.FIELD_H

# Палитра: (символ, подпись, цвет-образец для панели)
PALETTE = [
    (".", "Пусто", (30, 30, 30)),
    ("B", "Кирпич", c.BRICK_COLOR),
    ("S", "Сталь", c.STEEL_COLOR),
    ("W", "Вода", c.WATER_COLOR),
    ("F", "Лес", c.FOREST_COLOR),
    ("I", "Лёд", c.ICE_COLOR),
    ("A", "База", c.BASE_COLOR),
    ("P", "Игрок", c.PLAYER_COLOR),
    ("E", "Враг", c.ENEMY_COLOR),
]
UNIQUE = {"A", "P"}          # этих тайлов на карте может быть не больше одного


def blank_map():
    """Пустая карта: рамка из стали, база снизу по центру, три точки врага."""
    grid = [["." for _ in range(c.COLS)] for _ in range(c.ROWS)]
    for i in range(c.COLS):
        grid[0][i] = grid[c.ROWS - 1][i] = "S"
    for i in range(c.ROWS):
        grid[i][0] = grid[i][c.COLS - 1] = "S"
    mid = c.COLS // 2
    grid[c.ROWS - 1][mid] = "A"
    grid[c.ROWS - 2][mid] = "P"
    for col in (1, mid, c.COLS - 2):
        grid[1][col] = "E"
    return ["".join(r) for r in grid]


class Editor:
    def __init__(self, start=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Battle City — редактор карт")
        self.font = pygame.font.SysFont("Helvetica", 15, bold=True)
        self.small = pygame.font.SysFont("Helvetica", 12)
        self.clock = pygame.time.Clock()

        self.files = sorted(levels.LEVELS_DIR.glob("*.txt"))
        self.file_index = 0
        if start:
            p = Path(start)
            if not p.is_absolute():
                p = levels.LEVELS_DIR / p.name
            if p in self.files:
                self.file_index = self.files.index(p)
        self.path = None
        self.grid = None
        self.selected = "B"
        self.show_grid = True
        self.status = ""
        self.status_color = c.TEXT_COLOR
        self._load_current()

    # --- Файлы ---
    def _load_current(self):
        if self.files:
            self.path = self.files[self.file_index]
            rows = self.path.read_text(encoding="utf-8").splitlines()
            rows = [r for r in rows if r.strip()]
            if len(rows) == c.ROWS and all(len(r) == c.COLS for r in rows):
                self.grid = [list(r) for r in rows]
                self._set_status(f"Открыто: {self.path.name}", c.PLAYER_COLOR)
                return
            self._set_status(f"{self.path.name}: битый формат — пустая карта", c.ACCENT)
        else:
            self.path = None
            self._set_status("Карт нет — новая пустая", c.BASE_COLOR)
        self.grid = [list(r) for r in blank_map()]

    def _switch_file(self, delta):
        if not self.files:
            return
        self.file_index = (self.file_index + delta) % len(self.files)
        self._load_current()

    def _save(self):
        if self.path is None:
            # нет исходного файла — придумываем следующее свободное имя NN.txt
            n = len(self.files) + 1
            self.path = levels.LEVELS_DIR / f"{n:02d}.txt"
        text = "\n".join("".join(r) for r in self.grid) + "\n"
        self.path.write_text(text, encoding="utf-8")
        if self.path not in self.files:
            self.files = sorted(levels.LEVELS_DIR.glob("*.txt"))
            self.file_index = self.files.index(self.path)
        self._set_status(f"Сохранено: {self.path.name}", c.PLAYER_COLOR)

    def _validate(self):
        try:
            levels.validate(["".join(r) for r in self.grid], "карта")
            self._set_status("Карта корректна ✓", c.PLAYER_COLOR)
        except ValueError as ex:
            self._set_status(str(ex), c.ACCENT)

    def _set_status(self, text, color=c.TEXT_COLOR):
        self.status = text
        self.status_color = color

    # --- Рисование по клеткам ---
    def _paint(self, mx, my, char):
        if mx >= c.FIELD_W or my >= c.FIELD_H:
            return
        col, row = mx // c.TILE, my // c.TILE
        if not (0 <= col < c.COLS and 0 <= row < c.ROWS):
            return
        if char in UNIQUE:                 # база/игрок — единственные, старый убираем
            for r in range(c.ROWS):
                for cc in range(c.COLS):
                    if self.grid[r][cc] == char:
                        self.grid[r][cc] = "."
        self.grid[row][col] = char

    # --- Цикл ---
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                self._handle(e)
            self._paint_held()
            self.draw()
            self.clock.tick(60)

    def _handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                pygame.quit()
                sys.exit()
            elif pygame.K_1 <= e.key <= pygame.K_9:
                idx = e.key - pygame.K_1
                if idx < len(PALETTE):
                    self.selected = PALETTE[idx][0]
            elif e.key == pygame.K_LEFT:
                self._switch_file(-1)
            elif e.key == pygame.K_RIGHT:
                self._switch_file(1)
            elif e.key == pygame.K_s:
                self._save()
            elif e.key == pygame.K_v:
                self._validate()
            elif e.key == pygame.K_n:
                self.path = None
                self.grid = [list(r) for r in blank_map()]
                self._set_status("Новая пустая карта", c.BASE_COLOR)
            elif e.key == pygame.K_g:
                self.show_grid = not self.show_grid
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                self._paint(*e.pos, self.selected)
            elif e.button == 3:
                self._paint(*e.pos, ".")

    def _paint_held(self):
        """Рисование при зажатой кнопке (перетаскивание)."""
        buttons = pygame.mouse.get_pressed()
        if buttons[0] or buttons[2]:
            mx, my = pygame.mouse.get_pos()
            self._paint(mx, my, self.selected if buttons[0] else ".")

    # --- Отрисовка ---
    def draw(self):
        self.screen.fill(c.BG_COLOR)
        rows = ["".join(r) for r in self.grid]
        level = Level(rows)
        level.base_alive = any("A" in r for r in rows)   # база только если есть 'A'
        pygame.draw.rect(self.screen, c.FIELD_COLOR, (0, 0, c.FIELD_W, c.FIELD_H))
        level.draw(self.screen)
        level.draw_forest(self.screen)
        self._draw_markers()
        if self.show_grid:
            self._draw_grid()
        pygame.draw.rect(self.screen, c.FIELD_BORDER, (0, 0, c.FIELD_W, c.FIELD_H), 2)
        self._draw_panel()
        pygame.display.flip()

    def _draw_markers(self):
        """Подписанные маркеры точек игрока (P) и врагов (E)."""
        for row in range(c.ROWS):
            for col in range(c.COLS):
                ch = self.grid[row][col]
                if ch not in ("P", "E"):
                    continue
                cx = col * c.TILE + c.TILE // 2
                cy = row * c.TILE + c.TILE // 2
                color = c.PLAYER_COLOR if ch == "P" else c.ENEMY_COLOR
                pygame.draw.circle(self.screen, color, (cx, cy), 12, 2)
                lbl = self.font.render(ch, True, color)
                self.screen.blit(lbl, (cx - lbl.get_width() // 2,
                                       cy - lbl.get_height() // 2))

    def _draw_grid(self):
        for x in range(0, c.FIELD_W + 1, c.TILE):
            pygame.draw.line(self.screen, (40, 40, 40), (x, 0), (x, c.FIELD_H))
        for y in range(0, c.FIELD_H + 1, c.TILE):
            pygame.draw.line(self.screen, (40, 40, 40), (0, y), (c.FIELD_W, y))
        # Подсветка клетки под курсором
        mx, my = pygame.mouse.get_pos()
        if mx < c.FIELD_W and my < c.FIELD_H:
            col, row = mx // c.TILE, my // c.TILE
            pygame.draw.rect(self.screen, c.WHITE,
                             (col * c.TILE, row * c.TILE, c.TILE, c.TILE), 2)

    def _draw_panel(self):
        x = c.FIELD_W
        pygame.draw.rect(self.screen, c.HUD_BG, (x, 0, PANEL_W, WIN_H))
        title = self.font.render("РЕДАКТОР", True, c.HUD_TEXT)
        self.screen.blit(title, (x + 14, 14))

        y = 46
        self.screen.blit(self.small.render("ТАЙЛЫ (1–9):", True, c.HUD_TEXT), (x + 14, y))
        y += 20
        for i, (ch, name, color) in enumerate(PALETTE):
            sel = ch == self.selected
            box = pygame.Rect(x + 14, y, 20, 20)
            pygame.draw.rect(self.screen, color, box, border_radius=3)
            pygame.draw.rect(self.screen, c.WHITE if sel else (60, 60, 60),
                             box, 2, border_radius=3)
            txt = self.small.render(f"{i + 1}  {name}", True,
                                    (20, 20, 20) if sel else c.HUD_TEXT)
            self.screen.blit(txt, (x + 42, y + 3))
            y += 26

        y += 6
        pygame.draw.line(self.screen, (70, 70, 70), (x + 12, y), (x + PANEL_W - 12, y))
        y += 10
        hints = [
            "ЛКМ — рисовать",
            "ПКМ — стереть",
            "← → — карта",
            "S — сохранить",
            "V — проверить",
            "N — новая",
            "G — сетка",
            "Esc — выход",
        ]
        for line in hints:
            self.screen.blit(self.small.render(line, True, c.HUD_TEXT), (x + 14, y))
            y += 18

        # Текущий файл + счётчик тайлов
        name = self.path.name if self.path else "(новая)"
        cnt = "".join("".join(r) for r in self.grid)
        info = f"{name}  A:{cnt.count('A')} P:{cnt.count('P')} E:{cnt.count('E')}"
        self.screen.blit(self.small.render(info, True, c.HUD_TEXT),
                         (x + 14, WIN_H - 46))

        # Статус (валидация/сохранение) с переносом
        self._blit_wrapped(self.status, x + 14, WIN_H - 28, PANEL_W - 24,
                           self.status_color)

    def _blit_wrapped(self, text, x, y, width, color):
        words = text.split(" ")
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if self.small.size(test)[0] > width and line:
                self.screen.blit(self.small.render(line, True, color), (x, y))
                y += 15
                line = w
            else:
                line = test
        if line:
            self.screen.blit(self.small.render(line, True, color), (x, y))


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else None
    Editor(start).run()


if __name__ == "__main__":
    main()
