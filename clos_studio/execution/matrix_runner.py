"""Matrix Runner – wykonuje pełną macierz eksperymentów."""

import sys
import os
import json
import subprocess
from typing import Dict, Any, List
from clos_studio.manifest.matrix_schema import MatrixManifest
from clos_studio.manifest.validator import validate_or_raise
from clos_studio.provenance.model import ExperimentProvenance
from clos_studio.metadata_index import MetadataIndex
from clos_studio.artifacts.manager import ArtifactManager
from clos_studio.dataset_exporter import export_all_formats
from clos_studio.verify import verify_experiment
from clos_studio.publication.bundle import build_bundle


class MatrixRunner:
    def __init__(self):
        self.metadata_index = MetadataIndex()
        self.metadata_index.connect()
        self.artifact_manager = ArtifactManager()

    def run(self, manifest_path: str) -> Dict[str, Any]:
        print("=" * 60)
        print("CLOS Research Matrix Core v0.4")
        print("=" * 60)

        print(f"\n[1] Loading manifest: {manifest_path}")
        manifest = MatrixManifest.from_yaml(manifest_path)
        print(manifest.summary())

        print("\n[2] Validating manifest...")
        validate_or_raise(manifest)
        print("    VALID")

        experiment_id = ExperimentProvenance.compute_experiment_id(manifest.to_dict())
        print(f"\n[3] Experiment ID: {experiment_id}")

        # ZAPISZ MANIFEST OD RAZU
        self.artifact_manager.save_manifest(experiment_id, manifest.to_dict())

        print("\n[4] Registering in metadata index...")
        self.metadata_index.register_experiment(
            experiment_id=experiment_id,
            manifest_dict=manifest.to_dict(),
            workflow_version=manifest.workflow_version,
            parent_experiment=manifest.parent_experiment,
        )

        runs_config = manifest.get_run_matrix()
        print(f"\n[5] Executing {len(runs_config)} runs...")

        results = []
        for i, run_config in enumerate(runs_config):
            run_id = f"{experiment_id}_{run_config['genome'].replace('_v1','')}_{run_config['scenario'].replace('_world','')}_s{run_config['seed']}"
            print(f"    [{i+1}/{len(runs_config)}] {run_id}...", end=" ")

            self.metadata_index.register_run(
                run_id=run_id, experiment_id=experiment_id,
                genome=run_config["genome"], scenario=run_config["scenario"],
                seed=run_config["seed"], ticks=run_config["ticks"],
                workflow_version=manifest.workflow_version, status="running",
            )

            project_root = os.getcwd()
            cmd = [
                sys.executable, "-m", "clos_cli", "demo",
                "--seed", str(run_config["seed"]),
                "--ticks", str(run_config["ticks"]),
            ]
            env = os.environ.copy()
            env["PYTHONPATH"] = project_root

            try:
                process = subprocess.run(cmd, capture_output=True, text=True,
                                        cwd=project_root, env=env, timeout=300)
                status = "COMPLETE" if process.returncode == 0 else "FAILED"
                print(status)
            except subprocess.TimeoutExpired:
                status = "TIMEOUT"
                print(status)
            except Exception as e:
                status = "ERROR"
                print(f"ERROR: {e}")

            self.metadata_index.register_run(
                run_id=run_id, experiment_id=experiment_id,
                genome=run_config["genome"], scenario=run_config["scenario"],
                seed=run_config["seed"], ticks=run_config["ticks"],
                workflow_version=manifest.workflow_version, status=status,
                summary_metrics={"stability_score": 0.0},
                artifact_pointers={"run_id": run_id},
            )

            results.append({"run_id": run_id, "status": status, "config": run_config})
            self.artifact_manager.save_run_result(experiment_id, run_id, {
                "run_id": run_id, "status": status, "config": run_config,
            })

        # Eksport datasetów
        print(f"\n[6] Exporting datasets...")
        dataset_base = f"datasets/{experiment_id}/dataset"
        try:
            formats = export_all_formats(results, dataset_base)
            for fmt, path in formats.items():
                print(f"    {fmt}: {path}")
        except Exception as e:
            print(f"    Export error: {e}")

        # Weryfikacja
        print(f"\n[7] Verifying experiment...")
        verify_result = verify_experiment(
            experiment_id=experiment_id, manifest=manifest,
            metadata_index=self.metadata_index, artifact_manager=self.artifact_manager,
        )
        print(verify_result.summary())

        # Publikacja – ZAWSZE, nawet jeśli verify nie przeszedł
        print(f"\n[8] Building publication bundle...")
        provenance = ExperimentProvenance(
            experiment_id=experiment_id,
            genome=",".join(manifest.genomes),
            scenario=",".join(manifest.scenarios),
            seeds=manifest.seeds, ticks=manifest.ticks,
            clos_version="0.4", cli_version="0.1.1",
        )
        self.artifact_manager.save_provenance(experiment_id, provenance.to_dict())

        try:
            bundle_path = build_bundle(
                experiment_id=experiment_id,
                manifest_dict=manifest.to_dict(),
                provenance_dict=provenance.to_dict(),
                results=results,
            )
            print(f"    Bundle: {bundle_path}")
        except Exception as e:
            print(f"    Bundle error: {e}")

        completed = sum(1 for r in results if r["status"] == "COMPLETE")
        print("\n" + "=" * 60)
        print(f"MATRIX {experiment_id} COMPLETE")
        print(f"Status: {completed}/{len(results)} runs passed")
        print(f"Verify: {'PASS' if verify_result.passed else 'FAIL'}")
        print("=" * 60)

        return {
            "experiment_id": experiment_id,
            "total_runs": len(results),
            "completed": completed,
            "verify_passed": verify_result.passed,
            "results": results,
        }

    def close(self):
        self.metadata_index.close()
