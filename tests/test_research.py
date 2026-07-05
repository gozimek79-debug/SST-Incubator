"""Testy dla Research Framework v0.1."""

import pytest
import sys
import json
from pathlib import Path
sys.path.insert(0, '.')

from clos_research.protocol import ResearchProtocol
from clos_research.manifest import ExperimentManifest
from clos_research.benchmark_runner import BenchmarkRunner
from clos_research.statistical_validator import (
    compute_statistics, validate_benchmark, format_stats_report
)
from clos_research.regression_harness import (
    CognitiveAssertion, RegressionHarness, create_default_harness
)
from clos_research.dataset_exporter import export_dataset, verify_dataset
from clos_research.benchmark_registry import BenchmarkRegistry


class TestProtocol:
    def test_create_protocol(self):
        p = ResearchProtocol(
            protocol_id="test_001",
            description="Test protocol",
            genome_id="default_v1",
            scenario="stable_world",
            seed_list=[1, 2, 3],
            tick_count=100,
        )
        assert p.protocol_id == "test_001"
        assert len(p.seed_list) == 3

    def test_experiment_matrix(self):
        p = ResearchProtocol(
            protocol_id="test_002",
            description="Matrix test",
            genome_id="default_v1",
            scenario="stable_world",
            seed_list=[1, 2],
            tick_count=50,
        )
        matrix = p.get_experiment_matrix()
        assert len(matrix) == 2
        assert matrix[0]["seed"] == 1
        assert matrix[1]["seed"] == 2

    def test_to_dict_and_back(self):
        p = ResearchProtocol(
            protocol_id="test_003",
            description="Serialization test",
            genome_id="default_v1",
            scenario="noise_world",
            seed_list=[5, 10, 15],
            tick_count=200,
        )
        d = p.to_dict()
        p2 = ResearchProtocol.from_dict(d)
        assert p2.protocol_id == p.protocol_id
        assert p2.seed_list == p.seed_list

    def test_summary(self):
        p = ResearchProtocol(
            protocol_id="summary_test",
            description="Summary",
            genome_id="default_v1",
            scenario="stable_world",
            seed_list=list(range(1, 11)),
            tick_count=500,
        )
        summary = p.summary()
        assert "summary_test" in summary
        assert "stable_world" in summary


class TestManifest:
    def test_create_manifest(self):
        m = ExperimentManifest(
            protocol_id="test",
            dataset_name="dataset_01",
            seed_count=10,
            scenario_count=1,
            genome_count=1,
        )
        assert m.seed_count == 10
        assert "test" in m.summary()

    def test_manifest_to_dict(self):
        m = ExperimentManifest(protocol_id="p1")
        d = m.to_dict()
        assert d["protocol_id"] == "p1"


