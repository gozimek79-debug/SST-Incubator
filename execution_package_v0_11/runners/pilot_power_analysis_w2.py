"""PC-001 B4a-2: PONOWNY pilot pod W2 (D-008/D-018/D-019, NOTATKA_B4_ANALIZA_MOCY,
SPECYFIKACJA_W2). Zastepuje pilot_power_analysis.py (B4a), ktory mierzyl W_early
SUROWE - W2 wymaga W_early_red = mean(max(0, PE(t)-floor)). Poprzednie 230
przebiegow NIE jest strata (wykryly blad projektu shock_world) - artefakty
zostaja w repo (Aneks 3 SS8), ten runner ich nie dotyka ani nie usuwa.

Srodowisko: WYLACZNIE noise_world (Primary Endpoint wg D-015 pkt 3 - shock_world
jest teraz srodowiskiem K3, nie Primary, wiec pilot pod Primary go nie obejmuje).

Ten plik NIE wchodzi do CRITICAL_FILES_PC_001 (ten sam scoping co
pilot_power_analysis.py z B4a - dostarcza dane WEJSCIOWE do decyzji projektowej
o liczbie seedow, nie jest kodem STOSOWANYM przy kazdym przebiegu eksperymentu).

GWARANCJA MECHANICZNA (identyczna jak B4a, D-008 pkt 1): _w_early_red_for_run()
przechwytuje prediction_error z tickow [0, W_EARLY_TICKS) WYLACZNIE w pamieci
(monkeypatch SnapshotEngine.create_snapshot - ten sam wzorzec co
tests/test_observer_removability.py i pilot_power_analysis.py), liczy
W_early_red w pamieci, i porzuca cala trajektorie natychmiast. Zero
save_to_file(), zero W_late, zero bety/trendu, zero jakiejkolwiek wielkosci
mowiacej CZY prediction_error spada - efekt (wielkosc redukcji) pochodzi
WYLACZNIE z prerejestracji (20%, Aneks 1), nigdy z pilota (moc retrospektywna
to blad, ktory ten projekt swiadomie usunal, patrz P0/power_n10).

PODLOGA: FROZEN_FLOOR_NOISE_WORLD z pc_001_experiment_config.py - UZYWANA
BEZPOSREDNIO (FLOOR_VALUE ponizej), NIE przeliczana. Ten plik CELOWO NIE
importuje floor_at_tick/floor_profile/select_floor_model (clos_world/
floor_model.py, clos_scientist/w2_endpoint.py::select_floor_model) - gdyby
przeliczal podloge sam, przestalby uzywac wartosci zamrozonej (test
gwarancyjny sprawdza brak tych importow, patrz
tests/test_pilot_w2_power_analysis_guarantee.py)."""

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
from clos_scientist.pc_001_experiment_config import FROZEN_FLOOR_NOISE_WORLD, MIN_DENOMINATOR
from clos_scientist.w2_endpoint import classify_run

PILOT_SEEDS = [1, 2, 3, 4, 5]
CONFIRMATORY_SEEDS_START = 1001
ENVIRONMENT = "noise_world"
LESSON = "L1.2"
W_EARLY_TICKS = 60
MIN_NON_NONE_FOR_SUFFICIENT = 5

# Uzyta BEZPOSREDNIO - NIE przeliczana tutaj (patrz docstring modulu).
FLOOR_VALUE = FROZEN_FLOOR_NOISE_WORLD["value"]

OUTPUT_PATH = REPO_ROOT / "reports" / "pilot" / "pilot_W_early_red_noise_world.json"


def _genomes() -> List[Dict[str, Any]]:
    path = REPO_ROOT / "execution_package_v0_11" / "genomes" / "population.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["genomes"]


