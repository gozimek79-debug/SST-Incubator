"""Scenariusze eksperymentalne CLOS v0.7.3."""

import random, math
from .generators import sine_wave, gaussian_noise, step_signal

CONTROL_ENVIRONMENTS = {"stable_world"}

def is_control(name: str) -> bool:
    return name in CONTROL_ENVIRONMENTS

def stable_world(tick: int, seed: int = 0) -> float:
    return sine_wave(tick, frequency=0.1, amplitude=0.4)

def noise_world(tick: int, seed: int = 0) -> float:
    signal = sine_wave(tick, frequency=0.1, amplitude=0.3)
    noise = gaussian_noise(tick, mean=0.0, variance=0.05, seed=seed)
    return max(0.0, min(1.0, signal + noise))

def drift_world(tick: int, seed: int = 0) -> float:
    """DRIFT_WORLD v0.7.3 – stochastyczny dryft zalezny od seedu."""
    rng = random.Random(seed)
    phase_shift = rng.uniform(0, 2 * math.pi)
    noise_amplitude = rng.uniform(0.01, 0.05)
    progress = min(1.0, tick / 300)
    freq = 0.05 + 0.45 * progress
    signal = 0.5 + 0.3 * math.sin(2 * math.pi * freq * tick + phase_shift)
    noise = gaussian_noise(tick, mean=0.0, variance=noise_amplitude, seed=seed)
    return max(0.0, min(1.0, signal + noise))

def shock_world(tick: int, seed: int = 0) -> float:
    rng = random.Random(seed)
    shock_tick = rng.randint(20, 80)
    shock_magnitude = rng.uniform(0.3, 0.9)
    if tick < shock_tick: return 0.2
    elif tick == shock_tick: return shock_magnitude
    else:
        noise = gaussian_noise(tick, mean=0.0, variance=0.02, seed=seed)
        return max(0.1, min(1.0, shock_magnitude * 0.8 + noise))

# --- SPRINT_v0.10.1.md P2: srodowiska walidacyjne, jedno na os zmiennosci ---
# Kazde jest CZYSTA FUNKCJA (tick, seed) -> float, jak wszystkie powyzsze - zero
# stanu, zero efektow ubocznych. Zaden nie zmienia istniejacych funkcji powyzej
# (regresja L1.1/L1.2 na noise_world/shock_world/stable_world jest wiec
# strukturalnie niemozliwa do naruszenia przez samo dodanie tych funkcji -
# zweryfikowane empirycznie w tests/test_new_environments_p2.py).

def high_noise_world(tick: int, seed: int = 0) -> float:
    """Os: POZIOM SZUMU. Jak noise_world, ale wariancja 5x wieksza (0.25 vs 0.05) -
    ten sam sygnal bazowy, testuje czy metryki przezyja duzo gorsze SNR."""
    signal = sine_wave(tick, frequency=0.1, amplitude=0.3)
    noise = gaussian_noise(tick, mean=0.0, variance=0.25, seed=seed)
    return max(0.0, min(1.0, signal + noise))

def recurring_shock_world(tick: int, seed: int = 0) -> float:
    """Os: CZESTOTLIWOSC ZAKLOCEN. Wstrzasy co stala liczbe tickow (interval=40),
    zamiast pojedynczego zdarzenia jak shock_world. Faza (offset) deterministyczna
    z samego seeda (jak shock_tick w shock_world); magnitude kazdego wstrzasu
    deterministyczne z (seed, tick) - zero stanu miedzy wywolaniami."""
    interval = 40
    offset = random.Random(seed).randint(0, interval - 1)
    position = (tick - offset) % interval
    if position == 0:
        return random.Random(seed * 7919 + tick).uniform(0.6, 0.95)
    noise = gaussian_noise(tick, mean=0.0, variance=0.02, seed=seed)
    return max(0.0, min(1.0, 0.2 + noise))

def weak_shock_world(tick: int, seed: int = 0) -> float:
    """Os: SILA PERTURBACJI. Jak shock_world (jeden wstrzas, ten sam rozklad
    shock_tick), ale shock_magnitude ledwo nad baseline 0.2 (0.25-0.35, nie
    0.3-0.9) - testuje czy recovery_time/homeostasis_band wykrywaja cokolwiek
    przy slabej perturbacji."""
    rng = random.Random(seed)
    shock_tick = rng.randint(20, 80)
    shock_magnitude = rng.uniform(0.25, 0.35)
    if tick < shock_tick: return 0.2
    elif tick == shock_tick: return shock_magnitude
    else:
        noise = gaussian_noise(tick, mean=0.0, variance=0.02, seed=seed)
        return max(0.1, min(1.0, shock_magnitude * 0.8 + noise))

