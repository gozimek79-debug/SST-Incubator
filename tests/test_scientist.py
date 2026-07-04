"""Testy dla Scientist & Report Engine v0.1."""

import pytest
import sys
import json
sys.path.insert(0, '.')

from clos_kernel.snapshot_engine import SnapshotEngine, Snapshot
from clos_kernel.event_bus import EventBus, Event, SystemEvent
from clos_scientist.metrics import (
    stability_index, mse, energy_drift,
    entropy_volatility, memory_growth_rate, compute_all_metrics
)
from clos_scientist.analyzer import (
    detect_phases, detect_anomalies, compute_adaptation_speed
)
from clos_scientist.reporter import generate_report, format_text_report
from clos_scientist.experiment import run_experiment
from clos_scientist.registry import ExperimentRegistry
from clos_scientist.types import ExperimentReport


def make_snapshots(entropies=None, energies=None, start_tick=0):
    if entropies is None:
        entropies = [0.5] * 10
    if energies is None:
        energies = [1.0] * 10
    se = SnapshotEngine()
    for i, (ent, ene) in enumerate(zip(entropies, energies)):
        se.create_snapshot(
            brain_id="test_brain", tick=start_tick + i, seed=42,
            lifecycle_state="running", brain_status="ALIVE",
            entropy=ent, energy=ene, age=i, step_counter=i
        )
    return se.get_all_snapshots()


class TestMetrics:
    def test_stability_identical(self):
        snaps = make_snapshots(entropies=[0.5]*20, energies=[1.0]*20)
        assert stability_index(snaps) > 100

    def test_stability_volatile(self):
        snaps = make_snapshots(
            entropies=[0.1,0.9,0.2,0.8,0.3,0.7,0.4,0.6]*3,
            energies=[0.9]*24
        )
        assert stability_index(snaps) < 10

    def test_mse_perfect(self):
        snaps = make_snapshots(energies=[1.0]*10)
        assert mse(snaps) == 0.0

    def test_mse_imperfect(self):
        snaps = make_snapshots(energies=[0.5]*10)
        assert mse(snaps) > 0.0

    def test_energy_drift(self):
        snaps = make_snapshots(energies=[1.0, 0.9, 0.8, 0.7])
        drift = energy_drift(snaps)
        assert abs(drift - (-0.3)) < 1e-9

    def test_entropy_volatility_zero(self):
        snaps = make_snapshots(entropies=[0.5]*10)
        assert entropy_volatility(snaps) == 0.0

    def test_memory_growth_rate(self):
        snaps = make_snapshots(entropies=[0.5]*5, energies=[1.0]*5)
        assert memory_growth_rate(snaps) >= 0.0

    def test_compute_all(self):
        snaps = make_snapshots()
        m = compute_all_metrics(snaps)
        for k in ["stability_index","mse","energy_drift","entropy_volatility","memory_growth_rate"]:
            assert k in m


class TestAnalyzer:
    def test_detect_phases_keys(self):
        snaps = make_snapshots(entropies=[0.5]*100)
        phases = detect_phases(snaps)
        for k in ["initial_chaos","adaptation","convergence"]:
            assert k in phases

    def test_detect_anomalies_none(self):
        snaps = make_snapshots(entropies=[0.5]*50)
        assert detect_anomalies(snaps, threshold_sigma=2.0) == []

    def test_detect_anomalies_spike(self):
        e = [0.5]*50
        e[25] = 0.99
        snaps = make_snapshots(entropies=e, energies=[1.0]*51)
        anomalies = detect_anomalies(snaps, threshold_sigma=1.5)
        assert len(anomalies) > 0
        assert 25 in anomalies

    def test_adaptation_speed(self):
        snaps = make_snapshots(entropies=[0.5]*20)
        assert compute_adaptation_speed(snaps) >= 0


class TestReporter:
    def test_generate_report(self):
        snaps = make_snapshots()
        report = generate_report("test", snaps, output_dir="reports/test")
        assert isinstance(report, ExperimentReport)
        assert report.run_id == "test"

    def test_deterministic_json(self):
        snaps1 = make_snapshots()
        snaps2 = make_snapshots()
        r1 = generate_report("det", snaps1, output_dir="reports/test").to_dict()
        r2 = generate_report("det", snaps2, output_dir="reports/test").to_dict()
        assert r1 == r2

    def test_text_report(self):
        snaps = make_snapshots()
        report = generate_report("txt", snaps, output_dir="reports/test")
        text = format_text_report(report)
        assert "EXPERIMENT REPORT" in text
        assert "METRICS" in text

    def test_stable_vs_shock(self):
        s1 = make_snapshots(entropies=[0.5]*50, energies=[1.0]*50)
        e = [0.5]*50
        e[25] = 0.99
        s2 = make_snapshots(entropies=e, energies=[0.9]*51)
        r1 = generate_report("stable", s1, output_dir="reports/test")
        r2 = generate_report("shock", s2, output_dir="reports/test")
        assert r1.stability_score != r2.stability_score


class TestExperiment:
    def test_run_experiment(self):
        snaps = make_snapshots()
        bus = EventBus()
        bus.publish(Event(event_type=SystemEvent.TICK_STARTED, data={"tick":0}))
        result = run_experiment("exp", snaps, bus.get_history())
        assert result.snapshots_count == 10
        assert result.report.run_id == "exp"


class TestRegistry:
    def test_register_get(self):
        reg = ExperimentRegistry(storage_path="storage/test_reg.json")
        snaps = make_snapshots()
        report = generate_report("reg1", snaps, output_dir="reports/test")
        reg.register_experiment(report)
        assert reg.get_experiment("reg1").run_id == "reg1"

    def test_list(self):
        reg = ExperimentRegistry(storage_path="storage/test_reg2.json")
        snaps = make_snapshots()
        reg.register_experiment(generate_report("a", snaps, output_dir="reports/test"))
        reg.register_experiment(generate_report("b", snaps, output_dir="reports/test"))
        assert "a" in reg.list_experiments()
        assert "b" in reg.list_experiments()

    def test_compare_output(self):
        reg = ExperimentRegistry(storage_path="storage/test_reg3.json")
        s1 = make_snapshots(entropies=[0.5]*50, energies=[1.0]*50)
        e = [0.5]*50
        e[25] = 0.99
        s2 = make_snapshots(entropies=e, energies=[0.9]*51)
        reg.register_experiment(generate_report("stable", s1, output_dir="reports/test"))
        reg.register_experiment(generate_report("shock", s2, output_dir="reports/test"))
        comp = reg.compare("stable", "shock")
        assert "COMPARISON" in comp
        assert "stable" in comp
        assert "shock" in comp

    def test_compare_nonexistent(self):
        reg = ExperimentRegistry(storage_path="storage/test_reg4.json")
        with pytest.raises(KeyError):
            reg.compare("x", "y")

    def test_compare_deterministic(self):
        reg = ExperimentRegistry(storage_path="storage/test_reg5.json")
        snaps = make_snapshots()
        reg.register_experiment(generate_report("a", snaps, output_dir="reports/test"))
        reg.register_experiment(generate_report("b", snaps, output_dir="reports/test"))
        assert reg.compare("a","b") == reg.compare("a","b")
