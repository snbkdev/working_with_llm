"""Синтез звуковых эффектов на лету (без внешних аудиофайлов).

Звуки генерируются как 16-битный моно-сигнал и проигрываются через
pygame.mixer. Если аудиоустройство недоступно — звук тихо отключается.
"""

import array
import math
import random

import pygame

SAMPLE_RATE = 44100


def _tone(freq_start, freq_end, duration, volume=0.4, fade=0.01, noise=0.0):
    """Тон с плавным изменением частоты и опциональным «шумом»."""
    n = int(SAMPLE_RATE * duration)
    fade_n = max(1, int(SAMPLE_RATE * fade))
    amp = int(32767 * volume)
    out = array.array("h")
    phase = 0.0
    for i in range(n):
        f = freq_start + (freq_end - freq_start) * (i / n)
        phase += 2 * math.pi * f / SAMPLE_RATE
        s = math.sin(phase)
        if noise:
            s = s * (1 - noise) + (random.random() * 2 - 1) * noise
        if i < fade_n:
            env = i / fade_n
        elif i > n - fade_n:
            env = (n - i) / fade_n
        else:
            env = 1.0
        s = max(-1.0, min(1.0, s))
        out.append(int(s * amp * env))
    return pygame.mixer.Sound(buffer=out.tobytes())


def _engine_loop(volume=0.16):
    """Зацикленный «рокот мотора». Длительность — целое число периодов,
    чтобы петля стыковалась без щелчка."""
    base = 60.0
    cycles = 9
    duration = cycles / base            # ровно 9 периодов 60 Гц
    n = int(SAMPLE_RATE * duration)
    amp = int(32767 * volume)
    out = array.array("h")
    for i in range(n):
        t = i / SAMPLE_RATE
        saw = 2 * ((t * base) % 1.0) - 1          # пила 60 Гц
        s = 0.6 * saw + 0.3 * math.sin(2 * math.pi * 120 * t)
        s = max(-1.0, min(1.0, s))
        out.append(int(s * amp))
    return pygame.mixer.Sound(buffer=out.tobytes())


class Sounds:
    """Набор звуковых эффектов игры."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.shoot = self.hit = self.engine = self.pickup = None
        self.explosion = self.alarm = None
        self.engine_channel = None
        if not enabled:
            return
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            self.shoot = _tone(900, 300, 0.12, volume=0.35, noise=0.3)
            self.hit = _tone(1200, 500, 0.07, volume=0.30, noise=0.5)
            self.pickup = _tone(500, 1150, 0.20, volume=0.32)  # восходящий «динь»
            # Взрыв танка/базы: низкий раскатистый «бум» с сильным шумом
            self.explosion = _tone(320, 45, 0.34, volume=0.5, fade=0.02, noise=0.75)
            # Тревога «враг у базы»: короткий нисходящий сигнал
            self.alarm = _tone(1046, 740, 0.16, volume=0.28)
            self.engine = _engine_loop()
        except pygame.error:
            self.enabled = False

    def play_shoot(self):
        if self.enabled and self.shoot:
            self.shoot.play()

    def play_hit(self):
        if self.enabled and self.hit:
            self.hit.play()

    def play_pickup(self):
        if self.enabled and self.pickup:
            self.pickup.play()

    def play_explosion(self):
        if self.enabled and self.explosion:
            self.explosion.play()

    def play_alarm(self):
        if self.enabled and self.alarm:
            self.alarm.play()

    # --- Двигатель (зацикленный, пока танк едет) ---
    def engine_start(self):
        if not self.enabled or not self.engine:
            return
        if self.engine_channel is None or not self.engine_channel.get_busy():
            self.engine_channel = self.engine.play(loops=-1)

    def engine_stop(self):
        if self.engine_channel is not None:
            self.engine_channel.stop()
            self.engine_channel = None