def long_stable_shock_world(tick: int, seed: int = 0) -> float:
    """Os: DLUGOSC STABILNYCH OKRESOW. Jak shock_world, ale shock_tick w [100,150]
    zamiast [20,80] - znacznie dluzszy stabilny okres przed perturbacja. Gorna
    granica 150 (nie wiecej) CELOWO zostaje DOKLADNIE na bezpiecznej granicy dla
    L1.2: okno sustained-in-band sprawdzane przez compute_recovery_time() czyta
    az do indeksu t_shock+W-1=t_shock+149 (nie tylko do deadline=t_shock+W-N),
    wiec potrzeba t_shock+149 <= ticks_total-1=299, czyli t_shock<=150 (SPRINT_
    v0.11.0.md P2 - poprzednia wersja tego komentarza podawala blednie t_shock
    <=159, pomijajac +N-1 z samego okna; skorygowane, zero zmiany zachowania,
    bo shock_tick i tak nigdy nie przekraczal 150). Powyzej tej granicy
    lesson_L1_2.run_shock_recovery() podnosi teraz jawny wyjatek opisowy
    (RecoveryWindowOutOfDomainError) zamiast cichego KeyError - patrz tam."""
    rng = random.Random(seed)
    shock_tick = rng.randint(100, 150)
    shock_magnitude = rng.uniform(0.3, 0.9)
    if tick < shock_tick: return 0.2
    elif tick == shock_tick: return shock_magnitude
    else:
        noise = gaussian_noise(tick, mean=0.0, variance=0.02, seed=seed)
        return max(0.1, min(1.0, shock_magnitude * 0.8 + noise))

def unpredictable_world(tick: int, seed: int = 0) -> float:
    """Os: PRZEWIDYWALNOSC. Zero okresowego wzorca (w przeciwienstwie do
    wszystkich powyzszych, ktore maja sine_wave lub plateau u podstawy) - kazdy
    tick to niezalezna losowa wartosc z [0,1]. Przeciwny biegun wzgledem
    stable_world (calkowicie deterministyczny, okresowy)."""
    return random.Random(seed * 104729 + tick).uniform(0.0, 1.0)

SCENARIOS = {
    "stable_world": stable_world, "noise_world": noise_world,
    "drift_world": drift_world, "shock_world": shock_world,
    "high_noise_world": high_noise_world,
    "recurring_shock_world": recurring_shock_world,
    "weak_shock_world": weak_shock_world,
    "long_stable_shock_world": long_stable_shock_world,
    "unpredictable_world": unpredictable_world,
}
def get_scenario(name: str):
    if name not in SCENARIOS: raise ValueError(f"Unknown: {name}")
    return SCENARIOS[name]
def list_scenarios(): return list(SCENARIOS.keys())

# --- SPRINT_v0.11.0.md P2: rejestr WLASCIWOSCI scenariusza (nie nazwy) ---
# Ktore scenariusze deklaruja POJEDYNCZE, jednoznacznie zlokalizowane zdarzenie
# perturbacyjne (jeden t_shock) - wlasciwosc, ktorej clos_academy/lesson_L1_2.py
# uzywa do policzenia recovery_time/pre_shock_in_band, ZAMIAST dawnego
# name-gate `scenario == "shock_world"` (odkrycie SPRINT_v0.10.1.md P2:
# weak_shock_world i long_stable_shock_world maja DOKLADNIE tę sama
# jednoperturbacyjna strukture co shock_world, ale byly pomijane bo nazwa
# sie nie zgadzala - to byla "cisza gorsza niz blad", nie wlasciwosc scenariusza).
#
# recurring_shock_world CELOWO NIE jest w tym rejestrze: ma WIELOKROTNE,
# okresowe perturbacje (interval=40), wiec nie pasuje do modelu "jeden t_shock"
# ktory recovery_time/pre_shock_in_band zakladaja - to jest prawdziwy brak
# zastosowania konstruktu (jak stable_world/drift_world), NIE bledny pomin.
SINGLE_PERTURBATION_SCENARIOS = {
    "shock_world": lambda seed: random.Random(seed).randint(20, 80),
    "weak_shock_world": lambda seed: random.Random(seed).randint(20, 80),
    "long_stable_shock_world": lambda seed: random.Random(seed).randint(100, 150),
}


def has_single_perturbation(scenario: str) -> bool:
    """Czy `scenario` deklaruje dokladnie jedno, zlokalizowane zdarzenie
    perturbacyjne (WLASCIWOSC scenariusza, nie jego nazwa dosłowna)."""
    return scenario in SINGLE_PERTURBATION_SCENARIOS


def single_perturbation_tick(scenario: str, seed: int) -> int:
    """Tick zdarzenia perturbacyjnego dla scenariusza z has_single_perturbation()
    == True. Replikuje DOKLADNIE pierwsza operacje RNG danego scenariusza (ten
    sam mechanizm, uogólniony, co historyczny lesson_L1_2._shock_tick())."""
    if scenario not in SINGLE_PERTURBATION_SCENARIOS:
        raise ValueError(
            f"'{scenario}' nie deklaruje pojedynczej perturbacji - sprawdz "
            "has_single_perturbation(scenario) przed wywolaniem tej funkcji"
        )
    return SINGLE_PERTURBATION_SCENARIOS[scenario](seed)
