"""Testy dla Experiment Studio v0.3."""

import pytest
import sys
import json
import os
sys.path.insert(0, '.')

from clos_studio.manifest.schema import ExperimentManifest
from clos_studio.manifest.validator import validate_manifest, validate_or_raise, ManifestValidationError
from clos_studio.execution.queue import ExecutionQueue
from clos_studio.artifacts.manager import ArtifactManager, ArtifactStatus
from clos_studio.provenance.model import ExperimentProvenance
from clos_studio.publication.bundle import build_bundle


def make_valid_manifest_dict():
    return {
        "schema_version": 1,
        "experiment": {
            "id": "test_experiment",
            "description": "Test experiment for validation"
        },
        "matrix": {
            "genomes": ["default_v1"],
            "scenarios": ["stable_world", "shock_world"],
            "seeds": [1, 2, 3]
        },
        "ticks": 100
    }


class TestManifestSchema:
    def test_from_dict(self):
        data = make_valid_manifest_dict()
        manifest = ExperimentManifest.from_dict(data)
        assert manifest.experiment_id == "test_experiment"
        assert manifest.ticks == 100
        assert manifest.genomes == ["default_v1"]

    def test_to_dict(self):
        data = make_valid_manifest_dict()
        manifest = ExperimentManifest.from_dict(data)
        d = manifest.to_dict()
        assert d["experiment"]["id"] == "test_experiment"

    def test_run_matrix(self):
        data = make_valid_manifest_dict()
        data["matrix"]["genomes"] = ["default_v1"]
        data["matrix"]["scenarios"] = ["stable_world"]
        data["matrix"]["seeds"] = [1, 2]
        manifest = ExperimentManifest.from_dict(data)
        runs = manifest.get_run_matrix()
        assert len(runs) == 2
        assert runs[0]["genome"] == "default_v1"
        assert runs[0]["seed"] == 1


class TestManifestValidator:
    def test_valid_manifest(self):
        manifest = ExperimentManifest.from_dict(make_valid_manifest_dict())
        is_valid, errors = validate_manifest(manifest)
        assert is_valid
        assert len(errors) == 0

    def test_missing_experiment_id(self):
        data = make_valid_manifest_dict()
        data["experiment"]["id"] = ""
        manifest = ExperimentManifest.from_dict(data)
        is_valid, errors = validate_manifest(manifest)
        assert not is_valid

    def test_invalid_genome(self):
        data = make_valid_manifest_dict()
        data["matrix"]["genomes"] = ["invalid_genome"]
        manifest = ExperimentManifest.from_dict(data)
        is_valid, errors = validate_manifest(manifest)
        assert not is_valid

    def test_invalid_scenario(self):
        data = make_valid_manifest_dict()
        data["matrix"]["scenarios"] = ["invalid_scenario"]
        manifest = ExperimentManifest.from_dict(data)
        is_valid, errors = validate_manifest(manifest)
        assert not is_valid

    def test_duplicate_genomes(self):
        data = make_valid_manifest_dict()
        data["matrix"]["genomes"] = ["default_v1", "default_v1"]
        manifest = ExperimentManifest.from_dict(data)
        is_valid, errors = validate_manifest(manifest)
        assert not is_valid

    def test_validate_or_raise(self):
        manifest = ExperimentManifest.from_dict(make_valid_manifest_dict())
        assert validate_or_raise(manifest)

    def test_validate_or_raise_invalid(self):
        data = make_valid_manifest_dict()
        data["matrix"]["genomes"] = []
        manifest = ExperimentManifest.from_dict(data)
        with pytest.raises(ManifestValidationError):
            validate_or_raise(manifest)


class TestExecutionQueue:
    def test_queue_creation(self):
        manifest = ExperimentManifest.from_dict(make_valid_manifest_dict())
        queue = ExecutionQueue(manifest)
        assert queue.total_runs == 6  # 1 genome x 2 scenarios x 3 seeds

    def test_get_next(self):
        manifest = ExperimentManifest.from_dict(make_valid_manifest_dict())
        queue = ExecutionQueue(manifest)
        run = queue.get_next()
        assert run["genome"] == "default_v1"
        assert run["seed"] == 1

    def test_get_run_id(self):
        manifest = ExperimentManifest.from_dict(make_valid_manifest_dict())
        queue = ExecutionQueue(manifest)
        run_id = queue.get_run_id(0)
        assert "test_experiment" in run_id
        assert "default" in run_id
        assert "stable" in run_id
        assert "s1" in run_id


class TestProvenance:
    def test_compute_experiment_id(self):
        data = make_valid_manifest_dict()
        exp_id = ExperimentProvenance.compute_experiment_id(data)
        assert exp_id.startswith("EXP-")
        assert len(exp_id) == 12  # EXP- + 8 hex

    def test_deterministic_id(self):
        data = make_valid_manifest_dict()
        id1 = ExperimentProvenance.compute_experiment_id(data)
        id2 = ExperimentProvenance.compute_experiment_id(data)
        assert id1 == id2

    def test_different_manifest_different_id(self):
        data1 = make_valid_manifest_dict()
        data2 = make_valid_manifest_dict()
        data2["ticks"] = 200
        id1 = ExperimentProvenance.compute_experiment_id(data1)
        id2 = ExperimentProvenance.compute_experiment_id(data2)
        assert id1 != id2


class TestArtifactManager:
    def test_save_and_check_manifest(self, tmp_path):
        am = ArtifactManager(base_path=str(tmp_path / "experiments"))
        am.save_manifest("EXP-TEST1234", make_valid_manifest_dict())
        integrity = am.check_integrity("EXP-TEST1234")
        assert integrity["manifest"] == ArtifactStatus.COMPLETE

    def test_missing_experiment(self):
        am = ArtifactManager()
        integrity = am.check_integrity("EXP-NONEXIST")
        assert integrity["manifest"] == ArtifactStatus.MISSING


class TestPublicationBundle:
    def test_build_bundle(self, tmp_path):
        bundle_path = build_bundle(
            experiment_id="EXP-BUNDLE01",
            manifest_dict=make_valid_manifest_dict(),
            provenance_dict={"experiment_id": "EXP-BUNDLE01"},
            results=[{"run_id": "test", "status": "COMPLETE"}],
            artifacts_base=str(tmp_path / "experiments"),
            output_dir=str(tmp_path / "publications"),
        )
        assert os.path.exists(bundle_path)
        assert os.path.exists(os.path.join(bundle_path, "manifest.json"))
        assert os.path.exists(os.path.join(bundle_path, "metadata.json"))
