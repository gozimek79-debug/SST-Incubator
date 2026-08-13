"""PC-001 Pilot Final (PF-01/PF-02, zgloszenie audytora 2026-08-12): rozszerzenie
B4a-2 (execution_package_v0_11/runners/pilot_power_analysis_w2.py) o DRUGIE
srodowisko (pure_noise_world, K4) i DRUGA wielkosc mierzona (Spearman[0,60),
wczesne okno korelacji prediction<->input, K6) - z zachowaniem WSZYSTKICH
gwarancji mechanicznych B4a-2 (przechwycenie w pamieci, natychmiastowe
porzucenie trajektorii, zero save_to_file, zero importu funkcji przeliczajacych
podloge).

SEEDY: 1-15 (D-042, decyzja CTO) - KONSERWATYWNA DECYZJA PROJEKTOWA, NIE wynik
analizy. Piec bylo za malo (ANALIZA_WARIANCJI_PILOTA_2026-08-03.md, publications/) -
analiza wykazala niewystarczalnosc piatki, nie wyznaczyla piemastki jako
optymalnej. Rozlaczne z konfirmacja (od 1001).

PODLOGI: FROZEN_FLOOR_NOISE_WORLD i FROZEN_FLOOR_PURE_NOISE_WORLD z
pc_001_experiment_config.py - UZYWANE BEZPOSREDNIO, NIE przeliczane. Ten plik
CELOWO NIE importuje floor_at_tick/floor_profile/select_floor_model (test
gwarancyjny sprawdza brak tych importow dla OBU srodowisk, patrz
tests/test_pilot_final_guarantee.py).

SPEARMAN[0,60) (K6, publications/BEZPIECZENSTWO_POMIARU_recovery_spearman.md §3):
BEZPIECZNE wylacznie w oknie wczesnym - mierzy stan poczatkowy (sprzezenie
prediction<->input NA STARCIE), nie wynik K6 (sprzezenie PRZEZ CALY przebieg).
Zapisywana WYLACZNIE jedna wartosc (rho) na przebieg z okna [0,60) - zero okna
poznego, zero calego okna [0,300), zero roznicy miedzy oknami. recovery_i
(K3b) NIE jest mierzone - jest wynikiem, nie parametrem (dokument bezpieczenstwa
§2, G-003 pkt 6) - patrz tez ZAKAZANE w docstringu B4a-2.
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
from clos_curriculum.laboratory.statistics import spearman_rho
from clos_kernel.snapshot_engine import SnapshotEngine
from clos_scientist.pc_001_experiment_config import (
    FROZEN_FLOOR_NOISE_WORLD, FROZEN_FLOOR_PURE_NOISE_WORLD, MIN_DENOMINATOR,
)
from clos_scientist.w2_endpoint import classify_run

PILOT_SEEDS = list(range(1, 16))  # 1-15 (D-042)
CONFIRMATORY_SEEDS_START = 1001
ENVIRONMENTS = ["noise_world", "pure_noise_world"]
LESSON = "L1.2"
W_EARLY_TICKS = 60
SPEARMAN_WINDOW = [0, 60]
MIN_NON_NONE_FOR_SUFFICIENT = 5
MIN_N_FOR_SPEARMAN = 3  # korelacja Spearmana wymaga n>=3 (df=n-2), statistics.py

# Uzyte BEZPOSREDNIO - NIE przeliczane tutaj (patrz docstring modulu).
FLOOR_BY_ENVIRONMENT: Dict[str, float] = {
    "noise_world": FROZEN_FLOOR_NOISE_WORLD["value"],
    "pure_noise_world": FROZEN_FLOOR_PURE_NOISE_WORLD["value"],
}
FLOOR_MODEL_BY_ENVIRONMENT: Dict[str, str] = {
    "noise_world": FROZEN_FLOOR_NOISE_WORLD["floor_model"],
    "pure_noise_world": FROZEN_FLOOR_PURE_NOISE_WORLD["floor_model"],
}

OUTPUT_PATH = REPO_ROOT / "reports" / "pilot" / "pilot_final.json"


def _genomes() -> List[Dict[str, Any]]:
    path = REPO_ROOT / "execution_package_v0_11" / "genomes" / "population.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["genomes"]


def _measure_run(genome: Dict[str, Any], seed: int, environment: str) -> Dict[str, Any]:
    """Uruchamia L1.2 RAZ, przechwytuje prediction_error/prediction/input z tickow
    [0, W_EARLY_TICKS) WYLACZNIE w pamieci, liczy W_early_red (podloga
    zamrozona dla danego srodowiska) i Spearman[0,60) (prediction vs input),
    porzuca cala trajektorie natychmiast po policzeniu dwoch skalarow."""
    captured_pe: List[Optional[float]] = []
    captured_pred: List[float] = []
    captured_input: List[float] = []
    original = SnapshotEngine.create_snapshot

    def spy(self, *args, **kwargs):
        snapshot = original(self, *args, **kwargs)
        if kwargs.get("tick", -1) < W_EARLY_TICKS:
            captured_pe.append(kwargs.get("prediction_error"))
            pred = kwargs.get("prediction")
            inp = kwargs.get("input")
            if pred is not None and inp is not None:
                captured_pred.append(pred)
                captured_input.append(inp)
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

    floor_value = FLOOR_BY_ENVIRONMENT[environment]
    non_none = [v for v in captured_pe if v is not None]
    if len(non_none) < MIN_NON_NONE_FOR_SUFFICIENT:
        w_early_red = None
    else:
        reduced = [max(0.0, v - floor_value) for v in non_none]
        w_early_red = sum(reduced) / len(reduced)
    status = classify_run(w_early_red)

    spearman_early_rho = None
    if len(captured_pred) >= MIN_N_FOR_SPEARMAN:
        result = spearman_rho(captured_pred, captured_input)
        if result.get("computable") and result.get("rho") is not None:
            spearman_early_rho = round(result["rho"], 6)

    return {
        "w_early_red": round(w_early_red, 6) if w_early_red is not None else None,
        "status": status,
        "n_non_none": len(non_none),
        "spearman_early_rho": spearman_early_rho,
        "spearman_early_n": len(captured_pred),
    }


def run_pilot() -> List[Dict[str, Any]]:
    genomes = _genomes()
    records: List[Dict[str, Any]] = []
    for environment in ENVIRONMENTS:
        for genome in genomes:
            for seed in PILOT_SEEDS:
                r = _measure_run(genome, seed, environment)
                records.append({
                    "genome_id": genome["genome_id"],
                    "environment": environment,
                    "seed": seed,
                    "w_early_red": r["w_early_red"],
                    "spearman_early_rho": r["spearman_early_rho"],
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


def _environment_summary(records: List[Dict[str, Any]], environment: str) -> Dict[str, Any]:
    env_records = [r for r in records if r["environment"] == environment]
    valid_values = [r["w_early_red"] for r in env_records if r["status"] == "VALID"]
    spearman_values = [r["spearman_early_rho"] for r in env_records if r["spearman_early_rho"] is not None]
    floor_limited = [r for r in env_records if r["status"] == "FLOOR_LIMITED"]
    insufficient = [r for r in env_records if r["status"] == "INSUFFICIENT_DATA"]
    n_total = len(env_records)
    return {
        "floor_used": FLOOR_BY_ENVIRONMENT[environment],
        "floor_model": FLOOR_MODEL_BY_ENVIRONMENT[environment],
        "n_runs_total": n_total,
        "n_valid": len(valid_values),
        "n_floor_limited": len(floor_limited),
        "n_insufficient_data": len(insufficient),
        "floor_limited_fraction": round(len(floor_limited) / n_total, 4) if n_total else None,
        "floor_limited_runs": [{"genome_id": r["genome_id"], "seed": r["seed"]} for r in floor_limited],
        "insufficient_data_runs": [{"genome_id": r["genome_id"], "seed": r["seed"]} for r in insufficient],
        "w_early_red_distribution_valid_only": _quantile_stats(valid_values),
        "spearman_early_distribution": _quantile_stats(spearman_values),
    }


def build_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid_values = [r["w_early_red"] for r in records if r["status"] == "VALID"]
    floor_limited = [r for r in records if r["status"] == "FLOOR_LIMITED"]
    insufficient = [r for r in records if r["status"] == "INSUFFICIENT_DATA"]

    return {
        "purpose": "power_analysis_only",
        "NEVER_FOR_INFERENCE": True,
        "recorded_quantity": "W_early_red_and_spearman_early_only",
        "seeds_used": PILOT_SEEDS,
        "confirmatory_seeds_start": CONFIRMATORY_SEEDS_START,
        "environment": ENVIRONMENTS,
        "lesson": LESSON,
        "w_early_tick_window": [0, W_EARLY_TICKS],
        "spearman_early_window": SPEARMAN_WINDOW,
        "min_denominator": MIN_DENOMINATOR,
        "n_genomes": len(_genomes()),
        # Pola zbiorcze (obowiazkowe jak w B4a-2) - suma po obu srodowiskach,
        # sanity-check przeciw "by_environment" ponizej (PF-02: NIE agregowac
        # jako JEDYNE zrodlo - dwie rozne wielkosci o roznym znaczeniu).
        "n_runs_total": len(records),
        "n_valid": len(valid_values),
        "n_floor_limited": len(floor_limited),
        "n_insufficient_data": len(insufficient),
        "by_environment": {env: _environment_summary(records, env) for env in ENVIRONMENTS},
        "runs": [
            {"genome_id": r["genome_id"], "environment": r["environment"], "seed": r["seed"],
             "w_early_red": r["w_early_red"], "spearman_early_rho": r["spearman_early_rho"],
             "status": r["status"]}
            for r in records
        ],
        "supersedes": (
            "pilot_W_early_red_noise_world.json (B4a-2, jedno srodowisko "
            "noise_world, bez Spearman[0,60))"
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    all_records = run_pilot()
    report = build_report(all_records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Pilot Final report written to {OUTPUT_PATH}")
