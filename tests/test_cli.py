"""Testy dla CLI."""

import pytest, sys, os, subprocess
sys.path.insert(0, '.')

CLI_ENTRY = [sys.executable, "-m", "clos_cli"]


def test_cli_demo_runs():
    result = subprocess.run(
        CLI_ENTRY + ["demo", "--seed", "42", "--ticks", "20"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    assert result.returncode == 0, f"STDERR: {result.stderr}"
    # v0.6 zwraca JSON, nie tekst
    assert "stability_score" in result.stdout

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
