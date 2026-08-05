"""Konfiguracja eksperymentu PC-001 (D-012, specyfikacja_W2_2026-07-28.md §1).

Jawna, nazwana warstwa "konfiguracja eksperymentu" (lekcja x srodowisko x
hipoteza x endpoint) - zeby wynik PC-001 (protokol L1.2 w noise_world) nie byl
czytany jako "shock recovery" (Aneks 3 §1, specyfikacja_W2 §1: L1.2 opisuje
PROTOKOL, nie konkretna dynamike swiata - zweryfikowane w docstringu
clos_academy/lesson_L1_2.py, nowa lekcja niepotrzebna).

Stale ponizej (FLOOR_BIAS_TOLERANCE, MIN_DENOMINATOR, FLOOR_LIMITED_CELL_THRESHOLD,
okna W_early/W_late) sa PARAMETRAMI PREREJESTROWANYMI PC-001, NIE globalnymi
stalymi CLOS (D-018 pkt 3) - zyja tutaj, nie w clos_world/floor_model.py (modul
generyczny, uzywalny przez przyszle eksperymenty z WLASNYMI wartosciami tych
parametrow, wlasna prerejestracja).
"""

from typing import Dict, List

# --- Deklaratywny opis eksperymentu (D-012) ---
EXPERIMENT_CONFIG: Dict[str, object] = {
    "name": "PC-001",
    "hypothesis": "Predictive Coding (redukcja bledu redukowalnego)",
    "environments": {
        "primary": "noise_world",
        "K3": "shock_world",
        "K4": "pure_noise_world",
    },
    "protocol": {
        "lesson": "L1.2",
        "ticks_total": 300,
        "perceive_always_on": True,
        "note": (
            "L1.2 jest scenariuszowo-niezalezna (docstring clos_academy/"
            "lesson_L1_2.py: t_shock/pre_shock_in_band liczone dla WLASCIWOSCI "
            "scenariusza, nie nazwy 'shock_world'; w stable_world liczona jest "
            "bazowa stabilnosc, nie recovery_time; lekcja obsluguje tez "
            "weak_shock_world i long_stable_shock_world) - nowa lekcja "
            "niepotrzebna (Aneks 3 §1, specyfikacja_W2_2026-07-28.md §1)."
        ),
    },
    "endpoint": "W2 + procedura V-C (Adaptive Validation, D-018)",
    "statistical_model": [
        "wilcoxon_signed_rank", "kendall_tau", "spearman_rho",
        "mann_whitney_u", "benjamini_hochberg",
    ],
}

# --- Parametry W2 (specyfikacja_W2_2026-07-28.md) ---

# §2.1a: 10% wartosci MIN_DENOMINATOR. Parametr prerejestrowany PC-001.
FLOOR_BIAS_TOLERANCE: float = 0.002

# §3.1: ~11% najmniejszej niezerowej podlogi (shock_world po wstrzasie, ~0.113),
# ~8% podlogi pure_noise_world. Ponizej tego progu W_early_red jest tego samego
# rzedu co fluktuacja probkowania w oknie 60 tickow.
MIN_DENOMINATOR: float = 0.02

# §3.3: bezpiecznik przeciw skazeniu doborem proby - >30% FLOOR_LIMITED w komorce
# -> cala komorka INCONCLUSIVE, niezaleznie od wyniku pozostalych przebiegow.
FLOOR_LIMITED_CELL_THRESHOLD: float = 0.30

