"""Scenariusze eksperymentalne CLOS.

UWAGA metodologiczna (v0.7.2):
Nie każdy scenariusz jest stochastyczny. `stable_world` jest z założenia
DETERMINISTYCZNYM ŚRODOWISKIEM KONTROLNYM (Control Environment) — seed
NIE wpływa na jego przebieg i jest to cecha oczekiwana, nie błąd.
Scenariusze stochastyczne (shock_world, noise_world) realnie korzystają z seedu.
Zob. CONTROL_ENVIRONMENTS oraz is_control().
"""

import random
from .generators import sine_wave, gaussian_noise, drift_signal, step_signal


# Scenariusze deterministyczne z założenia — służą jako punkt odniesienia (baseline).
# Dla nich zerowa wariancja między seedami jest OCZEKIWANA i poprawna.
CONTROL_ENVIRONMENTS = {"stable_world"}


def is_control(name: str) -> bool:
    """Czy scenariusz jest deterministycznym środowiskiem kontrolnym.

    Reszta systemu (metrologia, raporty) używa tego, by NIE raportować
    cross-seed CI95 tam, gdzie wariancja jest z definicji zerowa.
    """
    return name in CONTROL_ENVIRONMENTS


def stable_world(tick: int, seed: int = 0) -> float:
    """STABLE_WORLD — deterministyczne środowisko KONTROLNE (baseline).

    Czysta sinusoida, bez szumu, driftu i zdarzeń losowych. Seed jest
    świadomie nieużywany: każdy seed daje identyczny przebieg. Zerowa
    wariancja jest oczekiwaną cechą eksperymentu kontrolnego i stanowi
    dowód reprodukowalności bazowej mechaniki Brain.
    """
    # seed celowo nieużyty — patrz docstring (Control Environment)
    return sine_wave(tick, frequency=0.1, amplitude=0.4)


def noise_world(tick: int, seed: int = 0) -> float:
    """NOISE_WORLD — sinus + szum gaussowski zależny od seedu (stochastyczny)."""
    signal = sine_wave(tick, frequency=0.1, amplitude=0.3)
    noise = gaussian_noise(tick, mean=0.0, variance=0.05, seed=seed)
    result = signal + noise
    return max(0.0, min(1.0, result))


def drift_world(tick: int, seed: int = 0) -> float:
    """DRIFT_WORLD — stopniowa zmiana częstotliwości.

    ZNANE OGRANICZENIE (v0.7.2): obecna implementacja drift_signal nie
    używa seedu, więc scenariusz jest de facto deterministyczny, mimo że
    NIE jest oznaczony jako kontrolny. Jeśli DRIFT ma być stochastyczny,
    wymaga seed-zależnego komponentu; jeśli kontrolny — dodaj go do
    CONTROL_ENVIRONMENTS. Do rozstrzygnięcia świadomą decyzją naukową.
    """
    return drift_signal(tick, start_freq=0.05, end_freq=0.5, duration=200, seed=seed)


def shock_world(tick: int, seed: int = 0) -> float:
    """SHOCK_WORLD — stochastyczny skok zależny OD SEEDU.

    Każdy seed generuje szok w innym ticku i o innej sile → realna wariancja.
    """
    rng = random.Random(seed)
    shock_tick = rng.randint(20, 80)
    shock_magnitude = rng.uniform(0.3, 0.9)

    if tick < shock_tick:
        return 0.2
    elif tick == shock_tick:
        return shock_magnitude
    else:
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
