"""Manifest Schema – definicja struktury eksperymentu."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class ExperimentManifest:
    """Manifest eksperymentu – jedyne źródło prawdy."""

    schema_version: int = 1
    experiment: Dict[str, Any] = field(default_factory=dict)
    matrix: Dict[str, Any] = field(default_factory=dict)
    ticks: int = 500

    @property
    def experiment_id(self) -> str:
        """Generuje ID eksperymentu z manifestu."""
        if not self.experiment:
            return ""
        return self.experiment.get("id", "")

    @property
    def description(self) -> str:
        """Opis eksperymentu."""
        return self.experiment.get("description", "")

    @property
    def genomes(self) -> List[str]:
        """Lista genomów."""
        return self.matrix.get("genomes", [])

    @property
    def scenarios(self) -> List[str]:
        """Lista scenariuszy."""
        return self.matrix.get("scenarios", [])

    @property
    def seeds(self) -> List[int]:
        """Lista seedów."""
        return self.matrix.get("seeds", [])

    def get_run_matrix(self) -> List[Dict[str, Any]]:
        """Generuje macierz runów.

        Returns:
            Lista konfiguracji: genome x scenario x seed.
        """
        runs = []
        for genome in self.genomes:
            for scenario in self.scenarios:
                for seed in self.seeds:
                    runs.append({
                        "genome": genome,
                        "scenario": scenario,
                        "seed": seed,
                        "ticks": self.ticks,
                    })
        return runs

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje manifest do słownika."""
        return {
            "schema_version": self.schema_version,
            "experiment": self.experiment,
            "matrix": self.matrix,
            "ticks": self.ticks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentManifest":
        """Tworzy manifest ze słownika."""
        return cls(
            schema_version=data.get("schema_version", 1),
            experiment=data.get("experiment", {}),
            matrix=data.get("matrix", {}),
            ticks=data.get("ticks", 500),
        )

    @classmethod
    def from_yaml(cls, path: str) -> "ExperimentManifest":
        """Wczytuje manifest z pliku YAML."""
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_json(cls, path: str) -> "ExperimentManifest":
        """Wczytuje manifest z pliku JSON."""
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
