"""Model podlogi nieredukowalnej (D-018, publications/specyfikacja_W2_2026-07-28.md,
publications/analiza_floor_model_2026-07-28.md).

Podloga NIE jest wyprowadzana analitycznie. `clos_world/generators.py:20` obcina
kazdy generowany sygnal do [0,1], wiec rozklad wyjsciowy jest normalnym UCIETY, nie
normalnym - wzor E|N(0,sigma^2)|=sigma*sqrt(2/pi) opisuje rozklad, ktorego zaden
generator w tym module NIE PRODUKUJE (D-017 krok 3: implementacja NIE zachowywala
zalozen wyprowadzenia analitycznego). Zamiast tego podloga jest wyznaczana
NUMERYCZNIE, przez probkowanie FAKTYCZNEGO generatora - to eliminuje cala klase
bledu D-017, bo nie ma idealizacji, ktora mogłaby sie rozjechac z implementacja.

floor(t) = oczekiwany blad bezwzgledny optymalnego predyktora (sredniej rozkladu)
w ticku t, oszacowany Monte Carlo z N niezaleznych realizacji env_fn(tick, seed).

Ten modul jest GENERYCZNY - dziala na dowolnym env_fn: (tick, seed) -> float (kazdy
scenariusz z clos_world/scenarios.py pasuje do tej sygnatury). Parametry SPECYFICZNE
dla PC-001 (FLOOR_BIAS_TOLERANCE, MIN_DENOMINATOR, okna W_early/W_late) CELOWO NIE
zyja tutaj - patrz clos_scientist/pc_001_experiment_config.py (D-018 pkt 3: parametr
prerejestrowany PC-001, nie globalna stala CLOS).
"""

from typing import Callable, Dict, List

DEFAULT_N = 100_000

# Pula seedow do probkowania Monte Carlo, CELOWO poza zakresem seedow PC-001
# (pilot: 1-5; konfirmacja: od 1001) - floor(t) nie dotyka Brain/genomu w ogole
# (czysta charakterystyka generatora srodowiska, wywolywana PRZED jakimkolwiek
# przebiegiem eksperymentalnym), wiec nakladanie sie puli seedow nie jest realnym
# ryzykiem skazenia danych - ale unikniecie tego pytania jest tanie.
DEFAULT_SEED_START = 500_000

EnvFn = Callable[[int, int], float]


def floor_at_tick(env_fn: EnvFn, tick: int, N: int = DEFAULT_N,
                   seed_start: int = DEFAULT_SEED_START) -> float:
    """floor(t) dla pojedynczego ticka: mean(|s_i - mean(s)|) po N realizacjach
    s_i = env_fn(tick, seed_i), seed_i = seed_start..seed_start+N-1.

    WOLA FAKTYCZNY GENERATOR (env_fn) - zero wzoru analitycznego, zero idealizacji
    rozkladu. To jest bezposrednia implementacja formuly z specyfikacja_W2 §2.1.
    """
    values = [env_fn(tick, s) for s in range(seed_start, seed_start + N)]
    mean = sum(values) / N
    return sum(abs(v - mean) for v in values) / N


def floor_profile(env_fn: EnvFn, ticks: List[int], N: int = DEFAULT_N,
                   seed_start: int = DEFAULT_SEED_START) -> Dict[int, float]:
    """floor(t) dla listy tickow - {tick: floor(t)}. Wrapper wygodnosciowy nad
    floor_at_tick(), ten sam N/seed_start dla kazdego ticka (spojna precyzja MC
    w calym profilu)."""
    return {t: floor_at_tick(env_fn, t, N=N, seed_start=seed_start) for t in ticks}
