"""Звук должен быть безопасным no-op без аудио и корректно переключаться."""

from src.sound import Synth


def test_headless_is_noop():
    snd = Synth()                    # без аудиоустройства ok=False
    # play/munch не должны падать, даже когда звук недоступен
    snd.play("waka_a")
    snd.munch()
    snd.munch()
    snd.play("nonexistent")


def test_toggle():
    snd = Synth()
    start = snd.enabled
    assert snd.toggle() is (not start)
    assert snd.toggle() is start


def test_volume_clamped():
    snd = Synth()
    assert snd.set_volume(2.0) == 1.0
    assert snd.set_volume(-1.0) == 0.0
    assert snd.set_volume(0.5) == 0.5


def test_munch_alternates():
    snd = Synth()
    snd._munch = 0
    snd.munch(); a = snd._munch
    snd.munch(); b = snd._munch
    assert a != b                    # чередуется waka_a / waka_b
