"""Testy dla CLI – sprawdzają tylko, czy komendy nie crashują."""

import pytest
import sys
import subprocess
import os

CLI_ENTRY = [sys.executable, "-m", "clos_cli"]


def test_cli_demo_runs():
    result = subprocess.run(
        CLI_ENTRY + ["demo", "--seed", "42", "--ticks", "20"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    assert result.returncode == 0, f"STDERR: {result.stderr}"
    assert "DEMO COMPLETE" in result.stdout


def test_cli_compare_runs():
    result = subprocess.run(
        CLI_ENTRY + ["compare", "--seed", "42", "--ticks", "20"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    assert result.returncode == 0
    assert "COMPARISON" in result.stdout


def test_cli_benchmark_runs():
    result = subprocess.run(
        CLI_ENTRY + ["benchmark", "--seed", "42", "--ticks", "20"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    assert result.returncode == 0
    assert "BENCHMARK COMPLETE" in result.stdout


def test_cli_dashboard_runs():
    result = subprocess.run(
        CLI_ENTRY + ["dashboard", "--seed", "42", "--ticks", "20"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    assert result.returncode == 0
    assert "EXPERIMENT" in result.stdout or "ENTROPY" in result.stdout


def test_cli_help():
    result = subprocess.run(
        CLI_ENTRY + ["--help"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    assert result.returncode == 0
    assert "demo" in result.stdout
