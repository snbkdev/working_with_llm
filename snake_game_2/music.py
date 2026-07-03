"""Фоновая музыка в стиле чиптюн — синтезируется при запуске (без файлов).

Зацикленная 8-тактовая мелодия в ля-миноре: квадратная волна с duty 25%
(соло, как на NES), треугольная волна (бас) и шумовые ударные.
Генерация идёт в фоновом потоке, чтобы не задерживать запуск игры,
музыка вступает через пару секунд после старта.
"""

import array
import math
import random
import threading

import pygame

SAMPLE_RATE = 44100
_HALF = 2             # синтез на половинной частоте, сэмплы дублируются
BPM = 132
SLOT = 60 / BPM / 2   # длительность восьмой ноты, сек

_NOTE_SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _freq(name):
    """«A4» → частота в герцах (None — пауза)."""
    if not name:
        return None
    semi = _NOTE_SEMI[name[0]] + name.count("#")
    midi = 12 * (int(name[-1]) + 1) + semi
    return 440.0 * 2.0 ** ((midi - 69) / 12)


# 8 тактов по 8 восьмых; гармония: Am Am C G / Am F G Am
MELODY = [
    "A4", None, "C5", "E5", "A5", "G5", "E5", "C5",
    "D5", None, "F5", "A5", "G5", "F5", "E5", None,
    "C5", None, "E5", "G5", "C6", "B5", "G5", "E5",
    "A5", "G5", "E5", "D5", "B4", "G4", "B4", "D5",
    "A4", None, "C5", "E5", "A5", "G5", "E5", "C5",
    "F5", None, "A5", "C6", "A5", "G5", "F5", "E5",
    "G5", "F5", "E5", "D5", "E5", "D5", "B4", "G4",
    "A4", "B4", "C5", "B4", "A4", None, "E5", None,
]
BASS_ROOTS = ["A2", "A2", "C3", "G2", "A2", "F2", "G2", "A2"]  # по такту


def _build_loop():
    """Собирает весь цикл мелодии в один pygame.mixer.Sound."""
    rate = SAMPLE_RATE // _HALF
    n = int(rate * SLOT)
    fade = max(1, int(rate * 0.004))
    kick_n = int(rate * 0.06)
    snare_n = int(rate * 0.05)
    hat_n = int(rate * 0.015)
    rnd = random.Random(7)
    samples = array.array("h")

    for slot, mel_name in enumerate(MELODY):
        mel = _freq(mel_name)
        root = _freq(BASS_ROOTS[slot // 8])
        bass = root * (2 if slot % 2 else 1)  # бас «прыгает» на октаву
        beat = slot % 8
        kick = beat in (0, 4)
        snare = beat in (2, 6)
        for i in range(n):
            t = i / rate
            # Огибающая слота, чтобы на стыках нот не щёлкало
            env = min(1.0, i / fade, (n - i) / fade)
            v = 0.0
            if mel:
                ph = (t * mel) % 1.0
                v += (0.9 if ph < 0.25 else -0.9) * 0.20 * env
            ph = (t * bass) % 1.0
            v += (4.0 * abs(ph - 0.5) - 1.0) * 0.17 * env
            if kick and i < kick_n:
                f = 90.0 - 55.0 * i / kick_n  # «бочка»: тон падает
                v += math.sin(2 * math.pi * f * t) * 0.5 * (1 - i / kick_n)
            elif i < hat_n:
                v += rnd.uniform(-1, 1) * 0.05 * (1 - i / hat_n)
            if snare and i < snare_n:
                v += rnd.uniform(-1, 1) * 0.16 * (1 - i / snare_n)
            s = int(32767 * max(-0.95, min(0.95, v)))
            for _ in range(_HALF):
                samples.append(s)

    return pygame.mixer.Sound(buffer=samples.tobytes())


class Music:
    """Зацикленная фоновая музыка на выделенном канале микшера.

    `enabled` можно переключать на лету (кнопка в игре): луп генерируется
    лениво при первом включении, дальше просто ставится на паузу/снимается.
    """

    def __init__(self, enabled=True, volume=0.35):
        self.available = pygame.mixer.get_init() is not None
        self.enabled = enabled
        self.volume = volume
        self.channel = None
        self.game_paused = False
        self._building = False
        if self.available:
            pygame.mixer.set_reserved(1)  # канал 0 — только для музыки
        if self.enabled:
            self._ensure()

    def _ensure(self):
        """Запускает фоновую генерацию лупа, если её ещё не было."""
        if not self.available or self.channel or self._building:
            return
        self._building = True
        threading.Thread(target=self._start, daemon=True).start()

    def _start(self):
        try:
            sound = _build_loop()
            sound.set_volume(self.volume)
            self.channel = pygame.mixer.Channel(0)
            self.channel.play(sound, loops=-1)
            self._apply()  # вдруг за время генерации выключили/поставили паузу
        except pygame.error:
            self.channel = None

    def _apply(self):
        if self.channel:
            if self.enabled and not self.game_paused:
                self.channel.unpause()
            else:
                self.channel.pause()

    def set_enabled(self, on):
        """Кнопка вкл/выкл музыки."""
        self.enabled = on
        if on:
            self._ensure()
        self._apply()

    def set_paused(self, paused):
        """Ставит музыку на паузу вместе с игрой."""
        self.game_paused = paused
        self._apply()
