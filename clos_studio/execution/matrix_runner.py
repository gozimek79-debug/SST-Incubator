"""Matrix Runner v0.7.3 – z Observation Engine i telemetria."""

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
from clos_curriculum.observations.engine import export_events_batch

GENOME_ID_TO_PRESET = {"default_v1":"default","minimal_v1":"minimal","highly_plastic_v1":"highly_plastic"}

class MatrixRunner:
    def __init__(self):
        self.metadata_index = MetadataIndex(); self.metadata_index.connect()
        self.artifact_manager = ArtifactManager()

    def run(self, manifest_path: str) -> Dict[str, Any]:
        manifest = MatrixManifest.from_yaml(manifest_path); validate_or_raise(manifest)
        experiment_id = ExperimentProvenance.compute_experiment_id(manifest.to_dict())
        print(f"Matrix: {experiment_id}")

        self.artifact_manager.save_manifest(experiment_id, manifest.to_dict())
        self.metadata_index.register_experiment(experiment_id=experiment_id, manifest_dict=manifest.to_dict(),
            workflow_version=manifest.workflow_version, parent_experiment=manifest.parent_experiment)

        runs_config = manifest.get_run_matrix(); results = []
        for i, rc in enumerate(runs_config):
            run_id = f"{experiment_id}_{rc['genome'].replace('_v1','')}_{rc['scenario'].replace('_world','')}_s{rc['seed']}"
            preset = GENOME_ID_TO_PRESET.get(rc["genome"], "default")
            print(f"    [{i+1}/{len(runs_config)}] {run_id}...", end=" ")
            cmd = [sys.executable, "-m", "clos_cli", "demo", "--seed", str(rc["seed"]),
                   "--ticks", str(rc["ticks"]), "--genome", preset, "--scenario", rc["scenario"]]
            env = os.environ.copy(); env["PYTHONPATH"] = os.getcwd()
            try:
                process = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd(), env=env, timeout=600)
                status = "COMPLETE" if process.returncode == 0 else "FAILED"
                metrics = {}
                for line in process.stdout.strip().split("\n"):
                    if line.strip().startswith("{") and "stability_score" in line:
                        try: metrics = json.loads(line.strip())
                        except: pass
                print(status)
            except: status = "ERROR"; metrics = {}; print(status)

            run_result = {"run_id":run_id,"genome":rc["genome"],"scenario":rc["scenario"],
                "seed":rc["seed"],"ticks":rc["ticks"],"status":status,
                "stability_score":metrics.get("stability_score",0),
                "mse":metrics.get("mse",0),"entropy_volatility":metrics.get("entropy_volatility",0),
                "adaptation_tick":metrics.get("adaptation_tick",0),
                "memory_size":metrics.get("memory_size",0),
                "final_energy":metrics.get("final_energy",1.0)}
            results.append(run_result)
            self.artifact_manager.save_run_result(experiment_id, run_id, run_result)

        # Observation Engine
        events_path, events_count = export_events_batch(results, experiment_id)
        print(f"    Events: {events_count} -> {events_path}")

        export_all_formats(results, f"datasets/{experiment_id}/dataset")
        verify_result = verify_experiment(experiment_id, manifest, self.metadata_index, self.artifact_manager)
        print(verify_result.summary())

        provenance = ExperimentProvenance(experiment_id=experiment_id,
            genome=",".join(manifest.genomes), scenario=",".join(manifest.scenarios),
            seeds=manifest.seeds, ticks=manifest.ticks, clos_version="0.7.3", cli_version="0.1.1")
        self.artifact_manager.save_provenance(experiment_id, provenance.to_dict())
        build_bundle(experiment_id, manifest.to_dict(), provenance.to_dict(), results)

        completed = sum(1 for r in results if r["status"]=="COMPLETE")
        print(f"MATRIX COMPLETE ({completed}/{len(results)})")
        return {"experiment_id":experiment_id,"results":results}

    def close(self): self.metadata_index.close()
