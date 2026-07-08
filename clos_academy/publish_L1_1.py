"""Publication Bundle dla L1.1 - regeneruje bundle z biezacego kodu (v0.8.4).

Nie liczy nic samodzielnie: uruchamia run_pattern_echo() (clos_academy/lesson_L1_1.py,
scenario=noise_world + control_baseline=stable_world, zgodnie z
publications/preregistration_L1_1.json) i pakuje wyniki przez
clos_studio.publication.bundle.build_bundle, zeby bundle byl zawsze zgodny
z kodem eksperymentu (SPRINT_v0.8.4.md, Priorytet 1).
"""

import json, os, sys
sys.path.insert(0, os.getcwd())

from clos_academy.lesson_L1_1 import run_pattern_echo
from clos_studio.publication.bundle import build_bundle, _git_commit
from clos_studio.provenance.model import ExperimentProvenance

EXPERIMENT_ID = "L1_1_pattern_echo"
GENOMES = ["default", "highly_plastic"]
SEEDS = list(range(1, 11))
TICKS = 200


def _strip_telemetry(r):
    return {k: v for k, v in r.items() if k != "telemetry"}


def publish_l1_1_bundle():
    results = []
    for genome in GENOMES:
        for scenario in ("noise_world", "stable_world"):
            for seed in SEEDS:
                r = run_pattern_echo(genome_preset=genome, seed=seed, scenario=scenario)
                results.append(_strip_telemetry(r))

    manifest_dict = {
        "schema_version": 1,
        "experiment": {
            "id": EXPERIMENT_ID,
            "description": "L1.1 Pattern Echo - Working Memory Emergence "
                            "(noise_world, control_baseline=stable_world)",
        },
        "matrix": {"genomes": GENOMES, "scenarios": ["noise_world", "stable_world"], "seeds": SEEDS},
        "ticks": TICKS,
        "workflow_version": "0.8.4",
        "parent_experiment": None,
        "seed_policy": "fixed",
        "publish_on_verify": True,
        "primary_scenario": "noise_world",
        "control_baseline": "stable_world",
    }

    provenance = ExperimentProvenance(
        experiment_id=EXPERIMENT_ID,
        genome=",".join(GENOMES),
        scenario="noise_world,stable_world",
        seeds=SEEDS,
        ticks=TICKS,
        clos_version="0.8.4",
        cli_version="0.1.1",
        git_commit=_git_commit(),
    )

    return build_bundle(EXPERIMENT_ID, manifest_dict, provenance.to_dict(), results,
                         artifacts_base="experiments", output_dir="publications")


if __name__ == "__main__":
    bundle_path = publish_l1_1_bundle()
    print(f"Bundle: {bundle_path}")
    with open(os.path.join(bundle_path, "metadata.json"), encoding="utf-8") as f:
        print(json.dumps(json.load(f), indent=2, ensure_ascii=False))
