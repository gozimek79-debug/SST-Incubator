"""Dashboard App – główna aplikacja (tekstowa, v0.1)."""

from clos_scientist.registry import ExperimentRegistry
from clos_kernel.snapshot_engine import SnapshotEngine
from clos_dashboard.telemetry_consumer import TelemetryConsumer
from clos_dashboard.data_adapter import adapt_snapshots_to_chart, adapt_snapshot_to_single
from clos_dashboard.replay import ReplayController
from clos_dashboard.layout import render_full_dashboard


class DashboardApp:
    """Główna aplikacja Dashboardu.

    Read-only. Zero analiz.
    """

    def __init__(self, registry: ExperimentRegistry):
        self.registry = registry
        self.telemetry = TelemetryConsumer(registry)
        self.snapshot_engine = SnapshotEngine()
        self.replay = ReplayController()
        self.selected_run_id = None

    def list_experiments(self):
        """Zwraca listę eksperymentów."""
        return self.telemetry.get_experiments_list()

    def select_experiment(self, run_id: str):
        """Wybierz eksperyment do wyświetlenia.

        Args:
            run_id: ID eksperymentu.
        """
        self.selected_run_id = run_id
        snapshots = self.telemetry.get_snapshots_for_experiment(run_id, self.snapshot_engine)
        self.replay.load_snapshots(snapshots)

    def get_dashboard_view(self, comparison_run_id: str = None) -> str:
        """Generuje widok dashboardu.

        Args:
            comparison_run_id: Opcjonalny ID drugiego eksperymentu do porównania.

        Returns:
            String z pełnym dashboardem.
        """
        experiments = self.list_experiments()
        selected_report = None
        chart_data = None
        replay_snapshot = None
        replay_min = 0
        replay_max = 0
        comparison_text = ""

        if self.selected_run_id:
            report = self.telemetry.get_report(self.selected_run_id)
            if report:
                selected_report = report.to_dict()
                snapshots = self.telemetry.get_snapshots_for_experiment(
                    self.selected_run_id, self.snapshot_engine
                )
                if snapshots:
                    chart_data = adapt_snapshots_to_chart(snapshots)
                    replay_snapshot = self.replay.get_current_snapshot()
                    replay_min = self.replay.min_tick
                    replay_max = self.replay.max_tick

            if comparison_run_id:
                try:
                    comparison_text = self.telemetry.get_comparison(
                        self.selected_run_id, comparison_run_id
                    )
                except KeyError:
                    comparison_text = f"Cannot compare: {comparison_run_id} not found"

        return render_full_dashboard(
            experiments=experiments,
            selected_report=selected_report,
            chart_data=chart_data,
            replay_snapshot=replay_snapshot,
            replay_min_tick=replay_min,
            replay_max_tick=replay_max,
            comparison_text=comparison_text,
        )

    def goto_replay_tick(self, tick: int):
        """Przejdź do konkretnego ticka w replay.

        Args:
            tick: Numer ticka.
        """
        self.replay.goto_tick(tick)
