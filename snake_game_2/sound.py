"""Синтез звуковых эффектов на лету (без внешних аудиофайлов).

Тоны генерируются как 16-битный моно-сигнал и проигрываются через
pygame.mixer. Если аудиоустройство недоступно — звук тихо отключается.
"""

import array
import math

import pygame

SAMPLE_RATE = 44100


def _sound(freq_start, freq_end, duration, volume=0.4, fade=0.008):
    """Создаёт Sound с плавным изменением частоты от freq_start к freq_end."""
    n = int(SAMPLE_RATE * duration)
    fade_n = max(1, int(SAMPLE_RATE * fade))
    amp = int(32767 * volume)
    samples = array.array("h")
    phase = 0.0
    for i in range(n):
        freq = freq_start + (freq_end - freq_start) * (i / n)
        phase += 2 * math.pi * freq / SAMPLE_RATE
        # Огибающая: плавное нарастание и затухание, чтобы не было щелчков
        if i < fade_n:
            env = i / fade_n
        elif i > n - fade_n:
            env = (n - i) / fade_n
        else:
            env = 1.0
        samples.append(int(amp * env * math.sin(phase)))
    return pygame.mixer.Sound(buffer=samples.tobytes())


class Sounds:
    """Набор звуковых эффектов игры."""

    def __init__(self, enabled=True):
        # Микшер и тоны готовим всегда, `enabled` лишь глушит воспроизведение
        # — так звук можно включать/выключать кнопкой прямо в игре
        self.enabled = enabled
        self.eat = None
        self.crash = None
        self.bonus = None
        self.rotten = None
        self.squeak = None
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            # Короткий восходящий «бип» — поедание
            self.eat = _sound(660, 990, 0.09, volume=0.35)
            # Низкий нисходящий «бззз» — проигрыш
            self.crash = _sound(320, 110, 0.35, volume=0.45)
            # Яркая «трель» вверх — бонус
            self.bonus = _sound(700, 1500, 0.18, volume=0.4)
            # Кислый низкий «блюп» — гнилое яблоко
            self.rotten = _sound(240, 90, 0.28, volume=0.4)
            # Высокий писк — пойманная мышка
            self.squeak = _sound(1400, 1900, 0.1, volume=0.3)
        except pygame.error:
            pass  # аудиоустройство недоступно — тоны остались None

    def _play(self, sound):
        if self.enabled and sound is not None:
            sound.play()

    def play_eat(self):
        self._play(self.eat)

    def play_crash(self):
        self._play(self.crash)

    def play_bonus(self):
        self._play(self.bonus)

    def play_rotten(self):
        self._play(self.rotten)

    def play_squeak(self):
        self._play(self.squeak)
