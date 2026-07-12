"""Lesson L1.2 - Shock Recovery: Homeostatic Resilience (v0.9).

Primary experiment: scenario=shock_world (jednorazowa perturbacja, seed-zalezny
moment i wielkosc szoku). Control baseline: scenario=stable_world (WARIANT B -
bazowa stabilnosc/fraction_in_band, NIE recovery_time - w stable_world nie ma
zdarzenia do odzyskania).

Implementacja DOKLADNIE wg publications/preregistration_L1_2.json (v0.9.3,
BRAMKA zatwierdzona). Formuly (pasmo B, N, W, min_non_censored, prog
pre_shock_band_check=0.8) sa 1:1 z tego dokumentu - nie zmieniac tu bez
rewizji prerejestracji.
"""

import json, os, random, sys, logging
sys.path.insert(0, os.getcwd())

from genome.engine import GenomeEngine
from birth.engine import BirthEngine
from clos_kernel.kernel import Kernel
from clos_world.world_runtime import WorldRuntime
from clos_brain.brain_runtime import BrainRuntime
from clos_brain.tissue import BrainTissue
from clos_scientist.experiment import run_experiment
from clos_scientist.analyzer import detect_phases
from clos_kernel.event_bus import EventBus
from clos_curriculum.laboratory.statistics import compute_ci95, glass_delta, cohens_d

# Stale z preregistration_L1_2.json (recovery_time_definition) - nie zgadywane.
N_SUSTAIN = 10          # sustained_stabilization_condition
W_WINDOW = 150          # observation_window
TICKS_TOTAL = 300       # experiment_design.ticks_total
MIN_NON_CENSORED = 5    # censoring.min_non_censored
PRE_SHOCK_THRESHOLD = 0.8  # pre_shock_band_check.conditional_definition


def _build_tissue(genome_preset: str) -> BrainTissue:
    ge = GenomeEngine(); genome = ge.create_genome(genome_preset)
    be = BirthEngine(ge); brain_obj = be.create_from_genome(genome)
    return BrainTissue(
        brain_id=brain_obj.identity.brain_id, genome_id=genome.id,
        plasticity=brain_obj.expressed_genes.get("plasticity", 0.5),
        homeostasis_target=brain_obj.expressed_genes.get("homeostasis_target", 0.5),
        learning_rate=brain_obj.expressed_genes.get("learning_rate", 0.1),
        decay_rate=brain_obj.expressed_genes.get("decay_rate", 0.01),
        memory_capacity=int(brain_obj.expressed_genes.get("memory_capacity", 100)),
    )


def _shock_tick(seed: int) -> int:
    """t_shock - identyczna, pierwsza operacja RNG co wewnatrz shock_world."""
    return random.Random(seed).randint(20, 80)


def _in_band(value: float, band: tuple) -> bool:
    return band[0] <= value <= band[1]


def _sustained_window_in_band(entropy_by_tick: dict, start: int, n: int, band: tuple) -> bool:
    return all(_in_band(entropy_by_tick[start + i], band) for i in range(n))


def compute_recovery_time(entropy_by_tick: dict, t_shock: int, band: tuple,
                           n: int = N_SUSTAIN, w: int = W_WINDOW):
    """recovery_time(seed) = t* - t_shock, formula z preregistration_L1_2.json.

    Zwraca (value, censored). value=None gdy censored=True.
    """
    deadline = t_shock + w - n
    for t_star in range(t_shock, deadline + 1):
        if _sustained_window_in_band(entropy_by_tick, t_star, n, band):
            return t_star - t_shock, False
    return None, True


def pre_shock_in_band(entropy_by_tick: dict, t_shock: int, band: tuple, n: int = N_SUSTAIN) -> bool:
    """Okno [t_shock-n, t_shock-1] w calosci w pasmie B."""
    return _sustained_window_in_band(entropy_by_tick, t_shock - n, n, band)


