"""Research Protocol – formalna definicja eksperymentu.

Jedyne źródło prawdy dla benchmarku.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class ResearchProtocol:
    """Protokół badawczy – definiuje co i jak badamy."""

    protocol_id: str
    description: str

    # Co badamy
    genome_id: str
    brain_id: str = ""
    scenario: str = "stable_world"
    genome_preset: str = "default"

    # Jak badamy
    seed_list: List[int] = field(default_factory=lambda: list(range(1, 11)))
    tick_count: int = 500

    # Co mierzymy
    metrics: List[str] = field(default_factory=lambda: [
        "stability_index", "mse", "entropy_volatility",
        "energy_drift", "memory_growth_rate"
    ])

    # Oczekiwania (Cognitive Assertions)
    assertions: Dict[str, Any] = field(default_factory=dict)

    # Wyjście
    dataset_name: str = "dataset_v01"
    version: str = "0.1"

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje protokół na słownik."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchProtocol":
        """Tworzy protokół ze słownika."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def get_experiment_matrix(self) -> List[Dict[str, Any]]:
        """Generuje macierz eksperymentów.

        Returns:
            Lista konfiguracji pojedynczych runów.
        """
        matrix = []
        for seed in self.seed_list:
            matrix.append({
                "protocol_id": self.protocol_id,
                "genome_preset": self.genome_preset,
                "genome_id": self.genome_id,
                "scenario": self.scenario,
                "seed": seed,
                "tick_count": self.tick_count,
                "brain_id": self.brain_id,
            })
        return matrix

    def summary(self) -> str:
        """Zwraca podsumowanie protokołu."""
        lines = [
            f"Protocol: {self.protocol_id}",
            f"Description: {self.description}",
            f"Genome: {self.genome_id} (preset: {self.genome_preset})",
            f"Scenario: {self.scenario}",
            f"Seeds: {len(self.seed_list)} ({self.seed_list[0]}..{self.seed_list[-1]})",
            f"Ticks: {self.tick_count}",
            f"Metrics: {', '.join(self.metrics)}",
            f"Dataset: {self.dataset_name}",
            f"Version: {self.version}",
        ]
        return "\n".join(lines)
