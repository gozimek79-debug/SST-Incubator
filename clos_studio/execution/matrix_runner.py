"""Matrix Runner v0.5 – mapuje genome_id na preset."""

import sys, os, json, subprocess
from typing import Dict, Any, List
from clos_studio.manifest.matrix_schema import MatrixManifest
from clos_studio.manifest.validator import validate_or_raise
from clos_studio.provenance.model import ExperimentProvenance
from clos_studio.metadata_index import MetadataIndex
from clos_studio.artifacts.manager import ArtifactManager
from clos_studio.dataset_exporter import export_all_formats
from clos_studio.verify import verify_experiment
from clos_studio.publication.bundle import build_bundle

GENOME_ID_TO_PRESET = {
    "default_v1": "default",
    "minimal_v1": "minimal",
    "highly_plastic_v1": "highly_plastic",
}

class MatrixRunner:
    def __init__(self):
        self.metadata_index = MetadataIndex(); self.metadata_index.connect()
        self.artifact_manager = ArtifactManager()

    def run(self, manifest_path: str) -> Dict[str, Any]:
        print("=" * 60); print("CLOS Research Matrix Core v0.5"); print("=" * 60)
        print(f"\n[1] Loading manifest: {manifest_path}")
        manifest = MatrixManifest.from_yaml(manifest_path); print(manifest.summary())
        print("\n[2] Validating..."); validate_or_raise(manifest); print("    VALID")
        experiment_id = ExperimentProvenance.compute_experiment_id(manifest.to_dict())
        print(f"\n[3] Experiment ID: {experiment_id}")
        self.artifact_manager.save_manifest(experiment_id, manifest.to_dict())
        self.metadata_index.register_experiment(experiment_id=experiment_id, manifest_dict=manifest.to_dict(), workflow_version=manifest.workflow_version, parent_experiment=manifest.parent_experiment)
        runs_config = manifest.get_run_matrix()
        print(f"\n[4] Executing {len(runs_config)} runs...")
        results = []
        for i, rc in enumerate(runs_config):
            run_id = f"{experiment_id}_{rc['genome'].replace('_v1','')}_{rc['scenario'].replace('_world','')}_s{rc['seed']}"
            preset = GENOME_ID_TO_PRESET.get(rc["genome"], "default")
            print(f"    [{i+1}/{len(runs_config)}] {run_id} (preset={preset})...", end=" ")
            cmd = [sys.executable, "-m", "clos_cli", "demo", "--seed", str(rc["seed"]), "--ticks", str(rc["ticks"]), "--genome", preset]
            env = os.environ.copy(); env["PYTHONPATH"] = os.getcwd()
            try:
                process = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd(), env=env, timeout=300)
                status = "COMPLETE" if process.returncode == 0 else "FAILED"
                stability_score = 0.0; mse_val = 0.0; entropy_vol = 0.0; adaptation_tick = 0
                for line in process.stdout.split("\n"):
                    if "Stability Score:" in line:
                        try: stability_score = float(line.split(":")[-1].strip())
                        except: pass
                    if "MSE:" in line and "Mean" not in line and "STD" not in line:
                        try: mse_val = float(line.split(":")[-1].strip())
                        except: pass
                    if "Entropy Volatility:" in line:
                        try: entropy_vol = float(line.split(":")[-1].strip())
                        except: pass
                    if "Adaptation:" in line and "tick" in line:
                        try: adaptation_tick = int(line.split("tick")[-1].strip())
                        except: pass
                print(status)
            except: status = "ERROR"; stability_score = mse_val = entropy_vol = 0.0; adaptation_tick = 0; print(status)
            self.metadata_index.register_run(run_id=run_id, experiment_id=experiment_id, genome=rc["genome"], scenario=rc["scenario"], seed=rc["seed"], ticks=rc["ticks"], workflow_version=manifest.workflow_version, status=status, summary_metrics={"stability_score": round(stability_score,4), "mse": round(mse_val,4), "entropy_volatility": round(entropy_vol,4), "adaptation_tick": adaptation_tick}, artifact_pointers={"run_id": run_id})
            results.append({"run_id": run_id, "genome": rc["genome"], "scenario": rc["scenario"], "seed": rc["seed"], "status": status, "stability_score": round(stability_score,4), "mse": round(mse_val,4), "entropy_volatility": round(entropy_vol,4), "adaptation_tick": adaptation_tick})
            self.artifact_manager.save_run_result(experiment_id, run_id, results[-1])
        print(f"\n[5] Exporting datasets...")
        try:
            formats = export_all_formats(results, f"datasets/{experiment_id}/dataset")
            for fmt, path in formats.items(): print(f"    {fmt}: {path}")
        except Exception as e: print(f"    Error: {e}")
        print(f"\n[6] Verifying...")
        verify_result = verify_experiment(experiment_id, manifest, self.metadata_index, self.artifact_manager)
        print(verify_result.summary())
        print(f"\n[7] Building bundle...")
        provenance = ExperimentProvenance(experiment_id=experiment_id, genome=",".join(manifest.genomes), scenario=",".join(manifest.scenarios), seeds=manifest.seeds, ticks=manifest.ticks, clos_version="0.5", cli_version="0.1.1")
        self.artifact_manager.save_provenance(experiment_id, provenance.to_dict())
        try:
            bundle_path = build_bundle(experiment_id, manifest.to_dict(), provenance.to_dict(), results)
            print(f"    Bundle: {bundle_path}")
        except Exception as e: print(f"    Error: {e}")
        completed = sum(1 for r in results if r["status"] == "COMPLETE")
        print(f"\n{'='*60}\nMATRIX {experiment_id} COMPLETE\n{completed}/{len(results)} passed\n{'='*60}")
        return {"experiment_id": experiment_id, "total_runs": len(results), "completed": completed, "verify_passed": verify_result.passed, "results": results}

    def close(self): self.metadata_index.close()
