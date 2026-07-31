"""W2 Primary Endpoint + procedura V-C (Adaptive Validation) - D-018,
publications/specyfikacja_W2_2026-07-28.md, publications/analiza_floor_model_2026-07-28.md.

MECHANIZM V-C JEST NIEKONFIGUROWALNY (D-018 pkt 6, specyfikacja_W2 §2.1a, warunek
weryfikacyjny W2-T7 punkt c): select_floor_model() przyjmuje WYLACZNIE env_fn (srodowisko
do scharakteryzowania) - brak jakiegokolwiek drugiego parametru, ktorym dalo by sie
wymusic model "constant" albo "per_tick". Decyzja wynika WYLACZNIE z porownania
bias_roznicowy (policzonego z samego generatora, PRZED jakimkolwiek przebiegiem
eksperymentalnym) z FLOOR_BIAS_TOLERANCE (clos_scientist/pc_001_experiment_config.py).
Nie istnieje sciezka kodu omijajaca to porownanie - zweryfikowane wprost w
tests/test_w2_endpoint.py::TestW2T7ValidationMechanism (introspekcja sygnatury +
brak jakiegokolwiek "if" rozgalezienia poza samym testem bias_roznicowy).
"""

from typing import Callable, Dict, List, Optional

from clos_world.floor_model import floor_at_tick, floor_profile, DEFAULT_N
from clos_scientist.pc_001_experiment_config import (
    FLOOR_BIAS_TOLERANCE,
    MIN_DENOMINATOR,
    FLOOR_LIMITED_CELL_THRESHOLD,
    W_EARLY_TICKS,
    W_LATE_TICKS,
    MEASURABLE_WINDOW_TICKS,
    FLOOR_ENV_VERIFICATION_TOLERANCE,
)

EnvFn = Callable[[int, int], float]


class FrozenFloorMismatchError(Exception):
    """Podniesiony gdy floor_env przeliczone przy starcie eksperymentu NIE
    miesci sie w tolerancji wzgledem wartosci zamrozonej w
    pc_001_experiment_config.FROZEN_FLOOR_NOISE_WORLD - HALT, nie ciche
    uzycie nowej wartosci (D-018: ta sama zasada co Hard-Halt dla hasha
    plikow krytycznych - wartosc zamrozona + kontrola zgodnosci, nie
    liczenie od nowa)."""


def select_floor_model(env_fn: EnvFn) -> Dict[str, object]:
    """Test waznosci V-C (specyfikacja_W2 §2.1a) - MECHANICZNY.

    Liczy floor(t) na CALYM mierzalnym oknie (MEASURABLE_WINDOW_TICKS), porownuje
    srednie obciazenie w W_early i W_late wzgledem floor_env, i wybiera model
    WYLACZNIE na podstawie porownania bias_roznicowy < FLOOR_BIAS_TOLERANCE.

    Jedyny parametr to `env_fn` (srodowisko do scharakteryzowania) - nie istnieje
    zaden dodatkowy argument pozwalajacy wymusic wynik "constant" albo "per_tick".
    N probek Monte Carlo jest STALA (clos_world.floor_model.DEFAULT_N=100_000,
    wyprowadzona z kryterium precyzji SE<0.001 - analiza_floor_model_2026-07-28.md
    §6), nie parametrem tej funkcji - zeby nie dawac nawet posredniej drogi do
    wplywania na wynik przez zanizenie precyzji.
    """
    profile = floor_profile(env_fn, MEASURABLE_WINDOW_TICKS)
    floor_env = sum(profile.values()) / len(profile)

    early_vals = [profile[t] for t in W_EARLY_TICKS]
    late_vals = [profile[t] for t in W_LATE_TICKS]
    bias_early = sum(early_vals) / len(early_vals) - floor_env
    bias_late = sum(late_vals) / len(late_vals) - floor_env
    bias_roznicowy = abs(bias_early - bias_late)

    if bias_roznicowy < FLOOR_BIAS_TOLERANCE:
        floor_model = "constant"
        warning = None
        floor_profile_out = None
    else:
        floor_model = "per_tick"
        warning = "bias exceeds tolerance"
        floor_profile_out = {t: round(v, 6) for t, v in profile.items()}

    return {
        "floor_model": floor_model,
        "floor_env": round(floor_env, 6),
        "bias_early": round(bias_early, 6),
        "bias_late": round(bias_late, 6),
        "bias_roznicowy": round(bias_roznicowy, 6),
        "floor_bias_tolerance": FLOOR_BIAS_TOLERANCE,
        "warning": warning,
        "floor_profile": floor_profile_out,
    }


