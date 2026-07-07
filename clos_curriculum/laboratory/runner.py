"""Laboratory Experiment Runner – wykonuje lekcje jako eksperymenty."""

import sys, os, json, subprocess
from typing import Dict, Any, List
from clos_curriculum.academy.lesson import LessonManifest
from clos_curriculum.laboratory.statistics import compute_ci95, cohens_d, validate_sample_size

GENOME_ID_TO_PRESET = {
    "default": "default", "default_v1": "default",
    "minimal": "minimal", "minimal_v1": "minimal",
    "highly_plastic": "highly_plastic", "highly_plastic_v1": "highly_plastic",
}


def run_lesson(lesson: LessonManifest) -> Dict[str, Any]:
    """Wykonuje pojedynczą lekcję jako eksperyment.

    Args:
        lesson: Manifest lekcji.

    Returns:
        Wynik lekcji z metrykami i statystykami.
    """
    print(f"\n{'='*60}")
    print(f"CRC Lesson: {lesson.lesson_id} – {lesson.name}")
    print(f"Level: {lesson.level} | Hypothesis: {lesson.hypothesis}")
    print(f"{'='*60}")

    all_results = []
    total_runs = len(lesson.genome_presets) * len(lesson.scenarios) * len(lesson.seeds)

    for genome in lesson.genome_presets:
        preset = GENOME_ID_TO_PRESET.get(genome, genome)
        for scenario in lesson.scenarios:
            for seed in lesson.seeds:
                run_id = f"{lesson.lesson_id}_{preset}_{scenario}_s{seed}"
                print(f"  [{len(all_results)+1}/{total_runs}] {run_id}...", end=" ")

                cmd = [
                    sys.executable, "-m", "clos_cli", "demo",
                    "--seed", str(seed), "--ticks", str(lesson.ticks),
                    "--genome", preset, "--scenario", scenario
                ]
                env = os.environ.copy()
                env["PYTHONPATH"] = os.getcwd()

                try:
                    process = subprocess.run(cmd, capture_output=True, text=True,
                                            cwd=os.getcwd(), env=env, timeout=600)
                    status = "COMPLETE" if process.returncode == 0 else "FAILED"
                    metrics = {}
                    for line in process.stdout.strip().split("\n"):
                        line = line.strip()
                        if line.startswith("{") and "stability_score" in line:
                            try: metrics = json.loads(line)
                            except: pass
                    all_results.append({
                        "run_id": run_id, "status": status,
                        "genome": genome, "scenario": scenario, "seed": seed,
                        **{k: metrics.get(k, 0) for k in [
                            "stability_score", "mse", "entropy_volatility",
                            "energy_drift", "adaptation_tick", "convergence_tick",
                            "memory_size", "final_entropy", "final_energy"
                        ]}
                    })
                    print(status)
                except Exception as e:
                    print(f"ERROR: {e}")
                    all_results.append({"run_id": run_id, "status": "ERROR"})

    # Analiza statystyczna
    completed = [r for r in all_results if r["status"] == "COMPLETE"]
    primary_values = [r.get(lesson.primary_endpoint, 0) for r in completed if lesson.primary_endpoint in r]

    stats = compute_ci95(primary_values) if primary_values else {}
    sample_check = validate_sample_size(primary_values, lesson.min_seeds)

    # Sprawdzenie warunków PASS/FAIL
    passed = True
    fail_reasons = []

    if lesson.pass_conditions:
        for condition, threshold in lesson.pass_conditions.items():
            if condition.endswith("_min") and stats.get("mean", 0) < threshold:
                passed = False
                fail_reasons.append(f"{condition}: {stats.get('mean', 0):.4f} < {threshold}")
            elif condition.endswith("_max") and stats.get("mean", 0) > threshold:
                passed = False
                fail_reasons.append(f"{condition}: {stats.get('mean', 0):.4f} > {threshold}")

    # Ogólna ocena
    grade = "PASS" if passed and sample_check["sufficient"] else "FAIL"

    result = {
        "lesson_id": lesson.lesson_id,
        "name": lesson.name,
        "level": lesson.level,
        "hypothesis": lesson.hypothesis,
        "grade": grade,
        "total_runs": len(all_results),
        "completed_runs": len(completed),
        "primary_endpoint": lesson.primary_endpoint,
        "statistics": stats,
        "sample_validation": sample_check,
        "pass_conditions_check": {
            "passed": passed,
            "fail_reasons": fail_reasons,
        },
        "runs": all_results,
    }

    # Podsumowanie
    print(f"\n  Grade: {grade}")
    if stats:
        print(f"  {lesson.primary_endpoint}: mean={stats.get('mean', 0):.4f}, CI95=[{stats.get('ci95_low', 0):.4f}, {stats.get('ci95_high', 0):.4f}]")
    if fail_reasons:
        for reason in fail_reasons:
            print(f"  FAIL: {reason}")

    return result
