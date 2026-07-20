"""Agregacja SUROWYCH danych z pelnego re-runu konfirmacyjnego (12765 runow)
do reports/population/population_validation_v0_11_0_0.json.

WAZNE (Final Audit Gate, 2026-07-19): ten skrypt NIE interpretuje wynikow.
Liczy WYLACZNIE mechaniczne, ustalone-z-gory statystyki opisowe:
  - per-genom CI95 (compute_ci95 - juz istniejaca funkcja, nie duplikowana)
  - klasyfikacja ROBUST/FRAGILE (fakt o jakosci pomiaru - ten sam prog 80%
    co w clos_academy/population_validation.py, NIE nowa decyzja)
  - parowe testy Welch + korekta BH-FDR (q=0.05) - MECHANIKA, ta sama
    metoda co w istniejacym pipeline'ie populacyjnym
  - omnibus ANOVA (cohens_f_anova) per komorka - SUROWY effect size,
    input do oceny mocy, NIE sam werdykt o mocy
ZERO statusow rekomendacji (VALIDATED/EXPERIMENTAL/INSUFFICIENT_POWER/...) -
to nalezy do audytora (docs/METRIC_STATUS_TABLE.md byl zbudowany na
Exploratory Dataset v0.10, NIE na tym pliku).

NIE dotyka reports/population/population_validation_v0_10_1.json
(Exploratory Dataset v0.10, zamrozone, nietykane) - pisze do NOWEGO pliku.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_ROOT = REPO_ROOT / "execution_package_v0_11"
sys.path.insert(0, str(REPO_ROOT))

from clos_curriculum.laboratory.statistics import compute_ci95, welch_t_test, benjamini_hochberg, cohens_f_anova

VALIDITY_MIN_N_EFFECTIVE = 5
ROBUST_THRESHOLD = 0.8
FDR_Q = 0.05
FDR_ALPHA_OMNIBUS_CORRECTED = 0.05 / 9  # aneks 2026-07-19, warunek_2 - NIE 0.05/21

L1_1_METRICS = {
    "primary_endpoint_value": "Working Memory (MAE@50)",
    "adaptation_tick": "Adaptation",
    "stability_score": "Stability",
    "mae_stimulus_phase": "Pattern Recognition",
    "memory_decay_rate": "Pattern Retention",
    "final_energy": "Final Energy Level",
}
L1_2_METRICS = {
    "primary_endpoint_value": "Homeostatic Resilience (recovery_time)",
    "adaptation_tick": "Adaptation",
    "stability_score": "Stability",
    "final_energy": "Final Energy Level",
}


def _git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def load_raw_records(results_path: Path) -> List[Dict[str, Any]]:
    records = []
    with open(results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _extract_metric_values(records: List[Dict[str, Any]], metric_key: str) -> Any:
    values = []
    for r in records:
        m = r["metrics"]
        if metric_key == "primary_endpoint_value":
            pe = m.get("primary_endpoint")
            if pe is None:
                return None
            if pe.get("censored"):
                continue
            values.append(pe["value"])
        else:
            if metric_key not in m:
                return None
            values.append(m[metric_key])
    return values


def _validity(stats: Dict[str, Any]) -> bool:
    return bool(stats["ci95_valid"]) and stats["n_effective"] >= VALIDITY_MIN_N_EFFECTIVE


def analyze_metric(per_genome_records: Dict[str, List[Dict[str, Any]]], metric_key: str) -> Dict[str, Any]:
    per_genome_stats: Dict[str, Any] = {}
    raw_values_by_genome: Dict[str, List[float]] = {}

    for genome_id, records in per_genome_records.items():
        values = _extract_metric_values(records, metric_key)
        if values is None or not values:
            continue
        stats = compute_ci95(values)
        stats["valid_population"] = _validity(stats)
        stats["n_available"] = len(values)
        per_genome_stats[genome_id] = stats
        raw_values_by_genome[genome_id] = values

    if not per_genome_stats:
        return {"status": "not_applicable", "reason": "brak danych dla tej (metryka, srodowisko) - konstrukt nie ma zastosowania lub wszystkie runy ucenzurowane"}

    n_total = len(per_genome_stats)
    n_valid = sum(1 for s in per_genome_stats.values() if s["valid_population"])
    valid_rate = round(n_valid / n_total, 4)
    classification = "GENOME-ROBUST" if valid_rate >= ROBUST_THRESHOLD else "GENOME-FRAGILE"

    valid_ids = [gid for gid, s in per_genome_stats.items() if s["valid_population"]]
    pairs = []
    for i in range(len(valid_ids)):
        for j in range(i + 1, len(valid_ids)):
            a_id, b_id = valid_ids[i], valid_ids[j]
            wt = welch_t_test(raw_values_by_genome[a_id], raw_values_by_genome[b_id])
            pairs.append({"genome_a": a_id, "genome_b": b_id, **wt})

    computable_p = [p["p_value"] for p in pairs if p["computable"]]
    fdr_flags = benjamini_hochberg(computable_p, q=FDR_Q) if computable_p else []
    idx = 0
    n_raw_sig, n_fdr_sig = 0, 0
    for p in pairs:
        if p["computable"]:
            p["raw_significant_p_lt_0_05"] = p["p_value"] < 0.05
            p["fdr_significant"] = fdr_flags[idx]
            idx += 1
            n_raw_sig += int(p["raw_significant_p_lt_0_05"])
            n_fdr_sig += int(p["fdr_significant"])
        else:
            p["raw_significant_p_lt_0_05"] = None
            p["fdr_significant"] = None

    means = [s["mean"] for s in per_genome_stats.values()]
    stds = [s["std"] for s in per_genome_stats.values()]
    ns = [s["n_available"] for s in per_genome_stats.values()]
    f_result = cohens_f_anova(means, stds, ns)

    return {
        "status": "measured",
        "n_genomes_total": n_total,
        "n_genomes_valid": n_valid,
        "valid_rate": valid_rate,
        "classification": classification,
        "per_genome": per_genome_stats,
        "omnibus_anova_raw": {
            "note": "SUROWY effect size (input do oceny mocy przez audytora) - NIE werdykt o mocy/confirmatory validity.",
            **f_result,
            "alpha_corrected_9_tests": FDR_ALPHA_OMNIBUS_CORRECTED,
        },
        "pairwise_comparisons": {
            "n_pairs": len(pairs),
            "n_pairs_computable": len(computable_p),
            "n_raw_significant_p_lt_0_05": n_raw_sig,
            "n_fdr_significant_q_0_05": n_fdr_sig,
            "details": pairs,
        },
    }


def build_report(results_path: Path) -> Dict[str, Any]:
    records = load_raw_records(results_path)

    report: Dict[str, Any] = {
        "study_id": "v0.11.0_confirmatory_rerun",
        "dataset_status": (
            "CONFIRMATORY (NIE Exploratory) - re-run autoryzowany przez Final Audit Gate "
            "(audytor, klon 5098e1f, 2026-07-19). N=185/93/92 wg experiment_manifest.json. "
            "ZERO interpretacji Power/Confirmatory w tym pliku - to zadanie audytora, potem "
            "red team wobec wnioskow. Ten plik NIE zastepuje ani nie nadpisuje Exploratory "
            "Dataset v0.10 (reports/population/population_validation_v0_10_1.json)."
        ),
        "manifest": "execution_package_v0_11/experiment_manifest.json",
        "hard_halt_baseline": "cca6f8f933a73c1ff9ca9a3e482b966fef4c430ee50f3ed6c35137d3ab8ec935",
        "git_commit": _git_commit(),
        "n_raw_records": len(records),
        "fdr_correction_omnibus": {
            "n_real_testable_cells": 9,
            "alpha": FDR_ALPHA_OMNIBUS_CORRECTED,
            "source": "publications/preregistration_v0_11_0_ANEKS_2026-07-19_run_count_i_fdr.json",
        },
        "lessons": {},
    }

    plan = {
        "L1.1": (L1_1_METRICS, ["noise_world", "stable_world"]),
        "L1.2": (L1_2_METRICS, ["shock_world", "stable_world"]),
    }

    for lesson_id, (metrics, envs) in plan.items():
        lesson_report: Dict[str, Any] = {}
        for env in envs:
            env_records = [r for r in records if r["lesson"] == lesson_id and r["environment"] == env]
            per_genome_records: Dict[str, List[Dict[str, Any]]] = {}
            for r in env_records:
                per_genome_records.setdefault(r["genome"], []).append(r)
            env_report = {label: analyze_metric(per_genome_records, key) for key, label in metrics.items()}
            lesson_report[env] = env_report
        report["lessons"][lesson_id] = lesson_report

    return report


def write_report(results_path: Path = None, out_path: Path = None) -> Path:
    results_path = results_path or (PACKAGE_ROOT / "results" / "full_rerun_results.jsonl")
    out_path = out_path or (REPO_ROOT / "reports" / "population" / "population_validation_v0_11_0.json")
    report = build_report(results_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    return out_path


if __name__ == "__main__":
    path = write_report()
    print(f"Raport (SUROWE dane, bez interpretacji): {path}")
