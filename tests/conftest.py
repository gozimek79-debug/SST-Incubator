"""Fixture wspoldzielone przez cala sesje testow.

Audyt commita 661b92a, punkt 2: pelny przebieg pytest brudzil trzy SLEDZONE pliki
(datasets/full_benchmark_v1/manifest.json, reports/shock_recovery_report.json,
storage/benchmark_registry.json) jako efekt uboczny wywolan run_pattern_echo()/
run_shock_recovery() (przez clos_scientist.experiment.run_experiment ->
generate_report(), ktora domyslnie pisze reports/{run_id}_report.json z FIXED
nazwa - kazdy test cwiczacy lekcje nadpisuje ten sam sledzony plik). Zadny test
nie zalezy od TRESCI tego pliku na dysku (tylko od zwracanego ExperimentResult) -
zweryfikowane grepem: zaden plik w tests/ nie otwiera reports/pattern_echo_report.json
ani reports/shock_recovery_report.json. Przekierowanie do tmp_path usuwa efekt
uboczny bez dotykania kodu produkcyjnego (clos_scientist/experiment.py nie jest
plikiem krytycznym PC-001, ale i tak nie jest tu modyfikowany - wystarczy
monkeypatch po stronie testow).
"""

import pytest

import clos_scientist.experiment as experiment_module


@pytest.fixture(autouse=True)
def _isolate_experiment_reports(tmp_path, monkeypatch):
    original_generate_report = experiment_module.generate_report

    def _redirected(run_id, snapshots, output_dir="reports"):
        target_dir = tmp_path / "reports" if output_dir == "reports" else output_dir
        return original_generate_report(run_id, snapshots, output_dir=str(target_dir))

    monkeypatch.setattr(experiment_module, "generate_report", _redirected)
    yield
