"""Provenance Model – historia pochodzenia eksperymentu."""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class ExperimentProvenance:
    """Pełna historia pochodzenia eksperymentu."""

    experiment_id: str
    parent_experiment: Optional[str] = None
    manifest_version: int = 1
    genome: str = ""
    scenario: str = ""
    seeds: list = field(default_factory=list)
    ticks: int = 500
    clos_version: str = "0.3"
    cli_version: str = "0.1.1"
    git_commit: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @staticmethod
    def compute_experiment_id(manifest_dict: Dict[str, Any], clos_version: str = "0.3") -> str:
        """Oblicza deterministyczny Experiment ID z manifestu.

        Args:
            manifest_dict: Manifest jako słownik.
            clos_version: Wersja CLOS.

        Returns:
            8-znakowy hex ID.
        """
        # Dodaj wersję CLOS do hashowania
        manifest_dict["_clos_version"] = clos_version

        # Stabilny hash – sortowanie kluczy
        canonical = json.dumps(manifest_dict, sort_keys=True, ensure_ascii=True)
        hash_hex = hashlib.sha256(canonical.encode()).hexdigest()
        return f"EXP-{hash_hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje proweniencję na słownik."""
        return asdict(self)

    def summary(self) -> str:
        """Zwraca podsumowanie proweniencji."""
        lines = [
            f"Experiment: {self.experiment_id}",
            f"Parent:     {self.parent_experiment or 'N/A'}",
            f"Genome:     {self.genome}",
            f"Scenario:   {self.scenario}",
            f"Seeds:      {len(self.seeds)} seeds",
            f"Ticks:      {self.ticks}",
            f"CLOS:       v{self.clos_version}",
            f"CLI:        v{self.cli_version}",
            f"Git:        {self.git_commit or 'N/A'}",
            f"Created:    {self.created_at}",
        ]
        return "\n".join(lines)