def _w_early_red_for_run(genome: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """Uruchamia L1.2 RAZ na noise_world, przechwytuje prediction_error z tickow
    [0, W_EARLY_TICKS) WYLACZNIE w pamieci, liczy W_early_red z FROZEN_FLOOR
    (zamrozona, nie przeliczana), i porzuca wszystko poza jedna liczba +
    klasyfikacje (VALID/FLOOR_LIMITED/INSUFFICIENT_DATA, z w2_endpoint.classify_run
    - ten sam kod co uzyje eksperyment konfirmacyjny, zero duplikacji progow)."""
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
            genome_preset=genome["genome_preset"], seed=seed, scenario=ENVIRONMENT,
            genome_params=genome["genome_params"], genome_label=genome["genome_id"],
            observe=True,
        )
    finally:
        SnapshotEngine.create_snapshot = original

    non_none = [v for v in captured if v is not None]
    if len(non_none) < MIN_NON_NONE_FOR_SUFFICIENT:
        w_early_red = None
    else:
        reduced = [max(0.0, v - FLOOR_VALUE) for v in non_none]
        w_early_red = sum(reduced) / len(reduced)

    status = classify_run(w_early_red)
    return {
        "w_early_red": round(w_early_red, 6) if w_early_red is not None else None,
        "status": status,
        "n_non_none": len(non_none),
    }


def run_pilot() -> List[Dict[str, Any]]:
    genomes = _genomes()
    records: List[Dict[str, Any]] = []
    for genome in genomes:
        for seed in PILOT_SEEDS:
            r = _w_early_red_for_run(genome, seed)
            records.append({
                "genome_id": genome["genome_id"],
                "environment": ENVIRONMENT,
                "seed": seed,
                "w_early_red": r["w_early_red"],
                "status": r["status"],
            })
    return records


def _quantile_stats(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"median": None, "q1": None, "q3": None, "min": None, "max": None}
    sv = sorted(values)
    return {
        "median": round(py_statistics.median(sv), 6),
        "q1": round(py_statistics.quantiles(sv, n=4)[0], 6) if len(sv) >= 2 else None,
        "q3": round(py_statistics.quantiles(sv, n=4)[2], 6) if len(sv) >= 2 else None,
        "min": round(min(sv), 6),
        "max": round(max(sv), 6),
    }


def build_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid_values = [r["w_early_red"] for r in records if r["status"] == "VALID"]
    floor_limited = [r for r in records if r["status"] == "FLOOR_LIMITED"]
    insufficient = [r for r in records if r["status"] == "INSUFFICIENT_DATA"]

    per_genome = {}
    for genome_id in sorted(set(r["genome_id"] for r in records)):
        g_vals = [r["w_early_red"] for r in records
                  if r["genome_id"] == genome_id and r["w_early_red"] is not None]
        per_genome[genome_id] = _quantile_stats(g_vals)

    return {
        "purpose": "power_analysis_only",
        "NEVER_FOR_INFERENCE": True,
        "recorded_quantity": "W_early_red_only",
        "seeds_used": PILOT_SEEDS,
        "confirmatory_seeds_start": CONFIRMATORY_SEEDS_START,
        "floor_used": FLOOR_VALUE,
        "floor_model": FROZEN_FLOOR_NOISE_WORLD["floor_model"],
        "environment": ENVIRONMENT,
        "lesson": LESSON,
        "w_early_tick_window": [0, W_EARLY_TICKS],
        "min_denominator": MIN_DENOMINATOR,
        "n_genomes": len(_genomes()),
        "n_runs_total": len(records),
        "n_valid": len(valid_values),
        "n_floor_limited": len(floor_limited),
        "n_insufficient_data": len(insufficient),
        "floor_limited_runs": [{"genome_id": r["genome_id"], "seed": r["seed"]} for r in floor_limited],
        "insufficient_data_runs": [{"genome_id": r["genome_id"], "seed": r["seed"]} for r in insufficient],
        "overall_distribution_valid_only": _quantile_stats(valid_values),
        "by_genome": per_genome,
        "runs": [
            {"genome_id": r["genome_id"], "environment": r["environment"], "seed": r["seed"],
             "w_early_red": r["w_early_red"], "status": r["status"]}
            for r in records
        ],
        "supersedes": "pilot_PE_distribution_W_early.json (B4a, mierzyl PE surowe)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    all_records = run_pilot()
    report = build_report(all_records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Pilot report written to {OUTPUT_PATH}")
