"""Testy End-to-End dla Research Matrix Core v0.4."""

import pytest
import sys
import os
import json
import subprocess
sys.path.insert(0, '.')

from clos_studio.manifest.matrix_schema import MatrixManifest
from clos_studio.metadata_index import MetadataIndex
from clos_studio.dataset_exporter import export_all_formats
from clos_studio.verify import verify_experiment, VerifyResult
from clos_studio.artifacts.manager import ArtifactManager


def make_matrix_manifest_dict():
    return {
        "schema_version": 1,
        "experiment": {
            "id": "e2e_test_matrix",
            "description": "E2E test matrix"
        },
        "matrix": {
            "genomes": ["default_v1"],
            "scenarios": ["stable_world"],
            "seeds": [42, 43]
        },
        "ticks": 20,
        "workflow_version": "0.4",
        "publish_on_verify": True,
    }


class TestMatrixManifest:
    def test_from_dict(self):
        data = make_matrix_manifest_dict()
        manifest = MatrixManifest.from_dict(data)
        assert manifest.get_total_runs() == 2

    def test_run_matrix_generation(self):
        data = make_matrix_manifest_dict()
        data["matrix"]["genomes"] = ["default_v1", "highly_plastic_v1"]
        data["matrix"]["scenarios"] = ["stable_world", "shock_world"]
        data["matrix"]["seeds"] = [1, 2]
        manifest = MatrixManifest.from_dict(data)
        runs = manifest.get_run_matrix()
        assert len(runs) == 8  # 2x2x2

    def test_summary(self):
        manifest = MatrixManifest.from_dict(make_matrix_manifest_dict())
        summary = manifest.summary()
        assert "e2e_test_matrix" in summary
        assert "2" in summary  # total runs


class TestMetadataIndex:
    def test_register_and_query(self, tmp_path):
        db_path = str(tmp_path / "test_index.db")
        idx = MetadataIndex(db_path=db_path)
        idx.connect()

        idx.register_experiment("EXP-001", {"experiment": {"id": "test"}})
        idx.register_run("run_1", "EXP-001", "default_v1", "stable_world", 42, 100, "0.4", status="COMPLETE")
        idx.register_run("run_2", "EXP-001", "default_v1", "stable_world", 43, 100, "0.4", status="COMPLETE")

        runs = idx.get_experiment_runs("EXP-001")
        assert len(runs) == 2

        counts = idx.get_run_count_by_status("EXP-001")
        assert counts["COMPLETE"] == 2

        idx.close()

    def test_list_experiments(self, tmp_path):
        db_path = str(tmp_path / "test_index2.db")
        idx = MetadataIndex(db_path=db_path)
        idx.connect()
        idx.register_experiment("EXP-A", {"experiment": {"id": "a"}})
        idx.register_experiment("EXP-B", {"experiment": {"id": "b"}})
        exps = idx.list_experiments()
        assert len(exps) == 2
        idx.close()


class TestDatasetExporter:
    def test_export_all_formats(self, tmp_path):
        data = [
            {"run_id": "r1", "status": "COMPLETE", "seed": 42},
            {"run_id": "r2", "status": "COMPLETE", "seed": 43},
        ]
        base = str(tmp_path / "test_export")
        formats = export_all_formats(data, base)
        assert os.path.exists(formats["jsonl"])
        assert os.path.exists(formats["csv"])
        assert os.path.exists(formats["parquet"])

    def test_jsonl_content(self, tmp_path):
        data = [{"a": 1}, {"b": 2}]
        base = str(tmp_path / "test_jsonl")
        formats = export_all_formats(data, base)
        with open(formats["jsonl"], "r") as f:
            lines = f.readlines()
        assert len(lines) == 2


class TestVerify:
    def test_verify_all_pass(self, tmp_path):
        data = make_matrix_manifest_dict()
        manifest = MatrixManifest.from_dict(data)
        exp_id = "EXP-VERIFY-PASS"

        db_path = str(tmp_path / "verify_test.db")
        idx = MetadataIndex(db_path=db_path)
        idx.connect()

        idx.register_experiment(exp_id, manifest.to_dict(), workflow_version="0.4")
        for seed in [42, 43]:
            run_id = f"{exp_id}_default_stable_s{seed}"
            idx.register_run(run_id, exp_id, "default_v1", "stable_world", seed, 20, "0.4", status="COMPLETE")

        am = ArtifactManager(base_path=str(tmp_path / "experiments"))
        am.save_manifest(exp_id, manifest.to_dict())
        for seed in [42, 43]:
            run_id = f"{exp_id}_default_stable_s{seed}"
            am.save_run_result(exp_id, run_id, {"status": "COMPLETE"})

        result = verify_experiment(exp_id, manifest, idx, am)
        assert result.passed

        idx.close()

    def test_verify_fails_on_missing_runs(self, tmp_path):
        data = make_matrix_manifest_dict()
        manifest = MatrixManifest.from_dict(data)
        exp_id = "EXP-VERIFY-FAIL"

        db_path = str(tmp_path / "verify_fail.db")
        idx = MetadataIndex(db_path=db_path)
        idx.connect()

        # Zarejestruj tylko 1 run zamiast 2
        idx.register_experiment(exp_id, manifest.to_dict())
        idx.register_run("run_1", exp_id, "default_v1", "stable_world", 42, 20, "0.4", status="COMPLETE")

        am = ArtifactManager(base_path=str(tmp_path / "experiments_fail"))

        result = verify_experiment(exp_id, manifest, idx, am)
        assert not result.passed

        idx.close()


class TestE2EPipeline:
    def test_full_matrix_cli(self):
        """Test E2E: manifest → run-matrix → verify."""
        manifest_path = "experiment_matrix.yaml"

        # Upewnij się, że manifest istnieje
        assert os.path.exists(manifest_path), f"Manifest {manifest_path} not found"

        # Uruchom matrix runner przez CLI
        result = subprocess.run(
            [sys.executable, "-m", "clos_cli", "run-matrix", manifest_path],
            capture_output=True, text=True, cwd=os.getcwd(),
            env={**os.environ, "PYTHONPATH": os.getcwd()},
            timeout=120,
        )

        assert result.returncode == 0, f"Matrix failed: {result.stderr[-500:]}"
        assert "MATRIX" in result.stdout
        assert "COMPLETE" in result.stdout
