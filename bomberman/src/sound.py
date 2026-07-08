"""Процедурный звук: короткие сигналы синтезируются на лету (без файлов).

Волновые формы собираем стандартным `array` (16-бит знаковый PCM) и отдаём в
`pygame.mixer.Sound(buffer=...)`, подстраиваясь под реальный формат микшера
(моно/стерео). Если аудио недоступно (например, headless-прогон), весь модуль
тихо превращается в «заглушку» — игра работает без звука и без исключений.
"""

import array
import math
import random


class Synth:
    def __init__(self, rate=22050):
        self.ok = False
        self.enabled = True
        self.rate = rate
        self.channels = 1
        self._cache = {}
        try:
            import pygame
            pygame.mixer.quit()
            pygame.mixer.init(frequency=rate, size=-16, channels=1, buffer=512)
            got = pygame.mixer.get_init()
            if got:
                self.rate, _, self.channels = got
                pygame.mixer.set_num_channels(16)
                self.ok = True
        except Exception:
            self.ok = False

    # --- Построение волны ---
    def _samples(self, dur, fn, vol=0.5):
        """fn(t01) → значение [-1..1]; собираем PCM с мягкой атакой/спадом."""
        n = max(1, int(self.rate * dur))
        buf = array.array("h")
        atk = max(1, int(n * 0.02))
        for i in range(n):
            t = i / n
            env = (i / atk) if i < atk else max(0.0, 1.0 - (i - atk) / (n - atk))
            s = fn(t) * env * vol
            v = int(max(-1.0, min(1.0, s)) * 32767)
            buf.append(v)
            if self.channels == 2:
                buf.append(v)
        return buf

    def _make(self, fn, dur, vol):
        import pygame
        return pygame.mixer.Sound(buffer=self._samples(dur, fn, vol).tobytes())

    def _build(self, name):
        two_pi = 2 * math.pi

        def tone(freq, drop=0.0):
            return lambda t: math.sin(two_pi * freq * (1 - drop * t) * t * 1.0)

        def sweep(f0, f1):
            return lambda t: math.sin(two_pi * (f0 + (f1 - f0) * t) * t)

        def noise():
            return lambda t: random.uniform(-1, 1)

        if name == "bomb":            # глухой «плюх» установки
            return self._make(sweep(320, 120), 0.09, 0.45)
        if name == "boom":            # взрыв — шумовой всплеск
            return self._make(lambda t: random.uniform(-1, 1) * (1 - t), 0.34, 0.6)
        if name == "pickup":          # восходящий бонусный «блип»
            return self._make(sweep(600, 1050), 0.14, 0.4)
        if name == "curse":           # нисходящий зловещий
            return self._make(sweep(700, 180), 0.3, 0.4)
        if name == "death":           # падение + шум
            return self._make(lambda t: math.sin(two_pi * (500 - 380 * t) * t)
                              * (1 - t) + random.uniform(-1, 1) * 0.2 * (1 - t),
                              0.35, 0.5)
        if name == "round":           # две ноты «приготовься»
            return self._make(lambda t: math.sin(two_pi * (440 if t < 0.5 else 660) * t),
                              0.3, 0.45)
        if name == "win":             # восходящее трезвучие
            def jingle(t):
                f = 523 if t < 0.33 else (659 if t < 0.66 else 784)
                return math.sin(two_pi * f * t)
            return self._make(jingle, 0.5, 0.5)
        if name == "blip":            # клик в меню
            return self._make(lambda t: 1.0 if math.sin(80 * t) > 0 else -1.0, 0.04, 0.25)
        if name == "siren":           # тревога начала sudden death
            return self._make(lambda t: math.sin(two_pi * (300 + 200 *
                              (0.5 + 0.5 * math.sin(two_pi * 4 * t))) * t), 0.6, 0.45)
        if name == "throw":           # свист брошенной бомбы
            return self._make(lambda t: math.sin(two_pi * (900 - 500 * t) * t)
                              * (1 - t), 0.16, 0.35)
        if name == "jump":            # пружинистый «бойнг»
            return self._make(sweep(300, 720), 0.18, 0.35)
        if name == "teleport":        # переливчатый варп
            return self._make(lambda t: math.sin(two_pi * (500 + 400 *
                              math.sin(two_pi * 9 * t)) * t) * (1 - t), 0.24, 0.4)
        if name == "drop":            # глухой удар упавшей стены
            return self._make(lambda t: (math.sin(two_pi * 90 * t)
                              + random.uniform(-1, 1) * 0.3) * (1 - t), 0.09, 0.4)
        return self._make(tone(440), 0.1, 0.3)

    def play(self, name):
        if not self.ok or not self.enabled:
            return
        try:
            snd = self._cache.get(name)
            if snd is None:
                snd = self._cache[name] = self._build(name)
            snd.play()
        except Exception:
            pass

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
