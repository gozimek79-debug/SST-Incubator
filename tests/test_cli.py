"""Testy dla CLI v0.7.3."""

import pytest, sys, os, subprocess
sys.path.insert(0, os.getcwd())

CLI_ENTRY = [sys.executable, "-m", "clos_cli"]
# Katalog repo musi zostac na sciezce importu (subprocess nie dziedziczy sys.path
# ustawionego w tym procesie) - ale robocze cwd przenosimy do tmp_path, zeby
# artefakty pisane wzgledem cwd (np. run_benchmark.py -> datasets/full_benchmark_v1/
# manifest.json, storage/benchmark_registry.json) nie trafialy do sledzonego drzewa
# repo (audyt commita 661b92a, punkt 2).
_REPO_ROOT = os.getcwd()


def _run_cli(args, cwd):
    env = {**os.environ, "PYTHONPATH": _REPO_ROOT}
    return subprocess.run(CLI_ENTRY + args, capture_output=True, text=True, cwd=cwd, env=env)


def test_cli_demo_runs(tmp_path):
    result = _run_cli(["demo", "--seed", "42", "--ticks", "20"], cwd=tmp_path)
    assert result.returncode == 0
    assert "stability_score" in result.stdout

def test_cli_demo_with_telemetry(tmp_path):
    result = _run_cli(["demo", "--seed", "42", "--ticks", "25", "--telemetry", "5"], cwd=tmp_path)
    assert result.returncode == 0
    assert "telemetry_count" in result.stdout

def test_cli_compare_runs(tmp_path):
    result = _run_cli(["compare", "--seed", "42", "--ticks", "20"], cwd=tmp_path)
    assert result.returncode == 0

def test_cli_benchmark_runs(tmp_path):
    result = _run_cli(["benchmark", "--seed", "42", "--ticks", "20"], cwd=tmp_path)
    assert result.returncode == 0

def test_cli_dashboard_runs(tmp_path):
    result = _run_cli(["dashboard", "--seed", "42", "--ticks", "20"], cwd=tmp_path)
    assert result.returncode == 0

def test_cli_help(tmp_path):
    result = _run_cli(["--help"], cwd=tmp_path)
    assert result.returncode == 0
