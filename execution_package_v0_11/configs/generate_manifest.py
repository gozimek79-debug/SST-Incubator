"""BUILD-003 (Execution Package v0.11, Faza 1 Build, Architekt 2026-07-19).

Generuje experiment_manifest.json z jawna weryfikacja arytmetyki: total_runs
MUSI wyjsc dokladnie 12765 (nie 25530) - bramka arytmetyczna. Czyta genomy z
genomes/population.json (wygenerowane wprost z
clos_curriculum.laboratory.population.generate_population(), nie duplikowane
tutaj) i seed_policy.json z kazdego katalogu srodowiska/lekcji.

Uzycie:
    python execution_package_v0_11/configs/generate_manifest.py
"""

import hashlib
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def _load(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _cell(lesson: str, environment: str, n_genomes: int, n_seeds: int, seeds_desc: str) -> dict:
    return {
        "lesson": lesson,
        "environment": environment,
        "n_genomes": n_genomes,
        "n_seeds": n_seeds,
        "seeds": seeds_desc,
        "n_runs": n_genomes * n_seeds,
    }


def build_manifest() -> dict:
    population = _load(PACKAGE_ROOT / "genomes" / "population.json")
    n_genomes = population["n_genomes"]
    if n_genomes != 23:
        raise ValueError(f"Oczekiwano 23 genomow, znaleziono {n_genomes} - bramka arytmetyczna FAIL")

    noise = _load(PACKAGE_ROOT / "environments" / "noise_world.json")
    shock = _load(PACKAGE_ROOT / "environments" / "shock_world.json")
    stable_l11 = _load(PACKAGE_ROOT / "environments" / "stable_world" / "L1_1_pattern_echo" / "seed_policy.json")
    stable_l12 = _load(PACKAGE_ROOT / "environments" / "stable_world" / "L1_2_shock_recovery" / "seed_policy.json")

    cells = [
        _cell("L1.1", "noise_world", n_genomes, noise["seed_policy"]["n_seeds"], noise["seed_policy"]["seeds"]),
        _cell("L1.1", "stable_world", n_genomes, stable_l11["n_seeds"], stable_l11["seeds"]),
        _cell("L1.2", "shock_world", n_genomes, shock["seed_policy"]["n_seeds"], shock["seed_policy"]["seeds"]),
        _cell("L1.2", "stable_world", n_genomes, stable_l12["n_seeds"], stable_l12["seeds"]),
    ]

    total_runs = sum(c["n_runs"] for c in cells)
    n_groups_per_environment_slot = 23  # genomy x srodowisko (3 slots: noise/stable/shock), NIE licza sie osobno per lekcja
    n_environment_slots = 3
    n_groups = n_genomes * n_environment_slots
    n_repetitions_per_group = 185

    # BRAMKA ARYTMETYCZNA (BUILD-003): total_runs MUSI wyjsc 12765.
    expected_total = n_groups * n_repetitions_per_group
    if total_runs != 12765:
        raise ValueError(
            f"BRAMKA ARYTMETYCZNA FAIL: total_runs={total_runs}, oczekiwano 12765. "
            f"(n_groups={n_groups} x n_repetitions_per_group={n_repetitions_per_group} = {expected_total})"
        )
    if total_runs != expected_total:
        raise ValueError(
            f"NIESPOJNOSC: suma komorek ({total_runs}) != n_groups*n_repetitions ({expected_total})"
        )

    manifest = {
        "study_id": "v0.11.0_confirmatory_rerun",
        "generated_by": "execution_package_v0_11/configs/generate_manifest.py (BUILD-003)",
        "genomes": n_genomes,
        "environments": n_environment_slots,
        "environments_list": ["noise_world", "stable_world", "shock_world"],
        "repetitions": n_repetitions_per_group,
        "n_groups": n_groups,
        "total_runs": total_runs,
        "cells": cells,
        "arithmetic_gate": {
            "formula": "n_genomes (23) x n_environment_slots (3) x n_repetitions_per_group (185) = 12765",
            "computed": expected_total,
            "matches_cell_sum": total_runs == expected_total,
            "matches_required_12765": total_runs == 12765,
            "status": "PASS" if (total_runs == expected_total == 12765) else "FAIL",
        },
        "stable_world_split_note": (
            "stable_world (23x185=4255 lacznie) podzielony miedzy L1.1 (93 seedow, "
            "2139 runow) i L1.2 (92 seedow, 2116 runow) - suma 185 seedow, ZERO "
            "nakladania. Patrz environments/stable_world/*/config.json:design_decision."
        ),
    }
    return manifest


def write_manifest() -> Path:
    manifest = build_manifest()
    manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False)
    manifest["manifest_sha256"] = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()

    out_path = PACKAGE_ROOT / "experiment_manifest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return out_path


if __name__ == "__main__":
    path = write_manifest()
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    print(f"Manifest: {path}")
    print(f"total_runs = {m['total_runs']} (bramka: {m['arithmetic_gate']['status']})")
    print(f"manifest_sha256 = {m['manifest_sha256']}")
    sys.exit(0 if m["arithmetic_gate"]["status"] == "PASS" else 1)
