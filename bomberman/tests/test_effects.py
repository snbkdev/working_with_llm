"""Частицы, тряска и вспышка — чистая логика (без pygame)."""

from src import config as c
from src.effects import Effects, Particle


def test_explosion_spawns_particles_shake_flash():
    fx = Effects(seed=1)
    fx.explosion(100, 100, now=0, fire=2)
    assert len(fx.particles) == c.EMBERS_MIN + c.EMBERS_FIRE * 2
    assert fx.shake > 0
    assert len(fx.flashes) == 1               # одно локальное свечение у взрыва


def test_shake_is_capped():
    fx = Effects(seed=1)
    for _ in range(20):
        fx.explosion(0, 0, now=0, fire=6)
    assert fx.shake <= c.SHAKE_MAX


def test_update_decays_shake_and_expires_flash():
    fx = Effects(seed=1)
    fx.explosion(0, 0, now=0, fire=1)
    s0 = fx.shake
    fx.update(0)                      # первый вызов только фиксирует _last
    fx.update(16)
    assert fx.shake < s0
    assert fx.flashes                 # ещё живо сразу после взрыва
    fx.update(c.FLASH_MS + 1)         # прожило дольше срока — исчезает
    assert fx.flashes == []


def test_particles_expire():
    fx = Effects(seed=2)
    fx.death(50, 50, now=0, color=(200, 100, 100))
    assert fx.particles
    fx.update(0)
    for step in range(1, 200):
        fx.update(step * 16)
    assert fx.particles == []         # все отжили


def test_particle_advance_moves_and_dies():
    p = Particle(0, 0, vx=0.1, vy=0.0, life=100, color=(255, 0, 0), size=3, grav=0.0)
    assert p.advance(50) is True
    assert p.x == 5.0                 # 0.1 px/мс * 50 мс
    assert p.advance(60) is False     # жизнь исчерпана


def test_reset_clears_state():
    fx = Effects(seed=3)
    fx.explosion(0, 0, now=0, fire=3)
    fx.reset()
    assert fx.particles == []
    assert fx.shake == 0.0
    assert fx.flashes == []
    assert fx.shake_offset() == (0, 0)


def test_shake_offset_within_amplitude():
    fx = Effects(seed=4)
    fx.explosion(0, 0, now=0, fire=1)
    dx, dy = fx.shake_offset()
    assert abs(dx) <= fx.shake and abs(dy) <= fx.shake
