"""Population Generator - Latin Hypercube Sampling genomow (SPRINT_v0.10.1.md P1/P3).

Realizuje DOKLADNIE publications/preregistration_v0_10_1_population.json:
population_design.sampling_method + population_design.sample_size. Zero zmian
w genome/birth (Core) - kazdy "genom" populacji to slownik 5 wartosci liczbowych
(plasticity, learning_rate, decay_rate, homeostasis_target, memory_capacity),
NADPISywanych NAD juz zbudowanym presetem "default" przez run_pattern_echo()/
run_shock_recovery() (genome_params=, patrz tam) - genom bazowy jest uzywany
WYLACZNIE jako neutralne zrodlo brain_id/identity.

Trzy dodatkowe pola BrainTissue (prediction_depth, attention_threshold,
meta_cognition_sensitivity) NIE sa tu w ogole wymieniane - lesson_L1_1.py/
lesson_L1_2.py nigdy ich nie czytaja ani z presetu, ani z genome_params
(zweryfikowane grepem przed napisaniem tego modulu), wiec BrainTissue uzywa
swoich wlasnych defaultow dataclass (3, 0.3, 0.5) dla KAZDEGO z 23 genomow -
strukturalnie stale, nie tylko "nie losowane".
"""

import random
from typing import Any, Dict, List, Optional

POPULATION_SAMPLING_SEED = 20101
N_NEW_GENOMES = 20

# Kolejnosc i granice DOKLADNIE z preregistration_v0_10_1_population.json
# population_design.parameter_space.dimensions - zrodlo granic: genome/presets.py
# (Core, TYLKO ODCZYT, patrz bounds_source w prerejestracji).
DIMENSIONS = [
    ("plasticity", 0.1, 1.0, float),
    ("learning_rate", 0.01, 1.0, float),
    ("decay_rate", 0.001, 0.1, float),
    ("homeostasis_target", 0.0, 1.0, float),
    ("memory_capacity", 10, 1000, int),
]

ANCHOR_PRESETS = ["default", "minimal", "highly_plastic"]


def _latin_hypercube_unit(n: int, seed: int) -> List[List[float]]:
    """LHS w [0,1)^d, d=len(DIMENSIONS). Kazdy wymiar stratyfikowany w n
    rownych przedzialow, jeden losowy punkt na przedzial, NIEZALEZNIE
    permutowany miedzy wymiarami (standardowy LHS - brak korelacji miedzy
    wymiarami wprowadzonej przez sama metode probkowania)."""
    rng = random.Random(seed)
    d = len(DIMENSIONS)
    unit_samples = [[0.0] * d for _ in range(n)]
    for dim_idx in range(d):
        points = [(i + rng.random()) / n for i in range(n)]
        rng.shuffle(points)
        for i in range(n):
            unit_samples[i][dim_idx] = points[i]
    return unit_samples


def generate_population(n_new: int = N_NEW_GENOMES,
                         seed: int = POPULATION_SAMPLING_SEED) -> List[Dict[str, Any]]:
    """23 genomy: n_new (domyslnie 20) z LHS + 3 istniejace presety (anchor).

    Zwraca liste slownikow:
        genome_id: etykieta (np. "pop_003" albo "default")
        kind: "lhs" | "anchor"
        genome_preset: preset uzyty jako baza (zawsze "default" dla lhs)
        genome_params: dict 5 wartosci (lhs) albo None (anchor - istniejacy,
            niezmieniony mechanizm presetow, zero nowego kodu na tej sciezce)
    """
    unit = _latin_hypercube_unit(n_new, seed)
    population: List[Dict[str, Any]] = []
    for i, point in enumerate(unit):
        params: Dict[str, Any] = {}
        for (name, lo, hi, cast), u in zip(DIMENSIONS, point):
            value = lo + u * (hi - lo)
            params[name] = int(round(value)) if cast is int else round(value, 6)
        population.append({
            "genome_id": f"pop_{i:03d}",
            "kind": "lhs",
            "genome_preset": "default",
            "genome_params": params,
        })
    for preset in ANCHOR_PRESETS:
        population.append({
            "genome_id": preset,
            "kind": "anchor",
            "genome_preset": preset,
            "genome_params": None,
        })
    return population


if __name__ == "__main__":
    import json
    print(json.dumps(generate_population(), indent=2, ensure_ascii=False))
