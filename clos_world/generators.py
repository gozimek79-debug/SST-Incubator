"""Generatory bodzcow CLOS v0.7.3.

Deterministyczne (sine_wave, step_signal, drift_signal) ignoruja seed
z zalozenia. Stochastyczne (gaussian_noise, pulse_signal) uzywaja seedu.
Dla stochastycznego dryftu uzyj scenarios.drift_world zamiast drift_signal.
"""

import math, random

def sine_wave(tick: int, frequency: float = 0.1, amplitude: float = 0.5, seed: int = 0) -> float:
    raw = 0.5 + amplitude * math.sin(2 * math.pi * frequency * tick)
    return max(0.0, min(1.0, raw))

def step_signal(tick: int, change_tick: int = 50, before: float = 0.2, after: float = 0.8, seed: int = 0) -> float:
    return before if tick < change_tick else after

def gaussian_noise(tick: int, mean: float = 0.5, variance: float = 0.1, seed: int = 0) -> float:
    rng = random.Random(seed * 1000 + tick)
    raw = rng.gauss(mean, math.sqrt(variance))
    return max(0.0, min(1.0, raw))

def drift_signal(tick: int, start_freq: float = 0.05, end_freq: float = 0.5, duration: int = 200, seed: int = 0) -> float:
    """Dryft czestotliwosci. Sam generator jest deterministyczny.
    Dla stochastycznego dryftu uzyj scenarios.drift_world, ktory dodaje
    seed-zalezny phase_shift i szum gaussowski."""
    progress = min(1.0, tick / duration)
    freq = start_freq + (end_freq - start_freq) * progress
    raw = 0.5 + 0.4 * math.sin(2 * math.pi * freq * tick)
    return max(0.0, min(1.0, raw))

def pulse_signal(tick: int, interval: int = 20, width: int = 3, seed: int = 0) -> float:
    rng = random.Random(seed)
    offset = rng.randint(0, interval - 1)
    position_in_interval = (tick + offset) % interval
    return 1.0 if position_in_interval < width else 0.0
