"""Population Validation Runner (SPRINT_v0.10.1.md P3).

Uruchamia probke 23 genomow (clos_curriculum.laboratory.population) x
srodowiska x seedy, DOKLADNIE wg publications/preregistration_v0_10_1_population.json
(metrology, environments, sample_size). Cel: znalezc GRANICE, nie potwierdzic
sukces (zasada nadrzedna SPRINT_v0.10.1.md) - degeneracje/cenzury/FRAGILE sa
raportowane z tym samym naciskiem co ROBUST.

Zero zmiany Execution: wywoluje WYLACZNIE run_pattern_echo()/run_shock_recovery()
z (juz zregresowanym, patrz tests/test_genome_params_regression.py) parametrem
genome_params. Zero dotkniecia clos_brain/, clos_kernel/, genome/, birth/.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clos_academy.lesson_L1_1 import run_pattern_echo
from clos_academy.lesson_L1_2 import run_shock_recovery
from clos_curriculum.laboratory.population import generate_population, POPULATION_SAMPLING_SEED
from clos_curriculum.laboratory.statistics import compute_ci95, welch_t_test, benjamini_hochberg

SEEDS = list(range(1, 11))
VALIDITY_MIN_N_EFFECTIVE = 5   # preregistration_v0_10_1_population.json: metrology.validity_threshold_per_genome_per_metric
ROBUST_THRESHOLD = 0.8         # preregistration_v0_10_1_population.json: metrology.robustness_definition
FDR_Q = 0.05                   # preregistration_v0_10_1_population.json: metrology.multiple_comparisons_correction

LESSON_ENVIRONMENTS = {
    "L1.1": ["noise_world", "stable_world", "drift_world"],
    "L1.2": ["shock_world", "stable_world", "drift_world"],
}

L1_1_METRICS = {
    "primary_endpoint_value": "Working Memory (MAE@50)",  # SPRINT_v0.11.0.md P1: MSE->MAE, wartosc bez zmian
    "adaptation_tick": "Adaptation",
    "stability_score": "Stability",
    "mae_stimulus_phase": "Pattern Recognition",  # SPRINT_v0.11.0.md P1: bylo mse_stimulus_phase
    "memory_decay_rate": "Pattern Retention",
    "final_energy": "Final Energy Level",  # SPRINT_v0.11.0.md P1: bylo "Energy Efficiency" (blad kategorii, nie nazwy - patrz docs/ENERGY_EFFICIENCY_ONTOLOGY_DECISION.md), zmienna stanu fizjologicznego nie zdolnosc poznawcza
}
L1_2_METRICS = {
    "primary_endpoint_value": "Homeostatic Resilience (recovery_time)",
    "adaptation_tick": "Adaptation",
    "stability_score": "Stability",
    "final_energy": "Final Energy Level",  # SPRINT_v0.11.0.md P1: bylo "Energy Efficiency" (blad kategorii, nie nazwy - patrz docs/ENERGY_EFFICIENCY_ONTOLOGY_DECISION.md), zmienna stanu fizjologicznego nie zdolnosc poznawcza
}


def _git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _run_l1_1(genome: Dict[str, Any], environment: str) -> List[Dict[str, Any]]:
    return [
        run_pattern_echo(genome_preset=genome["genome_preset"], seed=seed, scenario=environment,
                          genome_params=genome["genome_params"], genome_label=genome["genome_id"])
        for seed in SEEDS
    ]


def _run_l1_2(genome: Dict[str, Any], environment: str) -> List[Dict[str, Any]]:
    return [
        run_shock_recovery(genome_preset=genome["genome_preset"], seed=seed, scenario=environment,
                            genome_params=genome["genome_params"], genome_label=genome["genome_id"])
        for seed in SEEDS
    ]


def _extract_metric_values(results: List[Dict[str, Any]], metric_key: str) -> Optional[List[float]]:
    """None = metryka nie istnieje w tym kontekscie (np. primary_endpoint poza
    scenario=='shock_world' - odkrycie P2, name-gate). Cenzurowane wartosci
    (primary_endpoint.censored=True) sa POMIJANE, nie liczone jako 0."""
    values = []
    for r in results:
        if metric_key == "primary_endpoint_value":
            pe = r.get("primary_endpoint")
            if pe is None:
                return None
            if pe.get("censored"):
                continue
            values.append(pe["value"])
        else:
            if metric_key not in r:
                return None
            values.append(r[metric_key])
    return values


def _validity(stats: Dict[str, Any]) -> bool:
    return bool(stats["ci95_valid"]) and stats["n_effective"] >= VALIDITY_MIN_N_EFFECTIVE


def analyze_metric(per_genome_results: Dict[str, List[Dict[str, Any]]], metric_key: str) -> Dict[str, Any]:
    per_genome_stats: Dict[str, Any] = {}
    raw_values_by_genome: Dict[str, List[float]] = {}

    for genome_id, results in per_genome_results.items():
        values = _extract_metric_values(results, metric_key)
        if values is None:
            continue
        stats = compute_ci95(values)
        stats["valid_population"] = _validity(stats)
        stats["n_available"] = len(values)
        per_genome_stats[genome_id] = stats
        raw_values_by_genome[genome_id] = values

    if not per_genome_stats:
        return {
            "status": "not_applicable",
            "reason": "metryka nie istnieje w tym kontekscie (pole gated na inna nazwe scenariusza - patrz SPRINT_v0.10.1.md P2 odkrycie)",
        }

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

    return {
        "status": "measured",
        "n_genomes_total": n_total,
        "n_genomes_valid": n_valid,
        "valid_rate": valid_rate,
        "classification": classification,
        "per_genome": per_genome_stats,
        "pairwise_comparisons": {
            "n_pairs": len(pairs),
            "n_pairs_computable": len(computable_p),
            "n_raw_significant_p_lt_0_05": n_raw_sig,
            "n_fdr_significant_q_0_05": n_fdr_sig,
            "details": pairs,
        },
    }


def run_population_validation(verbose: bool = True) -> Dict[str, Any]:
    population = generate_population()
    report: Dict[str, Any] = {
        "study_id": "v0.10.1_population_validation",
        "dataset_status": ("Exploratory Dataset v0.10 (SPRINT_v0.11.0.md P0) - n=10/genom, moc statystyczna "
                            "niska po korekcie na wielokrotne porownania dla wiekszosci osi. Nie poprawiane, "
                            "nie wycofywane. Power/Confirmatory validity: PENDING do re-run zatwierdzonego "
                            "przez CTO. Patrz publications/preregistration_v0_11_0_power_reproduction.json."),
        "preregistration": "publications/preregistration_v0_10_1_population.json",
        "population_sampling_seed": POPULATION_SAMPLING_SEED,
        "git_commit": _git_commit(),
        "n_genomes": len(population),
        "seeds_per_genome_per_environment": SEEDS,
        "validity_min_n_effective": VALIDITY_MIN_N_EFFECTIVE,
        "robust_threshold": ROBUST_THRESHOLD,
        "fdr_q": FDR_Q,
        "genomes": population,
        "lessons": {},
    }

    plan = {
        "L1.1": (_run_l1_1, L1_1_METRICS, LESSON_ENVIRONMENTS["L1.1"]),
        "L1.2": (_run_l1_2, L1_2_METRICS, LESSON_ENVIRONMENTS["L1.2"]),
    }

    for lesson_id, (runner, metrics, envs) in plan.items():
        lesson_report: Dict[str, Any] = {}
        for env in envs:
            if verbose:
                print(f"  {lesson_id} / {env} ({len(population)} genomow x {len(SEEDS)} seedow)...")
            per_genome_results = {g["genome_id"]: runner(g, env) for g in population}
            env_report = {label: analyze_metric(per_genome_results, key) for key, label in metrics.items()}
            lesson_report[env] = env_report
            if verbose:
                for label, res in env_report.items():
                    if res["status"] == "measured":
                        print(f"    {label}: {res['classification']} (valid_rate={res['valid_rate']})")
                    else:
                        print(f"    {label}: {res['status']}")
        report["lessons"][lesson_id] = lesson_report

    return report


def write_population_report(output_path: str = "reports/population/population_validation_v0_10_1.json") -> Path:
    report = run_population_validation()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    return path


if __name__ == "__main__":
    out = write_population_report()
    print(f"\nRaport: {out}")
