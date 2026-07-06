"""Testy dla Control Tower."""

import pytest, sys, os
sys.path.insert(0, '.')
from clos_tower.integration.cli_bridge import run_demo_stream, run_demo_full


class TestCLIBridge:
    def test_run_demo_full(self):
        output = run_demo_full(seed=42, ticks=10)
        # v0.6 zwraca JSON
        assert "stability_score" in output

    def test_run_demo_stream_yields_ticks(self):
        ticks = list(run_demo_stream(seed=42, ticks=10))
        assert len(ticks) == 10

    def test_run_demo_stream_deterministic(self):
        ticks1 = list(run_demo_stream(seed=42, ticks=10))
        ticks2 = list(run_demo_stream(seed=42, ticks=10))
        for t1, t2 in zip(ticks1, ticks2):
            assert t1["tick"] == t2["tick"]
            assert t1["telemetry"]["entropy"] == t2["telemetry"]["entropy"]

    def test_stream_jsonl_format(self):
        ticks = list(run_demo_stream(seed=42, ticks=3))
        assert len(ticks) == 3
        assert ticks[0]["tick"] == 0
