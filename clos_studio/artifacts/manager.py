"""Artifact Manager – zapis i integralność artefaktów."""

import json
from pathlib import Path
from enum import Enum
from typing import Dict, Any, List


class ArtifactStatus(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    CORRUPTED = "CORRUPTED"
    MISSING = "MISSING"


class ArtifactManager:
    """Zarządca artefaktów eksperymentu."""

    def __init__(self, base_path: str = "experiments"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_experiment_dir(self, experiment_id: str) -> Path:
        """Zwraca ścieżkę do katalogu eksperymentu."""
        exp_dir = self.base_path / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)
        return exp_dir

    def save_manifest(self, experiment_id: str, manifest_dict: Dict[str, Any]) -> Path:
        """Zapisuje manifest."""
        exp_dir = self.get_experiment_dir(experiment_id)
        path = exp_dir / "manifest.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest_dict, f, indent=2, ensure_ascii=False)
        return path

    def save_run_result(self, experiment_id: str, run_id: str, result: Dict[str, Any]) -> Path:
        """Zapisuje wynik pojedynczego runu."""
        exp_dir = self.get_experiment_dir(experiment_id)
        runs_dir = exp_dir / "runs"
        runs_dir.mkdir(exist_ok=True)
        path = runs_dir / f"{run_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        return path

    def save_provenance(self, experiment_id: str, provenance_dict: Dict[str, Any]) -> Path:
        """Zapisuje proweniencję."""
        exp_dir = self.get_experiment_dir(experiment_id)
        path = exp_dir / "provenance.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(provenance_dict, f, indent=2, ensure_ascii=False)
        return path

    def check_integrity(self, experiment_id: str) -> Dict[str, ArtifactStatus]:
        """Sprawdza integralność artefaktów.

        Args:
            experiment_id: ID eksperymentu.

        Returns:
            Słownik artefakt -> status.
        """
        exp_dir = self.get_experiment_dir(experiment_id)
        checks = {}

        # Manifest
        manifest_path = exp_dir / "manifest.json"
        checks["manifest"] = (
            ArtifactStatus.COMPLETE if manifest_path.exists()
            else ArtifactStatus.MISSING
        )

        # Provenance
        prov_path = exp_dir / "provenance.json"
        checks["provenance"] = (
            ArtifactStatus.COMPLETE if prov_path.exists()
            else ArtifactStatus.MISSING
        )

        # Runs
        runs_dir = exp_dir / "runs"
        if runs_dir.is_dir():
            run_files = list(runs_dir.glob("*.json"))
            checks["runs"] = (
                ArtifactStatus.COMPLETE if run_files
                else ArtifactStatus.MISSING
            )
            checks["runs_count"] = len(run_files)
        else:
            checks["runs"] = ArtifactStatus.MISSING
            checks["runs_count"] = 0

        return checks

    def list_experiments(self) -> List[str]:
        """Lista wszystkich eksperymentów."""
        if not self.base_path.exists():
            return []
        return [
            d.name for d in self.base_path.iterdir()
            if d.is_dir() and d.name.startswith("EXP-")
        ]
