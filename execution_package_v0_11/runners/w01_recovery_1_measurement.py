"""PC-001 W-01 (D-025 pkt 1, nowa rola): mierzy recovery_1 (pierwszy wstrzas)
w recurring_shock_world, interval=40 (OBECNY, BEZ ZMIAN). Cel: zweryfikowac,
czy K3b jest wykonalne W OGOLE - czy recovery miesci sie w oknie 40 tickow
miedzy kolejnymi wstrzasami - niezaleznie od dlugosci calego przebiegu L1.2
(300 dzis, 400 po ewentualnym C1 - ta zmiana NIE dotyczy interval, wiec W-01
jest wazne niezaleznie od decyzji C1/B).

23 genomy x 3 seedy = 69 przebiegow.

GWARANCJA MECHANICZNA (jak W_early_red, B4a/B4a-2): entropy_by_tick
przechwytywane WYLACZNIE w pamieci (monkeypatch SnapshotEngine.create_snapshot
- entropy jest juz przekazywane do create_snapshot() w run_shock_recovery(),
obserwacja Read-Only, addytywna), recovery_1 liczone przez ISTNIEJACA, juz
przetestowana funkcje compute_recovery_time() (clos_academy/lesson_L1_2.py -
ZERO duplikacji formuly recovery_time), trajektoria entropii ODRZUCANA
natychmiast po obliczeniu jednej liczby na przebieg.

RAPORTOWANIE (D-025, ograniczenie CTO, SCISLEJSZE niz przy W_early_red):
WYLACZNIE mediana/IQR/max zbiorczo. Zero wartosci per-genom, zero wartosci
per-przebieg, zero listy 69 surowych recovery_1 - nawet w postaci "runs".
Ten plik NIE wchodzi do CRITICAL_FILES_PC_001 (ten sam scoping co pilot_
power_analysis*.py - dostarcza dane WEJSCIOWE do decyzji o wykonalnosci
K3b, nie jest kodem stosowanym w eksperymencie konfirmacyjnym)."""

import json
import random as _random_module
import statistics as py_statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from clos_academy.lesson_L1_2 import run_shock_recovery, compute_recovery_time, N_SUSTAIN
from clos_kernel.snapshot_engine import SnapshotEngine

SEEDS = [1, 2, 3]
ENVIRONMENT = "recurring_shock_world"
LESSON = "L1.2"
INTERVAL = 40  # recurring_shock_world interval, OBECNY - bez zmian (D-025)
TICKS_TOTAL = 300

OUTPUT_PATH = REPO_ROOT / "reports" / "pilot" / "w01_recovery_1_recurring_shock_world.json"


def _genomes() -> List[Dict[str, Any]]:
    path = REPO_ROOT / "execution_package_v0_11" / "genomes" / "population.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["genomes"]


def first_shock_tick(seed: int, interval: int = INTERVAL) -> int:
    """Replikuje DOKLADNIE pierwsze losowanie recurring_shock_world
    (clos_world/scenarios.py:60): offset = random.Random(seed).randint(0, interval-1).
    Pierwszy wstrzas wystepuje na tick=offset (position=(offset-offset)%interval=0
    - najmniejszy tick>=0, dla ktorego position==0)."""
    return _random_module.Random(seed).randint(0, interval - 1)


CEILING_THRESHOLD = 0.99  # entropy >= tego na koncu okna = "utkniete przy suficie [0,1]"
FLOOR_THRESHOLD = 0.01


