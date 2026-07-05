"""Testy dla Control Tower v0.2."""

import pytest
import sys
import json
sys.path.insert(0, '.')

from clos_tower.integration.cli_bridge import run_demo_stream, run_demo_full


class TestCLIBridge:
    def test_run_demo_full(self):
        output = run_demo_full(seed=42, ticks=10)
        assert "DEMO COMPLETE" in output

    def test_run_demo_stream_yields_ticks(self):
        ticks = list(run_demo_stream(seed=42, ticks=10))
        assert len(ticks) == 10
        for tick_data in ticks:
            assert tick_data["event"] == "TICK"
            assert "tick" in tick_data
            assert "telemetry" in tick_data
            assert "entropy" in tick_data["telemetry"]
            assert "energy" in tick_data["telemetry"]

    def test_run_demo_stream_deterministic(self):
        ticks1 = list(run_demo_stream(seed=42, ticks=10))
        ticks2 = list(run_demo_stream(seed=42, ticks=10))

        for t1, t2 in zip(ticks1, ticks2):
            assert t1["tick"] == t2["tick"]
            assert t1["telemetry"]["entropy"] == t2["telemetry"]["entropy"]
            assert t1["telemetry"]["energy"] == t2["telemetry"]["energy"]

    def test_stream_jsonl_format(self):
        ticks = list(run_demo_stream(seed=42, ticks=3))
        assert len(ticks) == 3
        assert ticks[0]["tick"] == 0
        assert ticks[-1]["tick"] == 2
