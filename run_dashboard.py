"""CLOS v0.1 – Dashboard preview."""

from clos_research.benchmark_runner import BenchmarkRunner
from clos_research.protocol import ResearchProtocol
from clos_scientist.registry import ExperimentRegistry
from clos_dashboard.app import DashboardApp


def main(seed=42, ticks=100):
    # Najpierw uruchom mały benchmark
    print("Running benchmark for dashboard...")
    protocol = ResearchProtocol(
        protocol_id="dash_demo",
        description="Dashboard demo",
        genome_id="default_v1",
        scenario="stable_world",
        seed_list=[seed],
        tick_count=ticks,
    )
    runner = BenchmarkRunner()
    results = runner.run_protocol(protocol)

    # Użyj registry z benchmark runnera
    registry = runner.get_registry()

    # Dashboard
    print("\n" + "=" * 60)
    app = DashboardApp(registry)
    app.select_experiment(results["run_ids"][0])
    print(app.get_dashboard_view())


if __name__ == "__main__":
    main()
