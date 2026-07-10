"""Процедурный звук Pac-Man: короткие сигналы синтезируются на лету (без файлов).

Волновые формы собираем стандартным `array` (16-бит знаковый PCM) и отдаём в
`pygame.mixer.Sound(buffer=...)`, подстраиваясь под формат микшера (моно/стерео).
Если аудио недоступно (headless-прогон, нет устройства) — модуль тихо становится
«заглушкой»: игра работает без звука и без исключений.

Особенность Pac-Man — «waka-waka»: при поедании точек чередуются два коротких
тона (`munch`), поэтому у съедания две волны.
"""

import array
import math
import random


class Synth:
    def __init__(self, rate=22050):
        self.ok = False
        self.enabled = True
        self.volume = 0.7
        self.rate = rate
        self.channels = 1
        self._cache = {}
        self._munch = 0          # чётность для чередования waka-тона
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

    # --- Построение волны --------------------------------------------------
    def _samples(self, dur, fn, vol=0.5):
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

        def sweep(f0, f1):
            return lambda t: math.sin(two_pi * (f0 + (f1 - f0) * t) * t)

        if name == "waka_a":          # верхний тон «wa»
            return self._make(sweep(520, 300), 0.06, 0.35)
        if name == "waka_b":          # нижний тон «ka»
            return self._make(sweep(300, 520), 0.06, 0.35)
        if name == "energizer":       # булькающий энергайзер
            return self._make(lambda t: math.sin(two_pi * (200 + 120 *
                              math.sin(two_pi * 10 * t)) * t), 0.22, 0.4)
        if name == "ready":           # короткая вступительная трель
            def jingle(t):
                seq = [523, 659, 784, 1047]
                return math.sin(two_pi * seq[min(3, int(t * 4))] * t)
            return self._make(jingle, 0.55, 0.45)
        if name == "level":           # зачистка уровня — восходящее трезвучие
            def up(t):
                f = 523 if t < 0.33 else (659 if t < 0.66 else 880)
                return math.sin(two_pi * f * t)
            return self._make(up, 0.5, 0.5)
        if name == "extra":           # экстра-жизнь
            return self._make(sweep(700, 1200), 0.2, 0.4)
        if name == "eatghost":        # съели призрака — восходящий «вжух»
            return self._make(sweep(300, 1000), 0.28, 0.45)
        if name == "death":           # гибель Пакмана — падение + шум
            return self._make(lambda t: math.sin(two_pi * (600 - 480 * t) * t)
                              * (1 - t) + random.uniform(-1, 1) * 0.15 * (1 - t),
                              0.7, 0.5)
        if name == "fright":          # включение испуга — тревожная нота
            return self._make(lambda t: math.sin(two_pi * (200 + 60 *
                              math.sin(two_pi * 6 * t)) * t), 0.25, 0.35)
        if name == "blip":            # перемещение по меню
            return self._make(lambda t: 1.0 if math.sin(90 * t) > 0 else -1.0, 0.04, 0.25)
        if name == "select":          # выбор пункта
            return self._make(sweep(400, 800), 0.1, 0.35)
        return self._make(lambda t: math.sin(two_pi * 440 * t), 0.1, 0.3)

    # --- Воспроизведение ---------------------------------------------------
    def play(self, name):
        if not self.ok or not self.enabled:
            return
        try:
            snd = self._cache.get(name)
            if snd is None:
                snd = self._cache[name] = self._build(name)
            snd.set_volume(self.volume)
            snd.play()
        except Exception:
            pass

    def munch(self):
        """Чередующийся waka-waka при поедании точек."""
        self._munch ^= 1
        self.play("waka_a" if self._munch else "waka_b")

    # --- Настройки ---------------------------------------------------------
    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, v))
        return self.volume
