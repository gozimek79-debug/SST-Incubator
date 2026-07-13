"""Telemetry Diagnostics - warunek 5 CTO (SPRINT_v0.10.md P5).

Wykrywa uszkodzona/niekompletna telemetrie snapshotow ZANIM metryki
(adaptation_tick, stability_score) zostana z niej policzone. Nie sprawdza
tylko count>0 - sprawdza monotonicznosc timeline, spojnosc timestampow i
kompletnosc sekwencji (brak dziur w tickach), bo `detect_phases()`/
`stability_index()` degeneruja cicho do zera przy count<20
(clos_scientist/analyzer.py, clos_scientist/metrics.py) i nie maja zadnej
ochrony przed poprzestawianymi/dziurawymi tickami.

Uzywane w dwoch miejscach (ta sama funkcja, jedna definicja prawdy):
  - clos_academy/lesson_L1_1.py / lesson_L1_2.py: licza diagnostyke RAZ, przy
    generowaniu raportu, i zapisuja jako "snapshot_diagnostics" per run.
  - scripts/validate_observability.py: czyta juz policzona diagnostyke z
    reports/academy/*.json (szybki, statyczny walidator CI - ten sam wzorzec
    co validate_artifacts.py/validate_publication.py), NIE re-uruchamia lekcji.
"""

from typing import Any, Dict, List, Sequence

# detect_phases() (clos_scientist/analyzer.py) zwraca same zera ponizej tej
# liczby snapshotow - patrz `if len(snapshots) < 20: return {...same zera}`.
EXPECTED_MINIMUM_SNAPSHOTS = 20


def _tick_of(s: Any):
    return s["tick"] if isinstance(s, dict) else s.tick


def _timestamp_of(s: Any):
    return s["timestamp"] if isinstance(s, dict) else s.timestamp


def diagnose_snapshot_sequence(snapshots: Sequence[Any],
                                expected_minimum: int = EXPECTED_MINIMUM_SNAPSHOTS) -> Dict[str, Any]:
    """Fakty o sekwencji snapshotow - nie rzuca wyjatkow, nie ocenia.

    monotonic=None/complete=None/timestamps_monotonic=None gdy count=0
    (pytanie nie ma sensu bez zadnego snapshotu - to jest stan C, nie
    'monotoniczne tak/nie').
    """
    count = len(snapshots)
    if count == 0:
        return {
            "count": 0, "first_tick": None, "last_tick": None,
            "monotonic": None, "complete": None, "timestamps_monotonic": None,
            "meets_minimum": False,
        }

    ticks = [_tick_of(s) for s in snapshots]
    timestamps = [_timestamp_of(s) for s in snapshots]

    monotonic = all(ticks[i] > ticks[i - 1] for i in range(1, len(ticks)))
    complete = monotonic and all(ticks[i] - ticks[i - 1] == 1 for i in range(1, len(ticks)))
    timestamps_monotonic = all(timestamps[i] >= timestamps[i - 1] for i in range(1, len(timestamps)))

    return {
        "count": count,
        "first_tick": ticks[0],
        "last_tick": ticks[-1],
        "monotonic": monotonic,
        "complete": complete,
        "timestamps_monotonic": timestamps_monotonic,
        "meets_minimum": count >= expected_minimum,
    }


def diagnostics_errors(diag: Dict[str, Any], label: str = "") -> List[str]:
    """Diagnostyka -> lista bledow (pusta = OK). Jedna funkcja, uzywana
    zarowno przez scripts/validate_observability.py jak i bezposrednio w
    testach - zaden inny kod nie duplikuje tej logiki."""
    prefix = f"{label}: " if label else ""
    errors: List[str] = []

    if diag.get("count", 0) == 0:
        errors.append(
            f"{prefix}0 snapshotow - metryka liczona bez zadnej telemetrii "
            "(stan C, blad infrastruktury)"
        )
        return errors

    if not diag.get("meets_minimum", False):
        errors.append(
            f"{prefix}snapshot_count={diag['count']} < expected_minimum "
            f"({EXPECTED_MINIMUM_SNAPSHOTS}) - detect_phases() zwraca same "
            "zera ponizej tego progu"
        )
    if diag.get("monotonic") is False:
        errors.append(f"{prefix}timeline niemonotoniczny (tick nie rosnie scisle)")
    if diag.get("complete") is False and diag.get("monotonic") is True:
        errors.append(f"{prefix}dziura w sekwencji tickow (brakuje co najmniej jednego ticka)")
    if diag.get("timestamps_monotonic") is False:
        errors.append(f"{prefix}timestampy snapshotow cofaja sie w czasie")

    return errors
