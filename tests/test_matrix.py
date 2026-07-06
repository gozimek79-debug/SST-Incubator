"""Testy dla Matrix."""

import pytest, sys, os, json
sys.path.insert(0, '.')
from clos_studio.manifest.matrix_schema import MatrixManifest
from clos_studio.metadata_index import MetadataIndex
from clos_studio.artifacts.manager import ArtifactManager
from clos_studio.verify import verify_experiment


def make_matrix_manifest_dict():
    return {"schema_version":1,"experiment":{"id":"e2e_test","description":"Test"},"matrix":{"genomes":["default_v1"],"scenarios":["stable_world"],"seeds":[42,43]},"ticks":20,"workflow_version":"0.6","publish_on_verify":True}


class TestVerify:
    def test_verify_all_pass(self, tmp_path):
        data = make_matrix_manifest_dict()
        manifest = MatrixManifest.from_dict(data)
        exp_id = "EXP-VERIFY-PASS"
        db_path = str(tmp_path / "v.db")
        idx = MetadataIndex(db_path=db_path); idx.connect()
        idx.register_experiment(exp_id, manifest.to_dict(), workflow_version="0.6")
        for seed in [42,43]:
            idx.register_run(f"{exp_id}_default_stable_s{seed}", exp_id, "default_v1", "stable_world", seed, 20, "0.6", status="COMPLETE")
        am = ArtifactManager(base_path=str(tmp_path / "exp"))
        am.save_manifest(exp_id, manifest.to_dict())
        am.save_provenance(exp_id, {"experiment_id":exp_id})
        for seed in [42,43]:
            am.save_run_result(exp_id, f"{exp_id}_default_stable_s{seed}", {"status":"COMPLETE"})
        result = verify_experiment(exp_id, manifest, idx, am)
        assert result.passed
        idx.close()

    def test_verify_fails_on_missing_runs(self, tmp_path):
        data = make_matrix_manifest_dict()
        manifest = MatrixManifest.from_dict(data)
        exp_id = "EXP-VERIFY-FAIL"
        db_path = str(tmp_path / "vf.db")
        idx = MetadataIndex(db_path=db_path); idx.connect()
        idx.register_experiment(exp_id, manifest.to_dict())
        idx.register_run("run_1", exp_id, "default_v1", "stable_world", 42, 20, "0.4", status="COMPLETE")
        am = ArtifactManager(base_path=str(tmp_path / "expf"))
        result = verify_experiment(exp_id, manifest, idx, am)
        assert not result.passed
        idx.close()