# Warunek B (prog wielkosci redukcji) - PARAMETR PREREJESTROWANY PC-001, NIE
# globalna stala CLOS (D-018 pkt 3, jak pozostale stale w tym pliku).
#
# preregistration_PC_001_ANEKS_1_2026-07-28.md, "Zmiana 4" ("jawne oznaczenie
# pochodzenia progu 20%"): prog jest KONWENCJA PROJEKTU przyjeta w AIA v4, NIE
# wartoscia wyprowadzona z literatury przedmiotu ani z analizy oczekiwanej
# wielkosci efektu. Jego wartoscia jest NIEZMIENNOSC, nie trafnosc.
#
# "Zmiana progu po obejrzeniu danych jest niedopuszczalna i uniewaznia
# prerejestracje" (Aneks 1, tamze). Ta stala nie ma byc dostrajana - ma byc
# adresem, pod ktorym zyje wartosc juz ustalona przed zobaczeniem jakichkolwiek
# danych konfirmacyjnych.
#
# Do tego zlecenia (Z9) prog istnial WYLACZNIE jako tekst proza w prerejestracji
# i Aneksie 1 - clos_scientist/w2_endpoint.py liczy redukcje, ale NIE porownuje
# jej z progiem (to porownanie w repo nie istnieje, powstanie dopiero przy
# kodzie ewaluacji reguly decyzyjnej). Ta stala nadaje progowi ADRES; NIE
# implementuje porownania - to osobny, nieobjety tym zleceniem krok.
CONDITION_B_REDUCTION_THRESHOLD: float = 0.20

# Okna pomiarowe - z publications/preregistration_PC_001.json
# primary_endpoint.condition_b_reduction.windows (niezmienione przez W2,
# specyfikacja_W2 §6: "okien pomiarowych ta specyfikacja NIE rozstrzyga").
# Scenariuszowo-niezalezne (pozycja tickow w 300-tickowym przebiegu L1.2).
W_EARLY_TICKS: List[int] = list(range(0, 60))     # ticki 0-59, pierwsze 20%
W_LATE_TICKS: List[int] = list(range(240, 300))   # ticki 240-299, ostatnie 20%

# "Cale mierzalne okno" (specyfikacja_W2 §2.1a) - L1.2 ma PERCEIVE zawsze
# wlaczony (Aneks 3 §1: "300 tickow, PERCEIVE zawsze"), wiec prediction_error
# jest mierzalny na CALYM przebiegu, nie tylko w podoknach - w odroznieniu od
# L1.1, gdzie faza ciszy jest niemierzalna (CURRENT_SCIENTIFIC_LIMITS.md §8).
MEASURABLE_WINDOW_TICKS: List[int] = list(range(0, 300))

# --- floor_env jako WARTOSC PREREJESTROWANA (D-018) ---
#
# Probkowanie Monte Carlo daje INNA wartosc przy kazdym nowym probkowaniu (inny
# seed_start/N) - bez zamrozenia tej liczby wyniki W2 nie sa bitowo odtwarzalne
# miedzy uruchomieniami eksperymentu. Ta sama logika co PC_001_BASELINE
# (execution_package_v0_11/hashes/pc_001_baseline_hash.txt): wartosc ZAMROZONA
# + kontrola zgodnosci przy kazdym uzyciu (clos_scientist.w2_endpoint.
# verify_frozen_floor_env), NIE liczenie floor_env od nowa za kazdym razem, i
# NIGDY ciche uzycie nowej wartosci przy rozjezdzie.
#
# Wyznaczona RAZ: execution_package_v0_11/runners/compute_noise_world_floor.py,
# 2026-07-28 (jednorazowy runner, CELOWO POZA CRITICAL_FILES_PC_001 - wyznaczyl
# wartosc, nie jest kodem stosowanym w eksperymencie, decyzja CTO).
FROZEN_FLOOR_NOISE_WORLD: Dict[str, object] = {
    "environment": "noise_world",
    "value": 0.09589,
    "date_computed": "2026-07-28",
    "N": 100_000,
    "seed_start": 500_000,
    "seed_range": "500000-599999",
    "bias_roznicowy": 0.000024,
    "floor_model": "constant",
}

# Tolerancja kontroli reprodukowalnosci floor_env przy starcie eksperymentu -
# TA SAMA wartosc co kryterium precyzji SE<0.001 uzyte do wyprowadzenia
# N=100_000 (publications/analiza_floor_model_2026-07-28.md §6). Rozjazd >=
# tolerancja -> HALT (clos_scientist.w2_endpoint.FrozenFloorMismatchError),
# nie ciche przejscie na przeliczona wartosc.
FLOOR_ENV_VERIFICATION_TOLERANCE: float = 0.001
