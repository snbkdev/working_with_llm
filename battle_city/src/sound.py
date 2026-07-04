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


def _music_loop(volume=0.11):
    """Зацикленный бас-арпеджио (A-moll), квадратная волна + октава-мелодия.

    Каждая нота с огибающей затухает к концу, поэтому стык петли — почти тишина
    (зацикливается без щелчка). Длина — целое число нот.
    """
    seq = [220.00, 261.63, 329.63, 261.63,   # Am
           196.00, 246.94, 293.66, 246.94,   # G
           174.61, 220.00, 261.63, 220.00,   # F
           196.00, 246.94, 293.66, 246.94]   # G
    note_dur = 0.22
    n_note = int(SAMPLE_RATE * note_dur)
    amp = int(32767 * volume)
    out = array.array("h")
    for f in seq:
        for i in range(n_note):
            t = i / SAMPLE_RATE
            square = 1.0 if (f * t) % 1.0 < 0.5 else -1.0
            s = 0.6 * square + 0.25 * math.sin(2 * math.pi * f * 2 * t)
            attack = min(1.0, i / (n_note * 0.1))
            decay = max(0.0, 1.0 - (i / n_note) * 0.7)
            s = max(-1.0, min(1.0, s))
            out.append(int(s * amp * attack * decay))
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
        self.explosion = self.alarm = self.music = None
        self.engine_channel = None
        self.music_channel = None
        if not enabled:
            return
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)          # канал 0 — под фоновую музыку
            self.music_channel = pygame.mixer.Channel(0)
            self.music = _music_loop()
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

    # --- Настройки звука ---
    @property
    def available(self):
        """Инициализировался ли микшер (есть хотя бы один звук)."""
        return self.shoot is not None

    def set_enabled(self, on):
        """Вкл/выкл звук. Включить можно только при доступном микшере."""
        self.enabled = bool(on) and self.available
        if not self.enabled:
            self.engine_stop()
            self.music_stop()

    def set_volume(self, volume):
        """Мастер-громкость 0.0–1.0 для всех эффектов и музыки."""
        volume = max(0.0, min(1.0, volume))
        for snd in (self.shoot, self.hit, self.pickup, self.explosion,
                    self.alarm, self.engine):
            if snd:
                snd.set_volume(volume)
        if self.music_channel:
            self.music_channel.set_volume(volume)

    # --- Фоновая музыка (зациклена на выделенном канале) ---
    def music_start(self):
        if self.enabled and self.music and self.music_channel:
            if not self.music_channel.get_busy():
                self.music_channel.play(self.music, loops=-1)

    def music_stop(self):
        if self.music_channel:
            self.music_channel.stop()

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
