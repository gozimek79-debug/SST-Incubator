"""Matrix Analyzer v0.5 – analizuje dane z metrykami."""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np


def analyze_parquet_dataset(dataset_path: str) -> pd.DataFrame:
    return pd.read_parquet(dataset_path)


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "genome" not in df.columns or df["genome"].iloc[0] == "unknown":
        return pd.DataFrame()

    grouped = df.groupby(["genome", "scenario"])
    results = []
    for (genome, scenario), group in grouped:
        mse_vals = group["mse"].dropna().astype(float) if "mse" in group.columns else pd.Series([0.0])
        adapt_vals = group["adaptation_tick"].dropna().astype(float) if "adaptation_tick" in group.columns else pd.Series([0.0])
        stability_vals = group["stability_score"].dropna().astype(float) if "stability_score" in group.columns else pd.Series([0.0])

        results.append({
            "GENOME": genome,
            "SCENARIO": scenario,
            "MEAN_MSE": round(mse_vals.mean(), 6),
            "STD_MSE": round(mse_vals.std(), 6) if len(mse_vals) > 1 else 0.0,
            "MEAN_STABILITY": round(stability_vals.mean(), 4),
            "MEAN_ADAPTATION_TICK": round(adapt_vals.mean(), 1),
            "RUNS": len(group),
        })

    return pd.DataFrame(results)


def format_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No data. Run experiment first with v0.5 MatrixRunner."

    cols = ["GENOME", "SCENARIO", "MEAN_MSE", "STD_MSE", "MEAN_STABILITY", "MEAN_ADAPTATION_TICK", "RUNS"]
    widths = {"GENOME": 22, "SCENARIO": 16, "MEAN_MSE": 10, "STD_MSE": 10, "MEAN_STABILITY": 14, "MEAN_ADAPTATION_TICK": 20, "RUNS": 6}

    header = "  ".join(f"{c:<{widths[c]}}" for c in cols)
    sep = "-" * len(header)
    rows = [header, sep]
    for _, row in df.iterrows():
        rows.append("  ".join(f"{str(row[c]):<{widths[c]}}" for c in cols))
    return "\n".join(rows)


def analyze_experiment(experiment_id: str, base_path: str = "datasets") -> Dict[str, Any]:
    dataset_dir = Path(base_path) / experiment_id
    parquet_files = list(dataset_dir.glob("*.parquet"))

    if not parquet_files:
        return {"error": f"No Parquet files in {dataset_dir}. Run experiment first."}

    all_dfs = [analyze_parquet_dataset(str(pf)) for pf in parquet_files]
    combined = pd.concat(all_dfs, ignore_index=True)
    summary = compute_summary(combined)

    return {
        "experiment_id": experiment_id,
        "files_analyzed": len(parquet_files),
        "total_runs": len(combined),
        "summary_table": summary.to_dict(orient="records") if not summary.empty else [],
        "formatted_table": format_table(summary),
        "columns_found": list(combined.columns),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python matrix_analyzer.py <experiment_id>")
        sys.exit(1)

    experiment_id = sys.argv[1]
    print("=" * 90)
    print(f"CLOS Matrix Analyzer v0.5 – {experiment_id}")
    print("=" * 90)
    print()

    result = analyze_experiment(experiment_id)

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    print(f"Files: {result['files_analyzed']} | Runs: {result['total_runs']}")
    print(f"Columns found: {result['columns_found']}")
    print()
    print(result["formatted_table"])
    print()
    print("=" * 90)

    output_path = f"reports/{experiment_id}_analysis.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"Report saved: {output_path}")


if __name__ == "__main__":
    main()
