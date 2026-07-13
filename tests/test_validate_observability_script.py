"""Testy scripts/validate_observability.py (SPRINT_v0.10.md P5).

Test negatywny (warunek CTO): (a) 0 snapshotow, (b) snapshot_count<20,
(c) niemonotoniczny timeline, (d) dziura w sekwencji - kazdy z osobna
MUSI dac exit!=0. Plus (e) realny raport (juz w repo, po v0.10 P3) -> exit 0.
"""

import json

import scripts.validate_observability as validate_observability


def _snap(tick, timestamp="2026-01-01T00:00:00"):
    return {"tick": tick, "timestamp": timestamp}


def _sequence(n=30):
    return [_snap(t, f"2026-01-01T00:00:{t:02d}") for t in range(n)]


def _write_report(tmp_path, snapshot_diagnostics_list):
    """Zapisuje reports/academy/FAKE.json z jednym runem per wpis listy."""
    reports_dir = tmp_path / "reports" / "academy"
    reports_dir.mkdir(parents=True)
    results = []
    for i, diag in enumerate(snapshot_diagnostics_list):
        results.append({
            "run_id": f"FAKE_{i}", "genome": "default", "seed": i,
            "snapshot_diagnostics": diag,
        })
    report = {"lesson": "FAKE", "results": results, "baseline_results": []}
    with open(reports_dir / "FAKE_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f)
    return reports_dir


def _run_main_against(monkeypatch, reports_dir):
    monkeypatch.setattr(validate_observability, "REPORTS_DIR", reports_dir)
    return validate_observability.main()


class TestCaseA_ZeroSnapshots:
    def test_zero_snapshots_exit_nonzero(self, tmp_path, monkeypatch, capsys):
        from clos_scientist.telemetry import diagnose_snapshot_sequence
        diag = diagnose_snapshot_sequence([])
        reports_dir = _write_report(tmp_path, [diag])
        exit_code = _run_main_against(monkeypatch, reports_dir)
        assert exit_code != 0
        assert "0 snapshotow" in capsys.readouterr().out


class TestCaseB_BelowMinimum:
    def test_below_minimum_exit_nonzero(self, tmp_path, monkeypatch, capsys):
        from clos_scientist.telemetry import diagnose_snapshot_sequence
        diag = diagnose_snapshot_sequence(_sequence(10))
        reports_dir = _write_report(tmp_path, [diag])
        exit_code = _run_main_against(monkeypatch, reports_dir)
        assert exit_code != 0
        assert "expected_minimum" in capsys.readouterr().out


class TestCaseC_NonMonotonic:
    def test_non_monotonic_timeline_exit_nonzero(self, tmp_path, monkeypatch, capsys):
        from clos_scientist.telemetry import diagnose_snapshot_sequence
        seq = _sequence(30)
        seq[15] = _snap(13, seq[15]["timestamp"])
        diag = diagnose_snapshot_sequence(seq)
        reports_dir = _write_report(tmp_path, [diag])
        exit_code = _run_main_against(monkeypatch, reports_dir)
        assert exit_code != 0
        assert "niemonotoniczny" in capsys.readouterr().out


class TestCaseD_GapInSequence:
    def test_gap_in_sequence_exit_nonzero(self, tmp_path, monkeypatch, capsys):
        from clos_scientist.telemetry import diagnose_snapshot_sequence
        seq = [s for s in _sequence(30) if s["tick"] != 15]
        diag = diagnose_snapshot_sequence(seq)
        reports_dir = _write_report(tmp_path, [diag])
        exit_code = _run_main_against(monkeypatch, reports_dir)
        assert exit_code != 0
        assert "dziura" in capsys.readouterr().out


class TestCaseE_RealReportPasses:
    """Realne raporty juz w repo (reports/academy/, regenerowane w v0.10 P3)
    z prawdziwym Read-Only Observer - musza dac exit 0 bez zadnego patcha."""

    def test_real_committed_reports_pass(self, capsys):
        exit_code = validate_observability.main()
        assert exit_code == 0
        assert "OK" in capsys.readouterr().out


class TestMissingDiagnosticsField:
    """Run bez pola snapshot_diagnostics w ogole (raport sprzed P5) musi
    rowniez blokowac, nie byc cicho pomijany."""

    def test_missing_field_exit_nonzero(self, tmp_path, monkeypatch, capsys):
        reports_dir = tmp_path / "reports" / "academy"
        reports_dir.mkdir(parents=True)
        report = {
            "lesson": "FAKE", "results": [{"run_id": "FAKE_0", "genome": "default", "seed": 0}],
            "baseline_results": [],
        }
        with open(reports_dir / "FAKE_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f)
        exit_code = _run_main_against(monkeypatch, reports_dir)
        assert exit_code != 0
        assert "brak pola" in capsys.readouterr().out
