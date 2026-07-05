"""Benchmark Registry – rejestr benchmarków."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class BenchmarkRegistry:
    """Rejestr wykonanych benchmarków."""

    def __init__(self, storage_path: str = "storage/benchmark_registry.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._benchmarks: Dict[str, Dict[str, Any]] = {}
        self._load()

    def register(self, benchmark_id: str, data: Dict[str, Any]) -> None:
        """Zarejestruj benchmark.

        Args:
            benchmark_id: ID benchmarku.
            data: Dane benchmarku (wyniki, statystyki, manifest).
        """
        self._benchmarks[benchmark_id] = {
            "benchmark_id": benchmark_id,
            "protocol_id": data.get("protocol_id", ""),
            "dataset_name": data.get("manifest", {}).get("dataset_name", ""),
            "total_runs": data.get("total_runs", 0),
            "statistics_summary": {
                metric: {"mean": s["mean"], "ci95_low": s["ci95_low"], "ci95_high": s["ci95_high"]}
                for metric, s in data.get("statistics", {}).get("statistics", {}).items()
            },
            "regression_result": data.get("regression_result", "N/A"),
            "manifest": data.get("manifest", {}),
        }
        self._save()

    def get_benchmark(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        """Pobierz benchmark po ID."""
        return self._benchmarks.get(benchmark_id)

    def list_benchmarks(self) -> List[str]:
        """Lista ID benchmarków."""
        return list(self._benchmarks.keys())

    def compare_benchmarks(self, id_a: str, id_b: str) -> str:
        """Porównaj dwa benchmarki.

        Args:
            id_a: ID pierwszego benchmarku.
            id_b: ID drugiego benchmarku.

        Returns:
            Sformatowany tekst porównania.
        """
        bm_a = self._benchmarks.get(id_a)
        bm_b = self._benchmarks.get(id_b)

        if not bm_a or not bm_b:
            return "Cannot compare – one or both benchmarks not found."

        lines = [f"BENCHMARK COMPARISON: {id_a} vs {id_b}", "=" * 50]
        lines.append(f"{'Metric':<25} {id_a[:20]:>20} {id_b[:20]:>20}")

        stats_a = bm_a.get("statistics_summary", {})
        stats_b = bm_b.get("statistics_summary", {})

        all_metrics = set(list(stats_a.keys()) + list(stats_b.keys()))
        for metric in sorted(all_metrics):
            mean_a = stats_a.get(metric, {}).get("mean", "N/A")
            mean_b = stats_b.get(metric, {}).get("mean", "N/A")
            if isinstance(mean_a, float):
                mean_a = f"{mean_a:.4f}"
            if isinstance(mean_b, float):
                mean_b = f"{mean_b:.4f}"
            lines.append(f"{metric:<25} {str(mean_a):>20} {str(mean_b):>20}")

        return "\n".join(lines)

    def _save(self) -> None:
        """Zapisz rejestr do pliku."""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self._benchmarks, f, indent=2, ensure_ascii=False)

    def _load(self) -> None:
        """Wczytaj rejestr z pliku."""
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                self._benchmarks = json.load(f)
