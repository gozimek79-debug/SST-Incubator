"""Matrix Analyzer – analiza plików Parquet z eksperymentu macierzowego."""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np


def analyze_parquet_dataset(dataset_path: str) -> pd.DataFrame:
    """Wczytuje plik Parquet i zwraca DataFrame."""
    return pd.read_parquet(dataset_path)


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Oblicza zbiorcze statystyki dla grup genome-scenario.

    Args:
        df: DataFrame z kolumnami: genome, scenario, seed, status, mse, adaptation_tick, itd.

    Returns:
        DataFrame z kolumnami: GENOME, SCENARIO, MEAN_MSE, STD_MSE, MEAN_ADAPTATION_TICK.
    """
    # Upewnij się, że kolumny istnieją
    if "genome" not in df.columns:
        # Wyciągnij genome i scenario z config lub run_id
        genomes = []
        scenarios = []
        for _, row in df.iterrows():
            config = row.get("config", {})
            if isinstance(config, str):
                import json as _json
                try:
                    config = _json.loads(config)
                except:
                    config = {}
            genomes.append(config.get("genome", "unknown"))
            scenarios.append(config.get("scenario", "unknown"))
        df["genome"] = genomes
        df["scenario"] = scenarios

    # Grupuj
    grouped = df.groupby(["genome", "scenario"])

    results = []
    for (genome, scenario), group in grouped:
        # MSE proxy – użyj statusu jako liczbowej (COMPLETE=0, inaczej=1)
        if "mse" in group.columns:
            mse_values = group["mse"].dropna().astype(float)
        else:
            mse_values = pd.Series([0.0] * len(group))

        adaptation_ticks = group.get("adaptation_tick", pd.Series([0] * len(group)))

        results.append({
            "GENOME": genome,
            "SCENARIO": scenario,
            "MEAN_MSE": round(mse_values.mean(), 6) if len(mse_values) > 0 else 0.0,
            "STD_MSE": round(mse_values.std(), 6) if len(mse_values) > 1 else 0.0,
            "MEAN_ADAPTATION_TICK": round(adaptation_ticks.mean(), 1) if len(adaptation_ticks) > 0 else 0.0,
        })

    return pd.DataFrame(results)


def format_table(df: pd.DataFrame) -> str:
    """Formatuje DataFrame jako tabelę tekstową."""
    if df.empty:
        return "No data to display."

    col_widths = {
        "GENOME": 22,
        "SCENARIO": 16,
        "MEAN_MSE": 12,
        "STD_MSE": 12,
        "MEAN_ADAPTATION_TICK": 22,
    }

    header = "  ".join(f"{col:<{col_widths[col]}}" for col in df.columns)
    separator = "-" * len(header)
    rows = [header, separator]

    for _, row in df.iterrows():
        line = "  ".join(f"{str(row[col]):<{col_widths[col]}}" for col in df.columns)
        rows.append(line)

    return "\n".join(rows)


def analyze_experiment(experiment_id: str, base_path: str = "datasets") -> Dict[str, Any]:
    """Analizuje eksperyment i generuje raport.

    Args:
        experiment_id: ID eksperymentu.
        base_path: Katalog z datasetami.

    Returns:
        Słownik z wynikami analizy.
    """
    dataset_dir = Path(base_path) / experiment_id
    parquet_files = list(dataset_dir.glob("*.parquet"))

    if not parquet_files:
        return {"error": f"No Parquet files found in {dataset_dir}"}

    all_dfs = []
    for pf in parquet_files:
        df = analyze_parquet_dataset(str(pf))
        all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    summary = compute_summary(combined)

    return {
        "experiment_id": experiment_id,
        "files_analyzed": len(parquet_files),
        "total_runs": len(combined),
        "summary_table": summary.to_dict(orient="records"),
        "formatted_table": format_table(summary),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python matrix_analyzer.py <experiment_id> [datasets_path]")
        print("Example: python matrix_analyzer.py EXP-3A59D747")
        sys.exit(1)

    experiment_id = sys.argv[1]
    base_path = sys.argv[2] if len(sys.argv) > 2 else "datasets"

    print("=" * 80)
    print(f"CLOS Matrix Analyzer v0.5 – {experiment_id}")
    print("=" * 80)
    print()

    result = analyze_experiment(experiment_id, base_path)

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    print(f"Files analyzed: {result['files_analyzed']}")
    print(f"Total runs: {result['total_runs']}")
    print()
    print(result["formatted_table"])
    print()
    print("=" * 80)

    # Zapisz do JSON
    output_path = f"reports/{experiment_id}_analysis.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
