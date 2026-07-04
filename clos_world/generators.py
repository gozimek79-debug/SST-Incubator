"""Generatory bodźców – czyste, deterministyczne funkcje.

ZERO global state. ZERO random() bez seed. Wszystko clamped do [0, 1].
"""

import math
import random


def sine_wave(tick: int, frequency: float = 0.1, amplitude: float = 0.5, seed: int = 0) -> float:
    """Generuje falę sinusoidalną.

    Args:
        tick: Numer ticka.
        frequency: Częstotliwość fali.
        amplitude: Amplituda (0-0.5, bo wynik w [0,1]).
        seed: Ziarno (nieużywane, sinus jest deterministyczny).

    Returns:
        Wartość w [0, 1].
    """
    raw = 0.5 + amplitude * math.sin(2 * math.pi * frequency * tick)
    return max(0.0, min(1.0, raw))


def step_signal(tick: int, change_tick: int = 50, before: float = 0.2, after: float = 0.8, seed: int = 0) -> float:
    """Generuje sygnał skokowy – zmiana wartości w danym ticku.

    Args:
        tick: Numer ticka.
        change_tick: Tick, w którym następuje zmiana.
        before: Wartość przed zmianą.
        after: Wartość po zmianie.
        seed: Ziarno (nieużywane).

    Returns:
        Wartość w [0, 1].
    """
    return before if tick < change_tick else after


def gaussian_noise(tick: int, mean: float = 0.5, variance: float = 0.1, seed: int = 0) -> float:
    """Generuje szum gaussowski.

    Args:
        tick: Numer ticka.
        mean: Średnia rozkładu.
        variance: Wariancja.
        seed: Ziarno dla determinizmu.

    Returns:
        Wartość w [0, 1].
    """
    rng = random.Random(seed + tick)
    raw = rng.gauss(mean, math.sqrt(variance))
    return max(0.0, min(1.0, raw))


def drift_signal(tick: int, start_freq: float = 0.05, end_freq: float = 0.5, duration: int = 200, seed: int = 0) -> float:
    """Generuje sygnał z płynną zmianą częstotliwości.

    Args:
        tick: Numer ticka.
        start_freq: Częstotliwość początkowa.
        end_freq: Częstotliwość końcowa.
        duration: Czas trwania zmiany w tickach.
        seed: Ziarno (nieużywane).

    Returns:
        Wartość w [0, 1].
    """
    progress = min(1.0, tick / duration)
    freq = start_freq + (end_freq - start_freq) * progress
    raw = 0.5 + 0.4 * math.sin(2 * math.pi * freq * tick)
    return max(0.0, min(1.0, raw))


def pulse_signal(tick: int, interval: int = 20, width: int = 3, seed: int = 0) -> float:
    """Generuje sygnał impulsowy – krótkie impulsy w regularnych odstępach.

    Args:
        tick: Numer ticka.
        interval: Co ile ticków impuls.
        width: Szerokość impulsu w tickach.
        seed: Ziarno (nieużywane).

    Returns:
        Wartość w [0, 1] – 1.0 podczas impulsu, 0.0 poza.
    """
    position_in_interval = tick % interval
    return 1.0 if position_in_interval < width else 0.0
