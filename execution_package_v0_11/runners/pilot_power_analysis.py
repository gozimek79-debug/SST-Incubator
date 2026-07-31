"""PC-001 B4a: pilot analizy mocy (D-008, NOTATKA_B4_ANALIZA_MOCY_2026-07-28.md
sekcja 2-3). Ten plik NIE wchodzi do CRITICAL_FILES_PC_001 (decyzja CTO
scoping'u KROK 1: tylko sama notatka metodologiczna wchodzi do rejestru,
nie ten runner - lista rosnie z 30 do 31, nie 32).

GWARANCJA MECHANICZNA (D-008 pkt 1, nie deklaratywna): ten runner NIGDY nie
zapisuje snapshotow ani pelnej trajektorii prediction_error na dysk, NIGDY
nie liczy W_late (ticki 240-299), nachylenia/trendu, ani zadnej wielkosci
mowiacej CZY prediction_error spada. Jedyna wartosc, ktora opuszcza funkcje
_w_early_for_run() to POJEDYNCZY float (W_early) albo None - pelna trajektoria
per-tick istnieje WYLACZNIE w lokalnej liscie `captured` wewnatrz tej jednej
funkcji i jest odrzucana natychmiast po policzeniu sredniej. Zero wywolan
kernel.snapshot_engine.save_to_file() - ani tutaj, ani w run_shock_recovery()
(zweryfikowane grepem: lesson_L1_2.py nigdy nie wola save_to_file()).

Wielkosc efektu (redukcja 20%) NIE jest tu nigdzie uzywana ani liczona -
przynalezy do prerejestracji (Aneks 1), nie do pilota (D-008 pkt 1, "pilot nie
moze zobaczyc efektu").
"""

import json
import statistics as py_statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from clos_academy.lesson_L1_2 import run_shock_recovery
from clos_kernel.snapshot_engine import SnapshotEngine

# D-008 pkt 5: rozdzielnosc mechaniczna seedow pilota od eksperymentu
# konfirmacyjnego - te dwa zbiory NIE MOGA nachodzic.
PILOT_SEEDS = [1, 2, 3, 4, 5]
CONFIRMATORY_SEEDS_START = 1001
assert max(PILOT_SEEDS) < CONFIRMATORY_SEEDS_START, (
    "PILOT_SEEDS zachodzi na zakres konfirmacyjny - pilot skazilby eksperyment doslownie"
)

ENVIRONMENTS = ["shock_world", "pure_noise_world"]  # NIE stable_world (D-005 pkt 4)
LESSON = "L1.2"
W_EARLY_TICKS = 60  # pierwsze 20% z 300 tickow (TICKS_TOTAL, lesson_L1_2.py)
MIN_NON_NONE_FOR_SUFFICIENT = 5

OUTPUT_PATH = REPO_ROOT / "reports" / "pilot" / "pilot_PE_distribution_W_early.json"


def _genomes() -> List[Dict[str, Any]]:
    path = REPO_ROOT / "execution_package_v0_11" / "genomes" / "population.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["genomes"]


def _w_early_for_run(genome: Dict[str, Any], seed: int, environment: str) -> Dict[str, Any]:
    """Uruchamia L1.2 RAZ. Przechwytuje prediction_error z tickow
    [0, W_EARLY_TICKS) WYLACZNIE w pamieci procesu (monkeypatch
    SnapshotEngine.create_snapshot - identyczny wzorzec jak
    tests/test_observer_removability.py::_capture_snapshot_calls), liczy
    srednia, i NATYCHMIAST porzuca cala liste `captured` wychodzac z tej
    funkcji - zwraca WYLACZNIE {"w_early": float|None, "status": str,
    "n_non_none": int}."""
    captured: List[Optional[float]] = []
    original = SnapshotEngine.create_snapshot

    def spy(self, *args, **kwargs):
        snapshot = original(self, *args, **kwargs)
        if kwargs.get("tick", -1) < W_EARLY_TICKS:
            captured.append(kwargs.get("prediction_error"))
        return snapshot

    SnapshotEngine.create_snapshot = spy
    try:
        run_shock_recovery(
            genome_preset=genome["genome_preset"], seed=seed, scenario=environment,
            genome_params=genome["genome_params"], genome_label=genome["genome_id"],
            observe=True,
        )
    finally:
        SnapshotEngine.create_snapshot = original

    non_none = [v for v in captured if v is not None]
    # `captured`/`non_none` (pelna trajektoria) konczy zycie TUTAJ - ponizej
    # zwracany jest wylacznie skalar albo None.
    if len(non_none) < MIN_NON_NONE_FOR_SUFFICIENT:
        return {"w_early": None, "status": "INSUFFICIENT_DATA", "n_non_none": len(non_none)}
    w_early = sum(non_none) / len(non_none)
    return {"w_early": round(w_early, 6), "status": "OK", "n_non_none": len(non_none)}


def run_pilot() -> List[Dict[str, Any]]:
    genomes = _genomes()
    records = []
    for genome in genomes:
        for environment in ENVIRONMENTS:
            for seed in PILOT_SEEDS:
                r = _w_early_for_run(genome, seed, environment)
                records.append({
                    "genome_id": genome["genome_id"],
                    "environment": environment,
                    "seed": seed,
                    "w_early": r["w_early"],
                    "status": r["status"],
                })
    return records


def _quantile_stats(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"median": None, "q1": None, "q3": None, "min": None, "max": None, "n": 0}
    sv = sorted(values)
    stats = {"median": round(py_statistics.median(sv), 6), "min": round(min(sv), 6),
             "max": round(max(sv), 6), "n": len(sv)}
    if len(sv) >= 2:
        q = py_statistics.quantiles(sv, n=4)
        stats["q1"] = round(q[0], 6)
        stats["q3"] = round(q[2], 6)
    else:
        stats["q1"] = None
        stats["q3"] = None
    return stats


def build_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    ok_values = [r["w_early"] for r in records if r["status"] == "OK"]
    insufficient = [r for r in records if r["status"] == "INSUFFICIENT_DATA"]

    per_env = {
        env: _quantile_stats([r["w_early"] for r in records
                               if r["environment"] == env and r["status"] == "OK"])
        for env in ENVIRONMENTS
    }
    per_genome = {
        gid: _quantile_stats([r["w_early"] for r in records
                              if r["genome_id"] == gid and r["status"] == "OK"])
        for gid in sorted({r["genome_id"] for r in records})
    }

    return {
        "purpose": "power_analysis_only",
        "NEVER_FOR_INFERENCE": True,
        "recorded_quantity": "W_early_only",
        "seeds_used": PILOT_SEEDS,
        "confirmatory_seeds_start": CONFIRMATORY_SEEDS_START,
        "lesson": LESSON,
        "environments": ENVIRONMENTS,
        "w_early_tick_window": [0, W_EARLY_TICKS],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_genomes": len(_genomes()),
        "n_runs_total": len(records),
        "n_insufficient_data": len(insufficient),
        "insufficient_data_runs": [
            {"genome_id": r["genome_id"], "environment": r["environment"], "seed": r["seed"]}
            for r in insufficient
        ],
        "overall_distribution": _quantile_stats(ok_values),
        "by_environment": per_env,
        "by_genome": per_genome,
        "runs": [
            {"genome_id": r["genome_id"], "environment": r["environment"],
             "seed": r["seed"], "w_early": r["w_early"], "status": r["status"]}
            for r in records
        ],
    }


def main() -> Path:
    records = run_pilot()
    report = build_report(records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = main()
    print(f"Pilot report written to {path}")
