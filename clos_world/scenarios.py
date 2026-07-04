"""Scenariusze eksperymentalne – kompozycje generatorów.

Każdy scenariusz implementuje get_stimulus(tick, seed) → float.
"""

from .generators import sine_wave, gaussian_noise, drift_signal, pulse_signal, step_signal


def stable_world(tick: int, seed: int = 0) -> float:
    """STABLE_WORLD: czysta sinusoida, brak szumu, stała częstotliwość.

    Args:
        tick: Numer ticka.
        seed: Ziarno.

    Returns:
        Wartość w [0, 1].
    """
    return sine_wave(tick, frequency=0.1, amplitude=0.4, seed=seed)


def noise_world(tick: int, seed: int = 0) -> float:
    """NOISE_WORLD: sinus + szum gaussowski.

    Args:
        tick: Numer ticka.
        seed: Ziarno.

    Returns:
        Wartość w [0, 1].
    """
    signal = sine_wave(tick, frequency=0.1, amplitude=0.3, seed=seed)
    noise = gaussian_noise(tick, mean=0.0, variance=0.05, seed=seed)
    result = signal + noise
    return max(0.0, min(1.0, result))


def drift_world(tick: int, seed: int = 0) -> float:
    """DRIFT_WORLD: stopniowa zmiana częstotliwości.

    Args:
        tick: Numer ticka.
        seed: Ziarno.

    Returns:
        Wartość w [0, 1].
    """
    return drift_signal(tick, start_freq=0.05, end_freq=0.5, duration=200, seed=seed)


def shock_world(tick: int, seed: int = 0) -> float:
    """SHOCK_WORLD: nagły skok sygnału w deterministycznym ticku.

    Tick skoku jest wyznaczany przez seed.

    Args:
        tick: Numer ticka.
        seed: Ziarno.

    Returns:
        Wartość w [0, 1].
    """
    import random
    rng = random.Random(seed)
    shock_tick = rng.randint(30, 70)
    return step_signal(tick, change_tick=shock_tick, before=0.2, after=0.9, seed=seed)


# Mapa scenariuszy
SCENARIOS = {
    "stable_world": stable_world,
    "noise_world": noise_world,
    "drift_world": drift_world,
    "shock_world": shock_world,
}


def get_scenario(name: str):
    """Pobierz scenariusz po nazwie.

    Args:
        name: Nazwa scenariusza.

    Returns:
        Funkcja scenariusza.

    Raises:
        ValueError: Jeśli scenariusz nie istnieje.
    """
    if name not in SCENARIOS:
        available = ", ".join(SCENARIOS.keys())
        raise ValueError(f"Nieznany scenariusz: {name}. Dostępne: {available}")
    return SCENARIOS[name]


def list_scenarios() -> list:
    """Zwraca listę dostępnych scenariuszy."""
    return list(SCENARIOS.keys())
