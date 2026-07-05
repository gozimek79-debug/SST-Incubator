"""Statistical Validator – agregacja statystyczna wyników.

Pracuje wyłącznie na raportach Scientist.
Nie dotyka Brain. Nie wykonuje symulacji.
"""

import math
from typing import Dict, List, Any


def compute_statistics(values: List[float]) -> Dict[str, float]:
    """Oblicza statystyki dla listy wartości.

    Args:
        values: Lista wartości liczbowych.

    Returns:
        Słownik z mean, median, std, variance, min, max, ci95.
    """
    if not values:
        return {
            "mean": 0, "median": 0, "std": 0,
            "variance": 0, "min": 0, "max": 0, "ci95_low": 0, "ci95_high": 0
        }

    n = len(values)
    sorted_vals = sorted(values)
    mean = sum(values) / n

    # Mediana
    if n % 2 == 0:
        median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    else:
        median = sorted_vals[n // 2]

    # Wariancja i odchylenie standardowe
    variance = sum((v - mean) ** 2 for v in values) / (n - 1) if n > 1 else 0.0
    std = math.sqrt(variance)

    # 95% Confidence Interval
    if n > 1 and std > 0:
        ci95_margin = 1.96 * std / math.sqrt(n)
    else:
        ci95_margin = 0.0

    return {
        "mean": round(mean, 6),
        "median": round(median, 6),
        "std": round(std, 6),
        "variance": round(variance, 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "ci95_low": round(mean - ci95_margin, 6),
        "ci95_high": round(mean + ci95_margin, 6),
        "n": n,
    }


def validate_benchmark(benchmark_results: Dict[str, Any]) -> Dict[str, Any]:
    """Wykonaj walidację statystyczną benchmarku.

    Args:
        benchmark_results: Wynik z BenchmarkRunner.

    Returns:
        Słownik ze statystykami dla każdej metryki.
    """
    runs = benchmark_results.get("runs", [])
    if not runs:
        return {"error": "No runs in benchmark"}

    # Zbierz wartości metryk ze wszystkich runów
    metric_names = [
        "stability_index", "mse", "entropy_volatility",
        "energy_drift", "memory_growth_rate"
    ]

    stats = {}
    for metric in metric_names:
        values = []
        for run in runs:
            report = run.get("report", {})
            metrics = report.get("metrics", {})
            if metric in metrics:
                values.append(metrics[metric])

        if values:
            stats[metric] = compute_statistics(values)

    return {
        "protocol_id": benchmark_results.get("protocol_id"),
        "total_runs": len(runs),
        "statistics": stats,
    }


def format_stats_report(stats: Dict[str, Any]) -> str:
    """Formatuje raport statystyczny jako tekst.

    Args:
        stats: Wynik validate_benchmark.

    Returns:
        Sformatowany tekst.
    """
    lines = [
        "=" * 60,
        f"STATISTICAL VALIDATION: {stats.get('protocol_id', 'N/A')}",
        f"Total runs: {stats.get('total_runs', 0)}",
        "=" * 60,
    ]

    for metric, stat in stats.get("statistics", {}).items():
        lines.append(f"\n--- {metric} ---")
        lines.append(f"  Mean:     {stat['mean']:.6f}")
        lines.append(f"  Median:   {stat['median']:.6f}")
        lines.append(f"  Std:      {stat['std']:.6f}")
        lines.append(f"  Variance: {stat['variance']:.6f}")
        lines.append(f"  Min:      {stat['min']:.6f}")
        lines.append(f"  Max:      {stat['max']:.6f}")
        lines.append(f"  CI95:     [{stat['ci95_low']:.6f}, {stat['ci95_high']:.6f}]")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
