"""Scenariusze eksperymentalne – z pełnym wykorzystaniem seedu."""

import random
from .generators import sine_wave, gaussian_noise, drift_signal, step_signal


def stable_world(tick: int, seed: int = 0) -> float:
    """STABLE_WORLD: czysta sinusoida."""
    return sine_wave(tick, frequency=0.1, amplitude=0.4, seed=seed)


def noise_world(tick: int, seed: int = 0) -> float:
    """NOISE_WORLD: sinus + szum gaussowski zależny od seedu."""
    signal = sine_wave(tick, frequency=0.1, amplitude=0.3, seed=seed)
    noise = gaussian_noise(tick, mean=0.0, variance=0.05, seed=seed)
    result = signal + noise
    return max(0.0, min(1.0, result))


def drift_world(tick: int, seed: int = 0) -> float:
    """DRIFT_WORLD: stopniowa zmiana częstotliwości."""
    return drift_signal(tick, start_freq=0.05, end_freq=0.5, duration=200, seed=seed)


def shock_world(tick: int, seed: int = 0) -> float:
    """SHOCK_WORLD: deterministyczny skok zależny OD SEEDU.

    Każdy seed generuje szok w innym ticku i o innej sile.
    """
    rng = random.Random(seed)
    shock_tick = rng.randint(20, 80)
    shock_magnitude = rng.uniform(0.3, 0.9)

    if tick < shock_tick:
        return 0.2
    elif tick == shock_tick:
        return shock_magnitude
    else:
        # Dodaj szum zależny od seedu po szoku
        noise = gaussian_noise(tick, mean=0.0, variance=0.02, seed=seed)
        return max(0.1, min(1.0, shock_magnitude * 0.8 + noise))


SCENARIOS = {
    "stable_world": stable_world,
    "noise_world": noise_world,
    "drift_world": drift_world,
    "shock_world": shock_world,
}


def get_scenario(name: str):
    if name not in SCENARIOS:
        available = ", ".join(SCENARIOS.keys())
        raise ValueError(f"Nieznany scenariusz: {name}. Dostępne: {available}")
    return SCENARIOS[name]


def list_scenarios() -> list:
    return list(SCENARIOS.keys())