def verify_frozen_floor_env(env_fn: EnvFn, frozen: Dict[str, object],
                             tolerance: float = FLOOR_ENV_VERIFICATION_TOLERANCE,
                             verification_seed_start: int = 600_000) -> float:
    """Kontrola reprodukowalnosci floor_env PRZED uruchomieniem eksperymentu
    (D-018) - wywolywana przy starcie, nie przy kazdym przebiegu.

    Przelicza floor_env z NIEZALEZNEJ probki Monte Carlo: `verification_seed_start`
    jest CELOWO INNY niz `frozen["seed_start"]` uzyty do wyznaczenia wartosci
    zamrozonej (domyslnie 500_000, patrz FROZEN_FLOOR_NOISE_WORLD) - identyczny
    seed_start dawalby BIT-IDENTYCZNY wynik (env_fn i floor_at_tick sa
    deterministyczne), co testowalyby wylacznie "czy kod sie nie zmienil" - to
    juz pokrywa hash CRITICAL_FILES_PC_001. Rozny seed_start testuje to, o co
    faktycznie chodzi: czy DWIE NIEZALEZNE probki Monte Carlo zgadzaja sie w
    granicach SE (a wiec czy generator/N sa nadal takie, jak przy zamrozeniu).

    Podnosi FrozenFloorMismatchError (HALT), gdy roznica >= tolerance. Zwraca
    przeliczona wartosc, gdy zgodna."""
    profile = floor_profile(env_fn, MEASURABLE_WINDOW_TICKS, N=frozen["N"],
                             seed_start=verification_seed_start)
    recomputed = sum(profile.values()) / len(profile)
    diff = abs(recomputed - frozen["value"])
    if diff >= tolerance:
        raise FrozenFloorMismatchError(
            f"floor_env dla {frozen['environment']} przeliczone jako "
            f"{recomputed:.6f} (niezalezna probka MC, seed_start="
            f"{verification_seed_start}), zamrozona wartosc "
            f"{frozen['value']} (z {frozen['date_computed']}) - roznica "
            f"{diff:.6f} >= tolerancja {tolerance}. HALT: generator "
            f"srodowiska mogl sie zmienic od czasu zamrozenia - eksperyment "
            f"NIE MOZE ruszyc z niezgodna wartoscia podlogi."
        )
    return recomputed


def compute_pe_reducible(pe_trajectory: Dict[int, Optional[float]],
                          floor_result: Dict[str, object]) -> Dict[int, Optional[float]]:
    """PE_red(t) = max(0, PE(t) - floor(t)) - floor(t) zalezny od modelu wybranego
    przez select_floor_model() ("constant": floor_env dla kazdego t; "per_tick":
    profil per-tickowy). Ticki bez pomiaru PE (None, np. faza ciszy L1.1 - nie
    dotyczy L1.2, ktore ma PERCEIVE zawsze wlaczony) zostaja None."""
    if floor_result["floor_model"] == "constant":
        floor_value = floor_result["floor_env"]

        def floor_for(t: int) -> float:
            return floor_value
    else:
        profile = floor_result["floor_profile"]

        def floor_for(t: int) -> float:
            return profile[t]

    return {
        t: (max(0.0, pe - floor_for(t)) if pe is not None else None)
        for t, pe in pe_trajectory.items()
    }


def classify_run(w_early_red: Optional[float]) -> str:
    """VALID / FLOOR_LIMITED / INSUFFICIENT_DATA per specyfikacja_W2 §3.2."""
    if w_early_red is None:
        return "INSUFFICIENT_DATA"
    return "VALID" if w_early_red >= MIN_DENOMINATOR else "FLOOR_LIMITED"


def classify_cell(run_classifications: List[str]) -> str:
    """Bezpiecznik przeciw skazeniu doborem proby (specyfikacja_W2 §3.3):
    >FLOOR_LIMITED_CELL_THRESHOLD (30%) FLOOR_LIMITED w komorce -> INCONCLUSIVE,
    niezaleznie od wyniku pozostalych przebiegow."""
    total = len(run_classifications)
    if total == 0:
        return "INSUFFICIENT_DATA"
    floor_limited = sum(1 for c in run_classifications if c == "FLOOR_LIMITED")
    if floor_limited / total > FLOOR_LIMITED_CELL_THRESHOLD:
        return "INCONCLUSIVE"
    return "OK"


def compute_w2_reduction(pe_red_trajectory: Dict[int, Optional[float]]) -> Dict[str, object]:
    """W_early_red, W_late_red, redukcja_W2, klasyfikacja przebiegu
    (specyfikacja_W2 §2.3, §3.2). Redukcja liczona TYLKO dla przebiegow VALID -
    dla FLOOR_LIMITED/INSUFFICIENT_DATA redukcja jest None (nie 0.0 - brak
    wyniku, nie wynik zerowy)."""
    early = [pe_red_trajectory[t] for t in W_EARLY_TICKS if pe_red_trajectory.get(t) is not None]
    late = [pe_red_trajectory[t] for t in W_LATE_TICKS if pe_red_trajectory.get(t) is not None]

    if not early:
        return {"w_early_red": None, "w_late_red": None, "reduction": None,
                "classification": "INSUFFICIENT_DATA"}

    w_early_red = sum(early) / len(early)
    w_late_red = sum(late) / len(late) if late else None
    classification = classify_run(w_early_red)

    reduction = None
    if classification == "VALID" and w_late_red is not None:
        reduction = (w_early_red - w_late_red) / w_early_red

    return {
        "w_early_red": round(w_early_red, 6),
        "w_late_red": round(w_late_red, 6) if w_late_red is not None else None,
        "reduction": round(reduction, 6) if reduction is not None else None,
        "classification": classification,
    }
