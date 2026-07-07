"""Testy dla CLI v0.7.3."""

import pytest, sys, os, subprocess
sys.path.insert(0, os.getcwd())

CLI_ENTRY = [sys.executable, "-m", "clos_cli"]

def test_cli_demo_runs():
    result = subprocess.run(CLI_ENTRY + ["demo", "--seed", "42", "--ticks", "20"], capture_output=True, text=True, cwd=os.getcwd())
    assert result.returncode == 0
    assert "stability_score" in result.stdout

def test_cli_demo_with_telemetry():
    result = subprocess.run(CLI_ENTRY + ["demo", "--seed", "42", "--ticks", "25", "--telemetry", "5"], capture_output=True, text=True, cwd=os.getcwd())
    assert result.returncode == 0
    assert "telemetry_count" in result.stdout

def test_cli_compare_runs():
    result = subprocess.run(CLI_ENTRY + ["compare", "--seed", "42", "--ticks", "20"], capture_output=True, text=True, cwd=os.getcwd())
    assert result.returncode == 0

def test_cli_benchmark_runs():
    result = subprocess.run(CLI_ENTRY + ["benchmark", "--seed", "42", "--ticks", "20"], capture_output=True, text=True, cwd=os.getcwd())
    assert result.returncode == 0

def test_cli_dashboard_runs():
    result = subprocess.run(CLI_ENTRY + ["dashboard", "--seed", "42", "--ticks", "20"], capture_output=True, text=True, cwd=os.getcwd())
    assert result.returncode == 0

def test_cli_help():
    result = subprocess.run(CLI_ENTRY + ["--help"], capture_output=True, text=True, cwd=os.getcwd())
    assert result.returncode == 0
