"""Publication Bundle dla L1.2 - regeneruje bundle z biezacego kodu (v0.9).

Nie liczy nic samodzielnie: uruchamia run_shock_recovery() (clos_academy/lesson_L1_2.py,
scenario=shock_world + control_baseline=stable_world (wariant B), zgodnie z
publications/preregistration_L1_2.json) i pakuje wyniki przez
clos_studio.publication.bundle.build_bundle, zeby bundle byl zawsze zgodny
z kodem eksperymentu (SPRINT_v0.9.md, Priorytet 5).
"""

import json, os, sys
sys.path.insert(0, os.getcwd())

from clos_academy.lesson_L1_2 import run_shock_recovery, TICKS_TOTAL
from clos_studio.publication.bundle import build_bundle, _git_commit
from clos_studio.provenance.model import ExperimentProvenance

EXPERIMENT_ID = "L1_2_shock_recovery"
GENOMES = ["default", "highly_plastic"]
SEEDS = list(range(1, 11))


def _strip_telemetry(r):
    return {k: v for k, v in r.items() if k != "telemetry"}


def publish_l1_2_bundle():
    results = []
    for genome in GENOMES:
        for scenario in ("shock_world", "stable_world"):
            for seed in SEEDS:
                r = run_shock_recovery(genome_preset=genome, seed=seed, scenario=scenario)
                results.append(_strip_telemetry(r))

    manifest_dict = {
        "schema_version": 1,
        "experiment": {
            "id": EXPERIMENT_ID,
            "description": "L1.2 Shock Recovery - Homeostatic Resilience "
                            "(shock_world, control_baseline=stable_world, wariant B)",
        },
        "matrix": {"genomes": GENOMES, "scenarios": ["shock_world", "stable_world"], "seeds": SEEDS},
        "ticks": TICKS_TOTAL,
        "workflow_version": "0.9",
        "parent_experiment": None,
        "seed_policy": "fixed",
        "publish_on_verify": True,
        "primary_scenario": "shock_world",
        "control_baseline": "stable_world",
    }

    provenance = ExperimentProvenance(
        experiment_id=EXPERIMENT_ID,
        genome=",".join(GENOMES),
        scenario="shock_world,stable_world",
        seeds=SEEDS,
        ticks=TICKS_TOTAL,
        clos_version="0.9",
        cli_version="0.1.1",
        git_commit=_git_commit(),
    )

    return build_bundle(EXPERIMENT_ID, manifest_dict, provenance.to_dict(), results,
                         artifacts_base="experiments", output_dir="publications")


if __name__ == "__main__":
    bundle_path = publish_l1_2_bundle()
    print(f"Bundle: {bundle_path}")
    with open(os.path.join(bundle_path, "metadata.json"), encoding="utf-8") as f:
        print(json.dumps(json.load(f), indent=2, ensure_ascii=False))
