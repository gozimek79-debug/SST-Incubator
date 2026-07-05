"""Dataset Exporter – pakowanie artefaktów eksperymentu.

Nie wykonuje analiz. Nie tworzy raportów. Jedynie pakuje.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def export_dataset(
    benchmark_results: Dict[str, Any],
    stats: Dict[str, Any],
    manifest: Dict[str, Any],
    output_dir: str = "datasets",
    reports_dir: str = "reports"
) -> str:
    """Eksportuje kompletny dataset.

    Args:
        benchmark_results: Wynik z BenchmarkRunner.
        stats: Wynik walidacji statystycznej.
        manifest: Manifest eksperymentu.
        output_dir: Katalog wyjściowy.
        reports_dir: Katalog z raportami Scientist.

    Returns:
        Ścieżka do datasetu.
    """
    protocol_id = benchmark_results.get("protocol_id", "unknown")
    dataset_path = Path(output_dir) / protocol_id
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Zapisz manifest
    with open(dataset_path / "manifest.json", 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Zapisz statystyki
    with open(dataset_path / "benchmark.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # Zapisz metryki per-run
    metrics_path = dataset_path / "metrics"
    metrics_path.mkdir(exist_ok=True)

    for run in benchmark_results.get("runs", []):
        run_id = run["run_id"]
        run_data = {
            "run_id": run_id,
            "seed": run["seed"],
            "scenario": run["scenario"],
            "genome_preset": run["genome_preset"],
            "report": run["report"],
        }
        with open(metrics_path / f"{run_id}.json", 'w', encoding='utf-8') as f:
            json.dump(run_data, f, indent=2, ensure_ascii=False)

    # Kopiuj raporty Scientist jeśli istnieją
    reports_src = Path(reports_dir)
    reports_dst = dataset_path / "reports"
    if reports_src.exists():
        reports_dst.mkdir(exist_ok=True)
        for report_file in reports_src.glob(f"*{protocol_id}*"):
            shutil.copy2(report_file, reports_dst / report_file.name)

    return str(dataset_path)


def verify_dataset(dataset_path: str) -> Dict[str, bool]:
    """Weryfikuje kompletność datasetu.

    Args:
        dataset_path: Ścieżka do datasetu.

    Returns:
        Słownik z wynikami weryfikacji.
    """
    path = Path(dataset_path)
    checks = {
        "manifest_exists": (path / "manifest.json").exists(),
        "benchmark_exists": (path / "benchmark.json").exists(),
        "metrics_dir_exists": (path / "metrics").is_dir(),
    }

    if checks["metrics_dir_exists"]:
        metric_files = list((path / "metrics").glob("*.json"))
        checks["metrics_files_count"] = len(metric_files) > 0
    else:
        checks["metrics_files_count"] = False

    return checks
