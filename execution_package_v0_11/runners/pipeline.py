"""BUILD-004/006/007 (Execution Package v0.11, Faza 1 Build, Architekt 2026-07-19).

Pipeline wykonawczy: generuje liste (genom, srodowisko, lekcja, seed) wg
manifestu/seed_policy.json, wywoluje ISTNIEJACE funkcje lekcji
(clos_academy.lesson_L1_1.run_pattern_echo / lesson_L1_2.run_shock_recovery -
ZERO duplikacji/modyfikacji Core), zapisuje kazdy run wg schematu BUILD-006
(run_id/genome/env/lesson/seed/timestamp/metrics/output_hash), z
checkpointingiem (BUILD-004) co CHECKPOINT_INTERVALS przebiegow i mozliwoscia
wznowienia (resume_from_checkpoint()).

DRY RUN (BUILD-007): run_dry_run() uzywa 3 seedow/grupe (23 genomy x 3
srodowiska x 3 seedy = 207) zamiast produkcyjnych 185 - sprawdza MECHANIKE
(czy pipeline dziala, czy checkpoint/resume dziala, czy Hard-Halt dziala),
NIE mierzy wynikow naukowych. To NIE jest eksperyment.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PACKAGE_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

from clos_academy.lesson_L1_1 import run_pattern_echo
from clos_academy.lesson_L1_2 import run_shock_recovery
from validators.hard_halt import enforce_hard_halt, check_stable_world_disjoint_seeds, AUD_001_BASELINE

CHECKPOINT_INTERVALS = [100, 500, 1000, 5000, 12765]
DRY_RUN_CHECKPOINT_INTERVALS = [100]  # jedyny checkpoint osiagalny w 207 runach


def _load(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _genomes() -> List[Dict[str, Any]]:
    return _load(PACKAGE_ROOT / "genomes" / "population.json")["genomes"]


def build_run_specs(n_seeds_per_group: Optional[int] = None) -> List[Tuple[str, str, str, int]]:
    """Zwraca liste (lesson, environment, genome_id, seed). n_seeds_per_group
    nadpisuje seed_policy.json (uzywane WYLACZNIE przez dry-run, patrz
    build_dry_run_specs ponizej) - domyslnie None = pelna polityka produkcyjna."""
    genomes = [g["genome_id"] for g in _genomes()]
    specs: List[Tuple[str, str, str, int]] = []

    def add(lesson, env, seeds):
        for g in genomes:
            for s in seeds:
                specs.append((lesson, env, g, s))

    if n_seeds_per_group is None:
        noise = _load(PACKAGE_ROOT / "environments" / "noise_world.json")
        shock = _load(PACKAGE_ROOT / "environments" / "shock_world.json")
        stable_l11 = _load(PACKAGE_ROOT / "environments" / "stable_world" / "L1_1_pattern_echo" / "seed_policy.json")
        stable_l12 = _load(PACKAGE_ROOT / "environments" / "stable_world" / "L1_2_shock_recovery" / "seed_policy.json")
        add("L1.1", "noise_world", range(1, noise["seed_policy"]["n_seeds"] + 1))
        add("L1.1", "stable_world", range(1, stable_l11["n_seeds"] + 1))
        add("L1.2", "shock_world", range(1, shock["seed_policy"]["n_seeds"] + 1))
        add("L1.2", "stable_world", range(94, 94 + stable_l12["n_seeds"]))
    else:
        # DRY RUN: 3 seedy/grupe. stable_world podzielony 2 (L1.1) + 1 (L1.2),
        # zeby wciaz cwiczyc OBIE sciezki lekcji (BUILD-002), proporcjonalnie
        # do podzialu produkcyjnego 93/92 (~1:1, tu 2:1 przy zaokragleniu w gore).
        add("L1.1", "noise_world", range(1, n_seeds_per_group + 1))
        add("L1.1", "stable_world", range(1, 3))       # 2 seedy
        add("L1.2", "shock_world", range(1, n_seeds_per_group + 1))
        add("L1.2", "stable_world", range(94, 95))      # 1 seed

    return specs


def build_dry_run_specs() -> List[Tuple[str, str, str, int]]:
    """BUILD-007: 23 genomy x 3 srodowiska x 3 seedy = 207."""
    return build_run_specs(n_seeds_per_group=3)


def _genome_lookup() -> Dict[str, Dict[str, Any]]:
    return {g["genome_id"]: g for g in _genomes()}


def _run_one(lesson: str, environment: str, genome: Dict[str, Any], seed: int) -> Dict[str, Any]:
    if lesson == "L1.1":
        result = run_pattern_echo(
            genome_preset=genome["genome_preset"], seed=seed, scenario=environment,
            genome_params=genome["genome_params"], genome_label=genome["genome_id"],
        )
    elif lesson == "L1.2":
        result = run_shock_recovery(
            genome_preset=genome["genome_preset"], seed=seed, scenario=environment,
            genome_params=genome["genome_params"], genome_label=genome["genome_id"],
        )
    else:
        raise ValueError(f"Nieznana lekcja: {lesson}")
    return {k: v for k, v in result.items() if k != "telemetry"}


def _record(lesson: str, environment: str, genome_id: str, seed: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """BUILD-006: schemat per-run rekordu."""
    metrics_json = json.dumps(metrics, sort_keys=True, default=str)
    return {
        "run_id": f"{lesson}_{genome_id}_{environment}_s{seed}",
        "genome": genome_id,
        "environment": environment,
        "lesson": lesson,
        "seed": seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "output_hash": hashlib.sha256(metrics_json.encode("utf-8")).hexdigest(),
    }


def write_checkpoint(logs_dir: Path, completed: int, total: int, results_path: Path) -> Path:
    ckpt = {
        "completed": completed,
        "total": total,
        "fraction": round(completed / total, 6),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results_path": str(results_path),
    }
    ckpt_path = logs_dir / f"checkpoint_{completed}.json"
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, indent=2, ensure_ascii=False)
    latest_path = logs_dir / "checkpoint_latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, indent=2, ensure_ascii=False)
    return ckpt_path


def resume_from_checkpoint(logs_dir: Path) -> int:
    """BUILD-004: zwraca liczbe JUZ ukonczonych runow (0 jesli brak checkpointu),
    zeby run_pipeline() mogl pominac juz wykonane specy i wznowic od tego miejsca."""
    latest_path = logs_dir / "checkpoint_latest.json"
    if not latest_path.exists():
        return 0
    with open(latest_path, encoding="utf-8") as f:
        ckpt = json.load(f)
    return ckpt["completed"]


def run_pipeline(specs: List[Tuple[str, str, str, int]], results_path: Path, logs_dir: Path,
                  checkpoint_intervals: List[int], enforce_core_hash: bool = True,
                  baseline: str = AUD_001_BASELINE, resume: bool = True) -> Dict[str, Any]:
    logs_dir.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    if enforce_core_hash:
        core_hash = enforce_hard_halt(REPO_ROOT, baseline=baseline)
    else:
        core_hash = None

    check_stable_world_disjoint_seeds(PACKAGE_ROOT)

    start_index = resume_from_checkpoint(logs_dir) if resume else 0
    genomes_by_id = _genome_lookup()

    mode = "a" if start_index > 0 else "w"
    total = len(specs)
    completed = start_index

    with open(results_path, mode, encoding="utf-8") as out:
        for i, (lesson, environment, genome_id, seed) in enumerate(specs[start_index:], start=start_index):
            genome = genomes_by_id[genome_id]
            metrics = _run_one(lesson, environment, genome, seed)
            record = _record(lesson, environment, genome_id, seed, metrics)
            out.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            completed = i + 1

            if completed in checkpoint_intervals or completed == total:
                out.flush()
                write_checkpoint(logs_dir, completed, total, results_path)

    return {
        "total": total,
        "completed": completed,
        "results_path": str(results_path),
        "core_hash": core_hash,
        "resumed_from": start_index,
    }


def hard_halt_self_test(repo_root: Path) -> Dict[str, Any]:
    """Dowod, ze mechanizm Hard-Halt FAKTYCZNIE halt'uje na niezgodnosc, na
    ZAMKNIETYM zakresie AUD-001 (24 pliki kanoniczne, algorytm potwierdzony
    2026-07-19 - patrz validators/hard_halt.py). Test: (a) prawdziwy hash
    24 plikow kontra baseline AUD-001 -> PASS (musi sie zgadzac - to jest
    TERAZ rzeczywista weryfikacja, nie samo-porownanie); (b) kontra celowo
    zepsuty string -> HALT. Nie modyfikuje zadnego pliku."""
    from validators.hard_halt import compute_files_hash, HardHaltError, enforce_hard_halt, CRITICAL_FILES_AUD_001, AUD_001_BASELINE

    current = compute_files_hash(repo_root, CRITICAL_FILES_AUD_001)
    result = {
        "current_critical_files_hash": current,
        "aud_001_baseline": AUD_001_BASELINE,
        "n_files": len(CRITICAL_FILES_AUD_001),
        "scope": "AUD-001 KANONICZNE (24 pliki, algorytm sciezka+sha256(zawartosc_LF-znormalizowana))",
    }

    try:
        enforce_hard_halt(repo_root, baseline=AUD_001_BASELINE)
        result["self_match_test"] = "PASS (hash policzony teraz == baseline AUD-001, brak HALT, jak oczekiwano)"
    except HardHaltError as e:
        result["self_match_test"] = f"FAIL (nieoczekiwany HALT): {e}"

    corrupted = AUD_001_BASELINE[:-4] + "0000"
    try:
        enforce_hard_halt(repo_root, baseline=corrupted)
        result["corruption_test"] = "FAIL (mechanizm NIE zatrzymal sie na niezgodnosc)"
    except HardHaltError:
        result["corruption_test"] = "PASS (HALT poprawnie wywolany na sztucznie zepsuty baseline)"

    return result


def run_dry_run() -> Dict[str, Any]:
    """BUILD-007: 207 runow (23x3x3), mechanika, NIE eksperyment.

    Hard-Halt uzywa TERAZ ZAMKNIETEGO baseline'u AUD-001 (24 pliki
    kanoniczne, dostarczone przez audytora, algorytm potwierdzony 2026-07-19
    po korekcie normalizacji CRLF->LF) - nie rekonstrukcji ani hasha
    samo-spojnego, jak w poprzednich iteracjach."""
    halt_proof = hard_halt_self_test(REPO_ROOT)

    specs = build_dry_run_specs()
    assert len(specs) == 207, f"DRY RUN oczekuje 207 specow, otrzymano {len(specs)}"
    results_path = PACKAGE_ROOT / "results" / "dry_run_results.jsonl"
    logs_dir = PACKAGE_ROOT / "logs" / "dry_run"
    from validators.hard_halt import AUD_001_BASELINE
    summary = run_pipeline(
        specs, results_path, logs_dir,
        checkpoint_intervals=DRY_RUN_CHECKPOINT_INTERVALS,
        enforce_core_hash=True, baseline=AUD_001_BASELINE,
        resume=False,
    )
    summary["hard_halt_mechanism_proof"] = halt_proof
    summary["aud_001_reconciliation_status"] = "ZAMKNIETE - hash odtworzony dokladnie, patrz hashes/baseline_hash.txt"
    return summary


if __name__ == "__main__":
    summary = run_dry_run()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