def run_shock_recovery(genome_preset="default", seed=42, scenario="shock_world",
                        ticks_total=TICKS_TOTAL, observe=True):
    for name in ["BirthEngine", "root", ""]:
        logging.getLogger(name).setLevel(logging.ERROR)

    tissue = _build_tissue(genome_preset)
    band = (0.5 * tissue.homeostasis_target, tissue.homeostasis_target)

    kernel = Kernel(seed=seed); kernel.brain_id = tissue.brain_id
    kernel.max_ticks = ticks_total; kernel.initialize()
    world = WorldRuntime(); brain_rt = BrainRuntime()

    entropy_by_tick = {}
    telemetry = []

    for tick in range(ticks_total):
        signal = world.step(tick=tick, seed=seed, scenario=scenario)
        tissue = brain_rt.step(brain=tissue, sensory_input=signal, seed=seed, tick=tick)

        # Read-Only Observer (SPRINT_v0.10.md P1/P2) - patrz docs/spec_snapshot_observer.md.
        # Addytywne: czyta tissue juz obliczone powyzej, nie wplywa na entropy_by_tick/telemetry.
        if observe:
            kernel.snapshot_engine.create_snapshot(
                brain_id=tissue.brain_id, tick=tick, seed=seed,
                lifecycle_state="OBSERVED", brain_status="RUNNING",
                entropy=tissue.entropy, energy=tissue.energy,
                age=tick, step_counter=tick,
            )

        entropy_by_tick[tick] = tissue.entropy
        if tick % 5 == 0:
            telemetry.append({
                "tick": tick, "signal": round(signal, 6), "entropy": round(tissue.entropy, 6),
                "energy": round(tissue.energy, 6),
                "prediction": round(tissue.last_prediction, 6) if tissue.last_prediction is not None else None,
            })

    kernel.stop()
    snapshots = kernel.snapshot_engine.get_all_snapshots()
    result = run_experiment("shock_recovery", snapshots, EventBus().get_history())
    phases = detect_phases(snapshots)

    in_band_count = sum(1 for e in entropy_by_tick.values() if _in_band(e, band))
    fraction_in_band = round(in_band_count / ticks_total, 6)

    output = {
        "run_id": f"L1.2_{genome_preset}_s{seed}_{scenario}", "lesson": "L1.2",
        "genome": genome_preset, "seed": seed, "scenario": scenario,
        "homeostasis_band": {"low": round(band[0], 6), "high": round(band[1], 6)},
        "fraction_in_band": fraction_in_band,
        "stability_score": round(result.report.stability_score, 4),
        "adaptation_tick": phases.get("adaptation", 0),
        "final_energy": round(tissue.energy, 6), "final_entropy": round(tissue.entropy, 6),
        "memory_size": len(tissue.memory), "telemetry": telemetry,
    }

    if scenario == "shock_world":
        t_shock = _shock_tick(seed)
        rt_value, censored = compute_recovery_time(entropy_by_tick, t_shock, band)
        pre_in_band = pre_shock_in_band(entropy_by_tick, t_shock, band)
        output.update({
            "t_shock": t_shock,
            "primary_endpoint": {"metric": "recovery_time", "value": rt_value, "censored": censored},
            "pre_shock_in_band": pre_in_band,
        })

    return output


def _cohens_d_with_flag(group_a, group_b):
    """Jak clos_scientist.capability_analyzer._cohens_d_with_flag - jawna
    flaga computable, bo cohens_d() zwraca 0.0 zarowno dla 'nieobliczalne'
    jak i dla realnego zerowego efektu."""
    import math
    if len(group_a) < 2 or len(group_b) < 2:
        return {"cohens_d": None, "computable": False}
    mean_a = sum(group_a) / len(group_a); mean_b = sum(group_b) / len(group_b)
    var_a = sum((v - mean_a) ** 2 for v in group_a) / (len(group_a) - 1)
    var_b = sum((v - mean_b) ** 2 for v in group_b) / (len(group_b) - 1)
    pooled_std = math.sqrt((var_a + var_b) / 2)
    if pooled_std < 1e-9:
        return {"cohens_d": None, "computable": False}
    return {"cohens_d": round((mean_b - mean_a) / pooled_std, 6), "computable": True}