def _recovery_1_for_run(genome: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """Uruchamia L1.2 RAZ na recurring_shock_world, przechwytuje entropy_by_tick
    WYLACZNIE w pamieci, liczy recovery_1 przez compute_recovery_time() (kod
    juz istniejacy/przetestowany w lesson_L1_2.py), i porzuca cala trajektorie
    natychmiast po zwroceniu wyniku. Dodatkowo klasyfikuje CENZUROWANE
    przebiegi wg entropii NA KONCU okna [t_shock_1, t_shock_1+interval) -
    "ceiling" (>=0.99, utkniete przy gornym ograniczeniu [0,1]) vs "floor"
    (<=0.01) vs "other" (cenzurowane, ale nie przy granicy) - agregatowa
    klasyfikacja przyczyny cenzurowania, NIE per-genom/per-przebieg dana
    (patrz build_report - tylko LICZNIKI wchodza do raportu)."""
    captured_entropy: Dict[int, float] = {}
    original = SnapshotEngine.create_snapshot

    def spy(self, *args, **kwargs):
        snapshot = original(self, *args, **kwargs)
        tick = kwargs.get("tick")
        entropy = kwargs.get("entropy")
        if tick is not None and entropy is not None:
            captured_entropy[tick] = entropy
        return snapshot

    SnapshotEngine.create_snapshot = spy
    try:
        result = run_shock_recovery(
            genome_preset=genome["genome_preset"], seed=seed, scenario=ENVIRONMENT,
            genome_params=genome["genome_params"], genome_label=genome["genome_id"],
            ticks_total=TICKS_TOTAL, observe=True,
        )
    finally:
        SnapshotEngine.create_snapshot = original

    band = (result["homeostasis_band"]["low"], result["homeostasis_band"]["high"])
    t_shock_1 = first_shock_tick(seed)

    value, censored = compute_recovery_time(
        captured_entropy, t_shock_1, band, n=N_SUSTAIN, w=INTERVAL,
    )
    if not censored:
        return {"value": float(value), "censor_reason": None}

    entropy_at_window_end = captured_entropy[t_shock_1 + INTERVAL - 1]
    if entropy_at_window_end >= CEILING_THRESHOLD:
        reason = "ceiling"
    elif entropy_at_window_end <= FLOOR_THRESHOLD:
        reason = "floor"
    else:
        reason = "other"
    return {"value": None, "censor_reason": reason}


def run_w01() -> List[Dict[str, Any]]:
    genomes = _genomes()
    records: List[Dict[str, Any]] = []
    for genome in genomes:
        for seed in SEEDS:
            records.append(_recovery_1_for_run(genome, seed))
    return records


def build_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """UWAGA (znalezisko wykonawcy, nie w oryginalnym zleceniu): mediana/IQR/max
    licza sie WYLACZNIE po przebiegach NIE-cenzurowanych (survivors). Gdy
    odsetek cenzurowania jest wysoki, ta statystyka jest myslaca sama w sobie
    (klasyczny survivorship bias) - dlatego n_censored/n_censored_at_ceiling
    MUSZA byc raportowane OBOK, nie tylko median/IQR/max w izolacji, inaczej
    ten sam raport moglby zostac odczytany jako 'K3b wykonalne z zapasem' przy
    faktycznym ~74% przebiegow, gdzie recovery nie zaszlo w ogole (entropia
    utkniela przy suficie [0,1] - dane, nie zalozenie, patrz interpretation)."""
    non_censored = [r["value"] for r in records if r["value"] is not None]
    censored = [r for r in records if r["value"] is None]
    n_ceiling = sum(1 for r in censored if r["censor_reason"] == "ceiling")
    n_floor = sum(1 for r in censored if r["censor_reason"] == "floor")
    n_other_censored = sum(1 for r in censored if r["censor_reason"] == "other")

    median = q1 = q3 = maximum = None
    if non_censored:
        sv = sorted(non_censored)
        median = py_statistics.median(sv)
        maximum = max(sv)
        if len(sv) >= 2:
            quantiles = py_statistics.quantiles(sv, n=4)
            q1, q3 = quantiles[0], quantiles[2]

    total = len(records)
    censoring_rate = len(censored) / total if total else None

    # Interpretacja MUSI byc zdominowana przez odsetek cenzurowania, nie tylko
    # przez median-of-survivors (patrz docstring powyzej) - progi z D-025 zostaly
    # napisane przy niejawnym zalozeniu niskiego cenzurowania; ten pilot je obala.
    if total == 0:
        interpretation = None
    elif censoring_rate > 0.30:
        interpretation = (
            f"K3b NIEWYKONALNE w obecnym srodowisku: {len(censored)}/{total} przebiegow "
            f"({censoring_rate:.0%}) NIE odzyskuje homeostazy w interval=40 w ogole "
            f"(z czego {n_ceiling} utkniete przy suficie entropii [0,1] - efekt "
            f"dynamiczny, nie brakujace dane). Mediana/IQR/max ponizej sa policzone "
            f"WYLACZNIE z {len(non_censored)} przebiegow, ktore odzyskaly - "
            f"survivorship bias, NIE dowod wykonalnosci K3b."
        )
    elif median is not None and median < 20:
        interpretation = "K3b wykonalne z zapasem (mediana < 20 tickow, cenzurowanie <=30%)"
    elif median is not None and median <= 35:
        interpretation = "wykonalne, ale ciasno (mediana 20-35) - wymaga dodatkowej analizy cenzurowania"
    else:
        interpretation = "recovery NIE miesci sie w interval=40 (mediana > 35) - K3b niewykonalne w obecnym srodowisku niezaleznie od dlugosci przebiegu"

    return {
        # Odmrozenie panelu (daty w artefaktach): brakowalo pola daty tresci -
        # dodane dla przyszlych przebiegow. Skrypt nie jest czlonkiem
        # CRITICAL_FILES_PC_001 (jednorazowy runner pomiarowy).
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "power_analysis_only",
        "NEVER_FOR_INFERENCE": True,
        "recorded_quantity": "recovery_1_summary_only",
        "seeds_used": SEEDS,
        "n_genomes": len(_genomes()),
        "n_runs_total": total,
        "environment": ENVIRONMENT,
        "interval": INTERVAL,
        "lesson": LESSON,
        "n_sustain": N_SUSTAIN,
        "n_censored": len(censored),
        "n_non_censored": len(non_censored),
        "censoring_rate": round(censoring_rate, 4) if censoring_rate is not None else None,
        "n_censored_at_ceiling": n_ceiling,
        "n_censored_at_floor": n_floor,
        "n_censored_other": n_other_censored,
        "median": round(median, 4) if median is not None else None,
        "q1": round(q1, 4) if q1 is not None else None,
        "q3": round(q3, 4) if q3 is not None else None,
        "max": round(maximum, 4) if maximum is not None else None,
        "interpretation": interpretation,
    }


if __name__ == "__main__":
    all_values = run_w01()
    report = build_report(all_values)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"W-01 report written to {OUTPUT_PATH}")
    print(json.dumps(report, indent=2, ensure_ascii=False))