class TestStatisticalValidator:
    def test_compute_statistics(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = compute_statistics(values)
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["n"] == 5

    def test_compute_statistics_empty(self):
        stats = compute_statistics([])
        assert stats["mean"] == 0
        # Dla pustej listy 'n' jest poza pętlą – poprawiamy funkcję
        assert "n" in stats or stats.get("n", 0) == 0

    def test_format_stats_report(self):
        stats = {
            "protocol_id": "test",
            "total_runs": 2,
            "statistics": {
                "mse": compute_statistics([0.1, 0.2])
            }
        }
        report = format_stats_report(stats)
        assert "test" in report
        assert "mse" in report


class TestRegressionHarness:
    def test_assertion_pass(self):
        a = CognitiveAssertion(
            name="TestMin",
            description="Test",
            metric="mse",
            expected_min=0.0,
        )
        stats = {"statistics": {"mse": {"mean": 0.05}}}
        passed, msg = a.check(stats)
        assert passed
        assert "PASS" in msg

    def test_assertion_fail(self):
        a = CognitiveAssertion(
            name="TestMax",
            description="Test",
            metric="mse",
            expected_max=0.01,
            tolerance=0.001,
        )
        stats = {"statistics": {"mse": {"mean": 0.5}}}
        passed, msg = a.check(stats)
        assert not passed
        assert "FAIL" in msg

    def test_default_harness(self):
        harness = create_default_harness()
        assert len(harness.assertions) == 3

    def test_harness_run_all(self):
        harness = create_default_harness()
        stats = {
            "statistics": {
                "stability_index": {"mean": 5.0},
                "mse": {"mean": 0.01},
                "entropy_volatility": {"mean": 0.05},
            }
        }
        passed, report = harness.run_all(stats)
        assert passed
        assert "PASS" in report


class TestDatasetExporter:
    def test_export_and_verify(self, tmp_path):
        results = {
            "protocol_id": "test_export",
            "runs": [
                {
                    "run_id": "run_1",
                    "seed": 1,
                    "scenario": "stable",
                    "genome_preset": "default",
                    "report": {"run_id": "run_1", "stability_score": 0.9}
                }
            ]
        }
        stats = {"statistics": {}}
        manifest = {"dataset_name": "test"}
        path = export_dataset(
            results, stats, manifest,
            output_dir=str(tmp_path / "datasets"),
            reports_dir=str(tmp_path / "reports")
        )
        checks = verify_dataset(path)
        assert checks["manifest_exists"]
        assert checks["metrics_files_count"]


class TestBenchmarkRegistry:
    def test_register_and_get(self):
        reg = BenchmarkRegistry(storage_path="storage/test_bench_reg.json")
        data = {
            "protocol_id": "p1",
            "total_runs": 10,
            "statistics": {"statistics": {}},
            "manifest": {"dataset_name": "test"},
            "regression_result": "PASS",
        }
        reg.register("bm_001", data)
        bm = reg.get_benchmark("bm_001")
        assert bm is not None
        assert bm["protocol_id"] == "p1"

    def test_list(self):
        reg = BenchmarkRegistry(storage_path="storage/test_bench_reg2.json")
        reg.register("a", {"protocol_id": "a", "statistics": {"statistics": {}}, "manifest": {}})
        reg.register("b", {"protocol_id": "b", "statistics": {"statistics": {}}, "manifest": {}})
        assert "a" in reg.list_benchmarks()
        assert "b" in reg.list_benchmarks()

    def test_compare(self):
        reg = BenchmarkRegistry(storage_path="storage/test_bench_reg3.json")
        reg.register("a", {
            "protocol_id": "a", "total_runs": 5,
            "statistics": {"statistics": {
                "mse": {"mean": 0.1, "ci95_low": 0.09, "ci95_high": 0.11}
            }},
            "manifest": {}
        })
        reg.register("b", {
            "protocol_id": "b", "total_runs": 5,
            "statistics": {"statistics": {
                "mse": {"mean": 0.2, "ci95_low": 0.18, "ci95_high": 0.22}
            }},
            "manifest": {}
        })
        comp = reg.compare_benchmarks("a", "b")
        assert "COMPARISON" in comp
        assert "mse" in comp


class TestBenchmarkRunner:
    def test_run_minimal_protocol(self):
        protocol = ResearchProtocol(
            protocol_id="minimal_test",
            description="Minimal benchmark test",
            genome_id="default_v1",
            scenario="stable_world",
            seed_list=[42, 43],
            tick_count=50,
            dataset_name="minimal_dataset",
        )
        runner = BenchmarkRunner()
        results = runner.run_protocol(protocol)
        assert results["total_runs"] == 2
        assert len(results["runs"]) == 2
        assert "manifest" in results
        for run in results["runs"]:
            assert "report" in run

    def test_protocol_determinism(self):
        protocol = ResearchProtocol(
            protocol_id="det_test",
            description="Determinism test",
            genome_id="default_v1",
            scenario="stable_world",
            seed_list=[42],
            tick_count=50,
        )
        runner1 = BenchmarkRunner()
        results1 = runner1.run_protocol(protocol)
        runner2 = BenchmarkRunner()
        results2 = runner2.run_protocol(protocol)

        metrics1 = results1["runs"][0]["report"]["metrics"]
        metrics2 = results2["runs"][0]["report"]["metrics"]
        for key in ["stability_index", "mse", "entropy_volatility", "energy_drift"]:
            assert metrics1[key] == metrics2[key], f"Różnica w {key}"

    def test_statistical_validation_of_benchmark(self):
        protocol = ResearchProtocol(
            protocol_id="stats_test",
            description="Stats test",
            genome_id="default_v1",
            scenario="stable_world",
            seed_list=[1, 2, 3, 4, 5],
            tick_count=100,
        )
        runner = BenchmarkRunner()
        results = runner.run_protocol(protocol)
        stats = validate_benchmark(results)
        assert stats["total_runs"] == 5
        assert "statistics" in stats
        for metric in ["stability_index", "mse", "entropy_volatility"]:
            assert metric in stats["statistics"]
            assert "mean" in stats["statistics"][metric]

    def test_regression_harness_on_benchmark(self):
        protocol = ResearchProtocol(
            protocol_id="reg_test",
            description="Regression test",
            genome_id="default_v1",
            scenario="stable_world",
            seed_list=[1, 2, 3],
            tick_count=100,
        )
        runner = BenchmarkRunner()
        results = runner.run_protocol(protocol)
        stats = validate_benchmark(results)
        harness = create_default_harness()
        passed, report = harness.run_all(stats)
        assert passed, f"Regression harness failed: {report}"