def run_lesson_L1_2():
    print("=" * 60)
    print("CLOS Cognitive Academy v0.9")
    print("Lesson L1.2: Shock Recovery - Homeostatic Resilience (shock_world)")
    print("=" * 60)

    genomes = ["default", "highly_plastic"]; seeds = list(range(1, 11))
    all_results = []       # scenario=shock_world (primary/experimental)
    baseline_results = []  # scenario=stable_world (control, wariant B)
    per_genome = {}

    for genome in genomes:
        print(f"\nGenome: {genome}")
        genome_results = []
        for seed in seeds:
            r = run_shock_recovery(genome_preset=genome, seed=seed, scenario="shock_world")
            genome_results.append(r); all_results.append(r)
            pe = r["primary_endpoint"]
            status = "CENSORED" if pe["censored"] else f"recovered@{pe['value']}"
            print(f"  seed {seed:2d}: t_shock={r['t_shock']:3d}  {status:16s} "
                  f"pre_shock_in_band={r['pre_shock_in_band']}")

        n_total = len(genome_results)
        non_censored = [r["primary_endpoint"]["value"] for r in genome_results if not r["primary_endpoint"]["censored"]]
        n_censored = n_total - len(non_censored)
        recovery_rate = round(len(non_censored) / n_total, 4)

        rt_stats = compute_ci95(non_censored)
        if len(non_censored) < MIN_NON_CENSORED:
            rt_stats = dict(rt_stats)
            rt_stats["ci95_valid"] = False
            rt_stats["interpretation"] = (
                f"nieucenzurowanych ({len(non_censored)}) < min_non_censored ({MIN_NON_CENSORED}) "
                "- CI95 wymuszone niewazne niezaleznie od compute_ci95"
            )

        pre_in_band_count = sum(1 for r in genome_results if r["pre_shock_in_band"])
        pre_shock_in_band_fraction = round(pre_in_band_count / n_total, 4)
        endpoint_path = "recovery_time (return)" if pre_shock_in_band_fraction >= PRE_SHOCK_THRESHOLD else "time_to_sustained_band (arrival)"

        adapt_vals = [r["adaptation_tick"] for r in genome_results]
        adapt_stats = compute_ci95(adapt_vals)
        stab_vals = [r["stability_score"] for r in genome_results]
        stab_stats = compute_ci95(stab_vals)

        print(f"  recovery_rate={recovery_rate}  n_censored={n_censored}/{n_total}  "
              f"mean_recovery_time={rt_stats['mean']}  n_effective={rt_stats['n_effective']}  "
              f"ci95_valid={rt_stats['ci95_valid']}")
        print(f"  pre_shock_in_band_fraction={pre_shock_in_band_fraction}  -> endpoint_path={endpoint_path}")
        print(f"  adaptation_tick: n_effective={adapt_stats['n_effective']} ci95_valid={adapt_stats['ci95_valid']}  "
              f"stability_score: n_effective={stab_stats['n_effective']} ci95_valid={stab_stats['ci95_valid']}")

        # Kontrola WARIANT B: stable_world raportuje stability_score + fraction_in_band, NIE recovery_time.
        control_results = [run_shock_recovery(genome_preset=genome, seed=seed, scenario="stable_world")
                            for seed in seeds]
        baseline_results.extend(control_results)
        control_stability_vals = [r["stability_score"] for r in control_results]
        control_stability_stats = compute_ci95(control_stability_vals)
        control_fraction_vals = [r["fraction_in_band"] for r in control_results]
        control_fraction_stats = compute_ci95(control_fraction_vals)

        gd_stability = glass_delta(control_stability_vals, stab_vals)
        print(f"  Control (stable_world): stability_score mean={control_stability_stats['mean']} "
              f"(deterministic={control_stability_stats['deterministic']})")
        if gd_stability.get("computable"):
            print(f"  Glass's delta stability_score (shock vs stable): {gd_stability['delta']:.4f}")
        else:
            print(f"  Glass's delta stability_score: not computable ({gd_stability.get('reason','')})")

        per_genome[genome] = {
            "experimental_stats": rt_stats,  # nazwa pola zgodna z L1.1 - wymagane przez scripts/validate_artifacts.py
            "recovery_time_detail": {
                "n_total": n_total, "n_censored": n_censored, "recovery_rate": recovery_rate,
                "min_non_censored": MIN_NON_CENSORED,
            },
            "pre_shock_band_check": {
                "pre_shock_in_band_fraction": pre_shock_in_band_fraction,
                "threshold": PRE_SHOCK_THRESHOLD, "endpoint_path": endpoint_path,
            },
            "adaptation_tick_stats": adapt_stats,
            "stability_score_stats": stab_stats,
            "control_stable_world": {
                "stability_score_stats": control_stability_stats,
                "fraction_in_band_stats": control_fraction_stats,
            },
            "glass_delta_stability_shock_vs_control": gd_stability,
        }

    default_rt = [r["primary_endpoint"]["value"] for r in all_results
                  if r["genome"] == "default" and not r["primary_endpoint"]["censored"]]
    plastic_rt = [r["primary_endpoint"]["value"] for r in all_results
                  if r["genome"] == "highly_plastic" and not r["primary_endpoint"]["censored"]]
    genome_gd = _cohens_d_with_flag(default_rt, plastic_rt)

    paths = {g: per_genome[g]["pre_shock_band_check"]["endpoint_path"] for g in genomes}
    mixed_case = len(set(paths.values())) > 1

    print(f"\n{'='*60}\nGENOME COMPARISON (recovery_time, Cohen's d)\n{'='*60}")
    if genome_gd["computable"]:
        print(f"Cohen's d (default vs highly_plastic): {genome_gd['cohens_d']}")
    else:
        print("Cohen's d: not computable")
    if mixed_case:
        print(f"MIXED CASE: genomy na roznych sciezkach endpointu -> {paths}")

    os.makedirs("reports/academy", exist_ok=True)
    report = {
        "lesson": "L1.2", "title": "Shock Recovery - Homeostatic Resilience", "version": "0.9",
        "scenario": "shock_world", "control_baseline": "stable_world",
        "control_variant": "B (baseline stability/fraction_in_band, cross-scenario Glass's delta na stability_score)",
        "total_runs": len(all_results) + len(baseline_results),
        "per_genome": per_genome,
        "genome_comparison": {"cohens_d_recovery_time": genome_gd, "mixed_case": mixed_case, "paths": paths},
        "results": [{k: v for k, v in r.items() if k != "telemetry"} for r in all_results],
        "baseline_results": [{k: v for k, v in r.items() if k != "telemetry"} for r in baseline_results],
    }
    with open("reports/academy/L1_2_shock_recovery.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport: reports/academy/L1_2_shock_recovery.json")
    print("=" * 60)
    return all_results


if __name__ == "__main__":
    run_lesson_L1_2()
