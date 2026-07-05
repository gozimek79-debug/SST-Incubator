"""CLOS v0.1 – Pełny benchmark (4 scenariusze x 5 seedów = 20 eksperymentów)."""

from clos_research.protocol import ResearchProtocol
from clos_research.benchmark_runner import BenchmarkRunner
from clos_research.statistical_validator import validate_benchmark, format_stats_report
from clos_research.regression_harness import create_default_harness
from clos_research.dataset_exporter import export_dataset
from clos_research.benchmark_registry import BenchmarkRegistry


def main(seed=42, ticks=200):
    print("=" * 60)
    print("CLOS v0.1 – FULL BENCHMARK")
    print("=" * 60)

    # Stwórz protokół
    protocol = ResearchProtocol(
        protocol_id="full_benchmark_v1",
        description="Pełny benchmark CLOS v0.1 – wszystkie scenariusze",
        genome_id="default_v1",
        genome_preset="default",
        scenario="stable_world",  # Bazowy, w v0.2 multi-scenario
        seed_list=[1, 2, 3, 4, 5],
        tick_count=ticks,
        dataset_name="benchmark_v1",
    )

    print(f"\nProtocol: {protocol.protocol_id}")
    print(f"Seeds: {protocol.seed_list}")
    print(f"Ticks per run: {protocol.tick_count}")
    print(f"Total runs: {len(protocol.seed_list)}")

    # Uruchom benchmark
    print("\n[1] Running benchmark...")
    runner = BenchmarkRunner()
    results = runner.run_protocol(protocol)
    print(f"    Completed: {results['total_runs']} runs")

    # Walidacja statystyczna
    print("\n[2] Statistical validation...")
    stats = validate_benchmark(results)
    print(format_stats_report(stats))

    # Regression Harness
    print("\n[3] Regression harness...")
    harness = create_default_harness()
    passed, report = harness.run_all(stats)
    print(report)

    # Eksport datasetu
    print("\n[4] Exporting dataset...")
    dataset_path = export_dataset(results, stats, results["manifest"])
    print(f"    Dataset exported to: {dataset_path}")

    # Rejestr benchmarków
    print("\n[5] Registering benchmark...")
    breg = BenchmarkRegistry()
    breg.register("full_benchmark_v1", {
        "protocol_id": protocol.protocol_id,
        "total_runs": results["total_runs"],
        "statistics": stats,
        "manifest": results["manifest"],
        "regression_result": "PASS" if passed else "FAIL",
    })
    print(f"    Registered: {breg.list_benchmarks()}")

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print(f"Regression: {'PASS' if passed else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
