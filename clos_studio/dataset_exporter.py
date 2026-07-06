"""Dataset Exporter – JSONL, CSV, Parquet."""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any


def export_jsonl(runs_data: List[Dict[str, Any]], output_path: str) -> str:
    """Eksportuje dane runów jako JSONL.

    Args:
        runs_data: Lista słowników z danymi runów.
        output_path: Ścieżka wyjściowa.

    Returns:
        Ścieżka do pliku.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for run in runs_data:
            f.write(json.dumps(run, ensure_ascii=False) + "\n")

    return str(path)


def export_csv(runs_data: List[Dict[str, Any]], output_path: str) -> str:
    """Eksportuje dane runów jako CSV.

    Args:
        runs_data: Lista słowników.
        output_path: Ścieżka wyjściowa.

    Returns:
        Ścieżka do pliku.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not runs_data:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return str(path)

    # Zbierz wszystkie klucze
    fieldnames = set()
    for run in runs_data:
        fieldnames.update(run.keys())
    fieldnames = sorted(fieldnames)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for run in runs_data:
            # Spłaszcz zagnieżdżone słowniki
            flat_run = {}
            for key, value in run.items():
                if isinstance(value, dict):
                    flat_run[key] = json.dumps(value)
                elif isinstance(value, list):
                    flat_run[key] = json.dumps(value)
                else:
                    flat_run[key] = value
            writer.writerow(flat_run)

    return str(path)


def export_parquet(runs_data: List[Dict[str, Any]], output_path: str) -> str:
    """Eksportuje dane runów jako Parquet.

    Args:
        runs_data: Lista słowników.
        output_path: Ścieżka wyjściowa.

    Returns:
        Ścieżka do pliku.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas required for Parquet export. Install: pip install pandas pyarrow")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not runs_data:
        pd.DataFrame().to_parquet(path)
        return str(path)

    df = pd.DataFrame(runs_data)
    df.to_parquet(path, index=False)
    return str(path)


def export_all_formats(runs_data: List[Dict[str, Any]], base_path: str) -> Dict[str, str]:
    """Eksportuje we wszystkich formatach.

    Args:
        runs_data: Lista słowników.
        base_path: Ścieżka bazowa (bez rozszerzenia).

    Returns:
        Słownik format → ścieżka.
    """
    return {
        "jsonl": export_jsonl(runs_data, f"{base_path}.jsonl"),
        "csv": export_csv(runs_data, f"{base_path}.csv"),
        "parquet": export_parquet(runs_data, f"{base_path}.parquet"),
    }
