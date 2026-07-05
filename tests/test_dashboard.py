"""Testy dla Dashboard Runtime v0.1."""

import pytest
import sys
import json
from pathlib import Path
sys.path.insert(0, '.')

from clos_kernel.snapshot_engine import SnapshotEngine
from clos_scientist.registry import ExperimentRegistry
from clos_scientist.reporter import generate_report
from clos_dashboard.telemetry_consumer import TelemetryConsumer
from clos_dashboard.replay import ReplayController
from clos_dashboard.data_adapter import (
    adapt_snapshots_to_chart,
    adapt_snapshot_to_single,
    adapt_report_to_display
)
from clos_dashboard.app import DashboardApp
from clos_dashboard.components.experiment_selector import (
    render_experiment_selector, render_metadata_panel, render_phase_overlay
)
from clos_dashboard.components.replay_slider import render_replay_slider
from clos_dashboard.components.comparison_panel import render_comparison_panel, render_report_panel


def make_snapshots(n=10):
    se = SnapshotEngine()
    for i in range(n):
        se.create_snapshot(
            brain_id="b1", tick=i, seed=42,
            lifecycle_state="running", brain_status="ALIVE",
            entropy=0.5, energy=1.0 - i*0.01, age=i, step_counter=i
        )
    return se.get_all_snapshots()


def make_registry_with_data():
    # Użyj unikalnej ścieżki per test
    import uuid
    path = f"storage/test_dash_{uuid.uuid4().hex[:8]}.json"
    reg = ExperimentRegistry(storage_path=path)
    snaps = make_snapshots(20)
    report = generate_report("dash_test", snaps, output_dir="reports/test")
    reg.register_experiment(report)
    return reg, snaps


class TestDataAdapter:
    def test_adapt_snapshots(self):
        snaps = make_snapshots(5)
        data = adapt_snapshots_to_chart(snaps)
        assert len(data["ticks"]) == 5
        assert len(data["entropy"]) == 5
        assert len(data["energy"]) == 5
        assert data["ticks"] == [0, 1, 2, 3, 4]

    def test_adapt_single_snapshot(self):
        snaps = make_snapshots(1)
        data = adapt_snapshot_to_single(snaps[0])
        assert data["tick"] == 0
        assert "entropy" in data
        assert "energy" in data

    def test_adapt_report(self):
        snaps = make_snapshots(10)
        report = generate_report("adapt_test", snaps, output_dir="reports/test")
        data = adapt_report_to_display(report)
        assert data["run_id"] == "adapt_test"


class TestTelemetryConsumer:
    def test_get_experiments(self):
        reg, _ = make_registry_with_data()
        tc = TelemetryConsumer(reg)
        exps = tc.get_experiments_list()
        assert len(exps) == 1

    def test_get_report(self):
        reg, _ = make_registry_with_data()
        tc = TelemetryConsumer(reg)
        report = tc.get_report("dash_test")
        assert report is not None
        assert report.run_id == "dash_test"

    def test_get_comparison(self):
        reg, _ = make_registry_with_data()
        snaps2 = make_snapshots(20)
        report2 = generate_report("dash_test2", snaps2, output_dir="reports/test")
        reg.register_experiment(report2)
        tc = TelemetryConsumer(reg)
        comp = tc.get_comparison("dash_test", "dash_test2")
        assert "COMPARISON" in comp


class TestReplay:
    def test_load_and_goto(self):
        snaps = make_snapshots(20)
        rc = ReplayController()
        rc.load_snapshots(snaps)
        assert rc.total_ticks == 20

        snap = rc.goto_tick(10)
        assert snap is not None
        assert snap.tick == 10

    def test_min_max(self):
        snaps = make_snapshots(20)
        rc = ReplayController()
        rc.load_snapshots(snaps)
        assert rc.min_tick == 0
        assert rc.max_tick == 19


class TestComponents:
    def test_experiment_selector(self):
        exps = [{"run_id": "test", "ticks": 10, "stability_score": 0.9, "mse": 0.01, "anomalies_count": 0}]
        text = render_experiment_selector(exps)
        assert "test" in text

    def test_experiment_selector_empty(self):
        text = render_experiment_selector([])
        assert "No experiments" in text

    def test_metadata_panel(self):
        report = {"run_id": "x", "stability_score": 0.5, "mse": 0.1, "adaptation_speed_ticks": 5, "phases": {}, "anomalies": []}
        text = render_metadata_panel(report)
        assert "x" in text

    def test_phase_overlay(self):
        report = {"phases": {"initial_chaos": 0, "adaptation": 10, "convergence": 30}}
        text = render_phase_overlay(report, 50)
        assert "adaptation" in text
        assert "convergence" in text

    def test_replay_slider(self):
        snaps = make_snapshots(5)
        text = render_replay_slider(snaps[2], 0, 4)
        assert "Tick 2" in text

    def test_replay_slider_none(self):
        text = render_replay_slider(None, 0, 0)
        assert "No snapshot" in text

    def test_comparison_panel(self):
        text = render_comparison_panel("COMPARISON: A vs B")
        assert "COMPARISON" in text

    def test_report_panel(self):
        report = {"run_id": "r", "stability_score": 0.5}
        text = render_report_panel(report)
        assert "r" in text
        assert "SCIENTIST REPORT" in text


class TestDashboardApp:
    def test_list_experiments(self):
        reg, _ = make_registry_with_data()
        app = DashboardApp(reg)
        exps = app.list_experiments()
        assert len(exps) == 1
        assert exps[0]["run_id"] == "dash_test"

    def test_select_and_view(self):
        reg, snaps = make_registry_with_data()
        # Zapisz snapshoty do pliku, żeby SnapshotEngine mógł je wczytać
        se = SnapshotEngine()
        for s in snaps:
            se.create_snapshot(s.brain_id, s.tick, s.seed or 0,
                              s.lifecycle_state, s.brain_status,
                              s.entropy, s.energy, s.age, s.step_counter)
        se.save_to_file("dash_test")

        app = DashboardApp(reg)
        app.select_experiment("dash_test")
        view = app.get_dashboard_view()
        assert "dash_test" in view

    def test_goto_replay(self):
        reg, snaps = make_registry_with_data()
        se = SnapshotEngine()
        for s in snaps:
            se.create_snapshot(s.brain_id, s.tick, s.seed or 0,
                              s.lifecycle_state, s.brain_status,
                              s.entropy, s.energy, s.age, s.step_counter)
        se.save_to_file("dash_test")

        app = DashboardApp(reg)
        app.select_experiment("dash_test")
        app.goto_replay_tick(5)
        snap = app.replay.get_current_snapshot()
        assert snap is not None

    def test_dashboard_readonly(self):
        reg, snaps = make_registry_with_data()
        se = SnapshotEngine()
        for s in snaps:
            se.create_snapshot(s.brain_id, s.tick, s.seed or 0,
                              s.lifecycle_state, s.brain_status,
                              s.entropy, s.energy, s.age, s.step_counter)
        se.save_to_file("dash_test")

        before = set(reg.list_experiments())
        app = DashboardApp(reg)
        app.select_experiment("dash_test")
        app.get_dashboard_view()
        after = set(reg.list_experiments())
        assert before == after
