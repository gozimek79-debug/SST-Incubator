"""Publication Bundle – tworzy kompletne archiwum eksperymentu."""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def build_bundle(
    experiment_id: str,
    manifest_dict: Dict[str, Any],
    provenance_dict: Dict[str, Any],
    results: list,
    artifacts_base: str = "experiments",
    output_dir: str = "publications",
) -> str:
    """Tworzy kompletne archiwum publikacyjne.

    Args:
        experiment_id: ID eksperymentu.
        manifest_dict: Manifest jako słownik.
        provenance_dict: Proweniencja jako słownik.
        results: Lista wyników runów.
        artifacts_base: Katalog z artefaktami.
        output_dir: Katalog wyjściowy.

    Returns:
        Ścieżka do archiwum.
    """
    bundle_path = Path(output_dir) / experiment_id
    bundle_path.mkdir(parents=True, exist_ok=True)

    # Manifest
    with open(bundle_path / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2, ensure_ascii=False)

    # Provenance
    with open(bundle_path / "provenance.json", "w", encoding="utf-8") as f:
        json.dump(provenance_dict, f, indent=2, ensure_ascii=False)

    # Results
    results_dir = bundle_path / "runs"
    results_dir.mkdir(exist_ok=True)
    for i, result in enumerate(results):
        with open(results_dir / f"run_{i:04d}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    # Metadata
    metadata = {
        "experiment_id": experiment_id,
        "git_commit": provenance_dict.get("git_commit", ""),
        "clos_version": provenance_dict.get("clos_version", ""),
        "cli_version": provenance_dict.get("cli_version", ""),
        "manifest_version": manifest_dict.get("schema_version", 1),
        "bundled_at": datetime.now().isoformat(),
        "total_runs": len(results),
    }
    with open(bundle_path / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Kopiuj istniejące artefakty
    artifacts_src = Path(artifacts_base) / experiment_id
    if artifacts_src.exists():
        artifacts_dst = bundle_path / "artifacts"
        shutil.copytree(artifacts_src, artifacts_dst, dirs_exist_ok=True)

    return str(bundle_path)
