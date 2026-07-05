"""Telemetry Consumer – pobiera dane z Registry, Snapshot, Replay.

Nie liczy. Nie analizuje. Tylko pobiera i przekazuje.
"""

from typing import Dict, List, Any, Optional
from clos_scientist.registry import ExperimentRegistry
from clos_scientist.types import ExperimentReport
from clos_kernel.snapshot_engine import SnapshotEngine, Snapshot
from clos_kernel.replay_engine import ReplayEngine


class TelemetryConsumer:
    """Konsument danych dla Dashboardu.

    Read-only. Zero analiz.
    """

    def __init__(self, registry: ExperimentRegistry):
        self.registry = registry

    def get_experiments_list(self) -> List[Dict[str, Any]]:
        """Pobiera listę eksperymentów z Registry.

        Returns:
            Lista słowników z podstawowymi informacjami.
        """
        experiments = []
        for run_id in self.registry.list_experiments():
            report = self.registry.get_experiment(run_id)
            if report:
                experiments.append({
                    "run_id": report.run_id,
                    "stability_score": report.stability_score,
                    "mse": report.mse,
                    "ticks": report.raw_summary.get("last_tick", 0),
                    "anomalies_count": len(report.anomalies),
                })
        return experiments

    def get_report(self, run_id: str) -> Optional[ExperimentReport]:
        """Pobiera raport Scientist dla danego eksperymentu.

        Args:
            run_id: ID eksperymentu.

        Returns:
            Raport lub None.
        """
        return self.registry.get_experiment(run_id)

    def get_snapshots_for_experiment(
        self, experiment_id: str, snapshot_engine: SnapshotEngine
    ) -> List[Snapshot]:
        """Pobiera snapshoty dla eksperymentu.

        Args:
            experiment_id: ID eksperymentu.
            snapshot_engine: Silnik snapshotów.

        Returns:
            Lista snapshotów.
        """
        try:
            return snapshot_engine.load_from_file(experiment_id)
        except FileNotFoundError:
            return []

    def get_snapshot_at_tick(
        self, experiment_id: str, tick: int, snapshot_engine: SnapshotEngine
    ) -> Optional[Snapshot]:
        """Pobiera konkretny snapshot.

        Args:
            experiment_id: ID eksperymentu.
            tick: Numer ticka.
            snapshot_engine: Silnik snapshotów.

        Returns:
            Snapshot lub None.
        """
        snapshots = self.get_snapshots_for_experiment(experiment_id, snapshot_engine)
        for s in snapshots:
            if s.tick == tick:
                return s
        return None

    def get_comparison(self, run_a: str, run_b: str) -> str:
        """Pobiera porównanie z Registry.

        Args:
            run_a: ID pierwszego eksperymentu.
            run_b: ID drugiego eksperymentu.

        Returns:
            Tekst porównania.
        """
        return self.registry.compare(run_a, run_b)
