"""Manifest – pełna informacja do odtworzenia badań."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any


@dataclass
class ExperimentManifest:
    """Manifest eksperymentu – wszystko co potrzebne do odtworzenia."""

    dataset_version: str = "0.1"
    protocol_version: str = "0.1"
    benchmark_version: str = "0.1"

    kernel_version: str = "0.1"
    brain_version: str = "0.1"
    scientist_version: str = "0.1"
    dashboard_version: str = "0.1"
    build_version: str = "0.1"

    git_commit: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hash: str = ""

    seed_count: int = 0
    scenario_count: int = 0
    genome_count: int = 0

    protocol_id: str = ""
    dataset_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje manifest na słownik."""
        return asdict(self)

    def summary(self) -> str:
        """Zwraca podsumowanie manifestu."""
        lines = [
            "=" * 50,
            "EXPERIMENT MANIFEST",
            "=" * 50,
            f"Dataset:     {self.dataset_name} v{self.dataset_version}",
            f"Protocol:    {self.protocol_id}",
            f"Build:       v{self.build_version}",
            f"Git Commit:  {self.git_commit or 'N/A'}",
            f"Timestamp:   {self.timestamp}",
            f"Seeds:       {self.seed_count}",
            f"Scenarios:   {self.scenario_count}",
            f"Genomes:     {self.genome_count}",
            "=" * 50,
        ]
        return "\n".join(lines)
