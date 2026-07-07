"""Generatory bodźców CLOS.

UWAGA (v0.7.2): nie wszystkie generatory używają seedu. Deterministyczne
(sine_wave, step_signal, drift_signal) ignorują seed z założenia — parametr
`seed` pozostaje w sygnaturze dla spójności API, ale nie wpływa na wynik.
Stochastyczne (gaussian_noise, pulse_signal) realnie korzystają z seedu.
"""

import math
import random


def sine_wave(tick: int, frequency: float = 0.1, amplitude: float = 0.5, seed: int = 0) -> float:
    """Deterministyczna sinusoida. Seed nieużywany (środowisko kontrolne)."""
    raw = 0.5 + amplitude * math.sin(2 * math.pi * frequency * tick)
    return max(0.0, min(1.0, raw))


def step_signal(tick: int, change_tick: int = 50, before: float = 0.2, after: float = 0.8, seed: int = 0) -> float:
    """Deterministyczny skok progowy. Seed nieużywany."""
    return before if tick < change_tick else after


def gaussian_noise(tick: int, mean: float = 0.5, variance: float = 0.1, seed: int = 0) -> float:
    """Szum gaussowski – seed realnie wpływa na wartość."""
    rng = random.Random(seed * 1000 + tick)  # seed + tick = unikalna wartość
    raw = rng.gauss(mean, math.sqrt(variance))
    return max(0.0, min(1.0, raw))


def drift_signal(tick: int, start_freq: float = 0.05, end_freq: float = 0.5, duration: int = 200, seed: int = 0) -> float:
    """Drift częstotliwości. UWAGA: obecnie deterministyczny (seed nieużywany)."""
    progress = min(1.0, tick / duration)
    freq = start_freq + (end_freq - start_freq) * progress
    raw = 0.5 + 0.4 * math.sin(2 * math.pi * freq * tick)
    return max(0.0, min(1.0, raw))


def pulse_signal(tick: int, interval: int = 20, width: int = 3, seed: int = 0) -> float:
    # Seed wpływa na fazę impulsu
    rng = random.Random(seed)
    offset = rng.randint(0, interval - 1)
    position_in_interval = (tick + offset) % interval
    return 1.0 if position_in_interval < width else 0.0
