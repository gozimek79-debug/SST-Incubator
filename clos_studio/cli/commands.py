"""CLI komendy Experiment Studio."""

import sys
import os
from clos_studio.manifest.schema import ExperimentManifest
from clos_studio.manifest.validator import validate_or_raise, ManifestValidationError
from clos_studio.execution.queue import ExecutionQueue
from clos_studio.execution.executor import ExperimentExecutor
from clos_studio.artifacts.manager import ArtifactManager
from clos_studio.provenance.model import ExperimentProvenance
from clos_studio.publication.bundle import build_bundle


def run_experiment_from_manifest(manifest_path: str):
    """Uruchamia eksperyment z pliku manifestu.

    Args:
        manifest_path: Ścieżka do pliku YAML/JSON.
    """
    print("=" * 60)
    print("CLOS Experiment Studio v0.3")
    print("=" * 60)

    # 1. Wczytaj manifest
    print(f"\n[1] Loading manifest: {manifest_path}")
    if manifest_path.endswith(".yaml") or manifest_path.endswith(".yml"):
        manifest = ExperimentManifest.from_yaml(manifest_path)
    elif manifest_path.endswith(".json"):
        manifest = ExperimentManifest.from_json(manifest_path)
    else:
        print(f"ERROR: Unsupported format. Use .yaml or .json")
        sys.exit(1)

    # 2. Walidacja
    print("[2] Validating manifest...")
    try:
        validate_or_raise(manifest)
        print("    Manifest VALID")
    except ManifestValidationError as e:
        print(f"    Manifest INVALID:\n{e}")
        sys.exit(1)

    # 3. Generuj Experiment ID
    experiment_id = ExperimentProvenance.compute_experiment_id(manifest.to_dict())
    print(f"\n[3] Experiment ID: {experiment_id}")

    # 4. Kolejka wykonawcza
    queue = ExecutionQueue(manifest)
    print(f"\n[4] Execution Queue:")
    print(f"    {queue.total_runs} runs")
    print(f"    Genomes: {manifest.genomes}")
    print(f"    Scenarios: {manifest.scenarios}")
    print(f"    Seeds: {manifest.seeds}")
    print(f"    Ticks: {manifest.ticks}")

    # 5. Wykonanie
    print(f"\n[5] Executing...")
    executor = ExperimentExecutor(queue)
    results = executor.run_all()

    completed = sum(1 for r in results if r["status"] == "COMPLETE")
    failed = sum(1 for r in results if r["status"] != "COMPLETE")
    print(f"    Completed: {completed}/{len(results)}")
    if failed > 0:
        print(f"    Failed: {failed}")

    # 6. Zapis artefaktów
    print(f"\n[6] Saving artifacts...")
    am = ArtifactManager()
    am.save_manifest(experiment_id, manifest.to_dict())

    # Proweniencja
    provenance = ExperimentProvenance(
        experiment_id=experiment_id,
        genome=",".join(manifest.genomes),
        scenario=",".join(manifest.scenarios),
        seeds=manifest.seeds,
        ticks=manifest.ticks,
    )
    am.save_provenance(experiment_id, provenance.to_dict())

    for i, result in enumerate(results):
        run_id = result.get("run_id", f"run_{i:04d}")
        am.save_run_result(experiment_id, run_id, result)

    # 7. Integrity check
    print(f"\n[7] Integrity check:")
    integrity = am.check_integrity(experiment_id)
    for artifact, status in integrity.items():
        print(f"    {artifact}: {status.value}")

    # 8. Publication bundle
    print(f"\n[8] Building publication bundle...")
    bundle_path = build_bundle(
        experiment_id=experiment_id,
        manifest_dict=manifest.to_dict(),
        provenance_dict=provenance.to_dict(),
        results=results,
    )
    print(f"    Bundle: {bundle_path}")

    print("\n" + "=" * 60)
    print(f"EXPERIMENT {experiment_id} COMPLETE")
    print(f"Status: {completed}/{len(results)} runs passed")
    print("=" * 60)
