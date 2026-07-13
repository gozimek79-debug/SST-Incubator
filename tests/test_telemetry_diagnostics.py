"""Testy clos_scientist/telemetry.py (SPRINT_v0.10.md P5, warunek 5 CTO).

Diagnostyka sekwencji snapshotow - musi wykryc: brak snapshotow, ilosc
ponizej progu, niemonotoniczny timeline, dziure w sekwencji, cofajace sie
timestampy - kazde z osobna, bez mieszania przyczyn (kazdy blad ma wlasny,
odrebny komunikat).
"""

from clos_scientist.telemetry import (
    EXPECTED_MINIMUM_SNAPSHOTS,
    diagnose_snapshot_sequence,
    diagnostics_errors,
)


def _snap(tick, timestamp):
    return {"tick": tick, "timestamp": timestamp}


def _valid_sequence(n=30):
    """Sekwencja bez zarzutu: tick 0..n-1, timestampy scisle rosnace."""
    return [_snap(t, f"2026-01-01T00:00:{t:02d}") for t in range(n)]


class TestValidSequence:
    def test_valid_sequence_has_no_errors(self):
        diag = diagnose_snapshot_sequence(_valid_sequence())
        assert diagnostics_errors(diag) == []

    def test_valid_sequence_diagnostics_fields(self):
        diag = diagnose_snapshot_sequence(_valid_sequence(30))
        assert diag == {
            "count": 30, "first_tick": 0, "last_tick": 29,
            "monotonic": True, "complete": True, "timestamps_monotonic": True,
            "meets_minimum": True,
        }


class TestCaseA_ZeroSnapshots:
    """(a) 0 snapshotow pod metryka."""

    def test_zero_snapshots_is_error(self):
        diag = diagnose_snapshot_sequence([])
        assert diag["count"] == 0
        errors = diagnostics_errors(diag)
        assert len(errors) == 1
        assert "0 snapshotow" in errors[0]
        assert "stan C" in errors[0]

    def test_zero_snapshots_other_fields_are_none(self):
        diag = diagnose_snapshot_sequence([])
        assert diag["monotonic"] is None
        assert diag["complete"] is None
        assert diag["timestamps_monotonic"] is None
        assert diag["meets_minimum"] is False


class TestCaseB_BelowMinimum:
    """(b) snapshot_count < expected_minimum (20)."""

    def test_below_minimum_is_error(self):
        seq = _valid_sequence(EXPECTED_MINIMUM_SNAPSHOTS - 1)
        diag = diagnose_snapshot_sequence(seq)
        assert diag["meets_minimum"] is False
        errors = diagnostics_errors(diag)
        assert any("expected_minimum" in e for e in errors)

    def test_exactly_at_minimum_is_ok(self):
        seq = _valid_sequence(EXPECTED_MINIMUM_SNAPSHOTS)
        diag = diagnose_snapshot_sequence(seq)
        assert diag["meets_minimum"] is True
        assert diagnostics_errors(diag) == []


class TestCaseC_NonMonotonicTimeline:
    """(c) niemonotoniczny timeline (tick cofa sie lub sie powtarza)."""

    def test_tick_goes_backward_is_error(self):
        seq = _valid_sequence(30)
        # tick 15 cofa sie do wartosci ticka 13 (zamiast kontynuowac 14->15).
        seq[15] = _snap(13, seq[15]["timestamp"])
        diag = diagnose_snapshot_sequence(seq)
        assert diag["monotonic"] is False
        errors = diagnostics_errors(diag)
        assert any("niemonotoniczny" in e for e in errors)

    def test_duplicate_tick_is_error(self):
        seq = _valid_sequence(30)
        seq[10] = _snap(seq[9]["tick"], seq[10]["timestamp"])
        diag = diagnose_snapshot_sequence(seq)
        assert diag["monotonic"] is False
        assert any("niemonotoniczny" in e for e in diagnostics_errors(diag))


class TestCaseD_GapInSequence:
    """(d) dziura w sekwencji tickow (monotoniczny, ale brakuje ticka)."""

    def test_skipped_tick_is_error(self):
        seq = _valid_sequence(30)
        # Usun tick 15 z listy (0..14, 16..29) - nadal scisle rosnaco, ale z dziura.
        seq = [s for s in seq if s["tick"] != 15]
        diag = diagnose_snapshot_sequence(seq)
        assert diag["monotonic"] is True
        assert diag["complete"] is False
        errors = diagnostics_errors(diag)
        assert any("dziura" in e for e in errors)
        assert not any("niemonotoniczny" in e for e in errors), (
            "dziura w rosnacej sekwencji to nie to samo co niemonotonicznosc - "
            "nie mieszac przyczyn"
        )


class TestTimestampsGoBackward:
    """Cofajace sie timestampy - osobny warunek od monotonicznosci ticka."""

    def test_timestamp_regression_is_error(self):
        seq = _valid_sequence(30)
        seq[20] = _snap(seq[20]["tick"], "2025-01-01T00:00:00")  # znacznie wczesniej
        diag = diagnose_snapshot_sequence(seq)
        assert diag["timestamps_monotonic"] is False
        errors = diagnostics_errors(diag)
        assert any("timestampy" in e and "cofaja" in e for e in errors)

    def test_equal_consecutive_timestamps_are_not_an_error(self):
        """Rowne (nie malejace) timestampy sa dopuszczalne - rozdzielczosc
        zegara moze byc grubsza niz odstep miedzy tickami."""
        seq = _valid_sequence(30)
        seq[5] = _snap(seq[5]["tick"], seq[4]["timestamp"])
        diag = diagnose_snapshot_sequence(seq)
        assert diag["timestamps_monotonic"] is True
