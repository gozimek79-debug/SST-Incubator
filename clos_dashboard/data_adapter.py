"""Data Adapter – konwertuje dane Scientist → format Dashboardu.

Zero obliczeń. Zero analiz. Tylko mapowanie.
"""

from typing import Dict, List, Any
from clos_scientist.types import ExperimentReport
from clos_kernel.snapshot_engine import Snapshot


def adapt_snapshots_to_chart(snapshots: List[Snapshot]) -> Dict[str, List[float]]:
    """Konwertuje snapshoty na dane wykresów.

    Args:
        snapshots: Lista snapshotów z Replay/SnapshotEngine.

    Returns:
        Słownik z listami: ticks, entropy, energy, step_counter.
    """
    return {
        "ticks": [s.tick for s in snapshots],
        "entropy": [s.entropy for s in snapshots],
        "energy": [s.energy for s in snapshots],
        "step_counter": [s.step_counter for s in snapshots],
    }


def adapt_snapshot_to_single(snapshot: Snapshot) -> Dict[str, Any]:
    """Konwertuje pojedynczy snapshot do słownika.

    Args:
        snapshot: Pojedynczy snapshot.

    Returns:
        Słownik z danymi snapshotu.
    """
    return {
        "tick": snapshot.tick,
        "entropy": snapshot.entropy,
        "energy": snapshot.energy,
        "step_counter": snapshot.step_counter,
        "lifecycle_state": snapshot.lifecycle_state,
        "brain_status": snapshot.brain_status,
    }


def adapt_report_to_display(report: ExperimentReport) -> Dict[str, Any]:
    """Konwertuje raport Scientist do formatu wyświetlania.

    Args:
        report: Raport z Scientist.

    Returns:
        Słownik z danymi do wyświetlenia.
    """
    return report.to_dict()
