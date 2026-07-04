"""Experiment Engine – orkiestracja analizy runu."""

from typing import List, Dict, Any
from clos_kernel.snapshot_engine import Snapshot
from clos_kernel.event_bus import Event
from .types import ExperimentResult
from .reporter import generate_report


def run_experiment(
    run_id: str,
    snapshots: List[Snapshot],
    events: List[Event],
    config: Dict[str, Any] = None
) -> ExperimentResult:
    """Uruchom analizę istniejącego runu.

    NIE wykonuje symulacji. Tylko analizuje snapshoty.

    Args:
        run_id: ID eksperymentu.
        snapshots: Lista snapshotów z Kernela.
        events: Lista zdarzeń z EventBus.
        config: Dodatkowa konfiguracja (opcjonalna).

    Returns:
        ExperimentResult z raportem i metadanymi.
    """
    report = generate_report(run_id, snapshots)

    return ExperimentResult(
        report=report,
        snapshots_count=len(snapshots),
        events_count=len(events),
        duration_ticks=snapshots[-1].tick if snapshots else 0
    )
