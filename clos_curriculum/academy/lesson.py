"""Lesson Manifest – definicja eksperymentu edukacyjnego.

Każda lekcja jest kontrolowanym eksperymentem naukowym.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class LessonManifest:
    """Manifest lekcji – pełna definicja eksperymentu."""

    # Identyfikacja
    lesson_id: str
    level: int
    name: str
    description: str

    # Hipoteza badawcza
    hypothesis: str = ""
    research_question: str = ""

    # Środowisko eksperymentalne
    genome_presets: List[str] = field(default_factory=lambda: ["default"])
    scenarios: List[str] = field(default_factory=lambda: ["stable_world"])
    seeds: List[int] = field(default_factory=lambda: [42])
    ticks: int = 500

    # Endpointy
    primary_endpoint: str = "mse"  # Główna metryka
    secondary_endpoints: List[str] = field(default_factory=lambda: [
        "stability_score", "entropy_volatility", "energy_drift",
        "adaptation_tick", "memory_size"
    ])

    # Kryteria zaliczenia
    pass_conditions: Dict[str, Any] = field(default_factory=dict)
    fail_conditions: Dict[str, Any] = field(default_factory=dict)

    # Rygor naukowy
    min_seeds: int = 5
    min_ticks: int = 200
    required_ci95: bool = True
    required_effect_size: bool = True

    # Metadane
    version: str = "0.7"
    parent_lesson: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LessonManifest":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def validate_seeds(self) -> bool:
        """Sprawdza czy liczba seedów spełnia minimum."""
        return len(self.seeds) >= self.min_seeds

    def validate_ticks(self) -> bool:
        """Sprawdza czy liczba ticków spełnia minimum."""
        return self.ticks >= self.min_ticks

    def summary(self) -> str:
        lines = [
            f"Lesson: {self.lesson_id} (Level {self.level})",
            f"  Name: {self.name}",
            f"  Hypothesis: {self.hypothesis}",
            f"  Primary Endpoint: {self.primary_endpoint}",
            f"  Genomes: {self.genome_presets}",
            f"  Scenarios: {self.scenarios}",
            f"  Seeds: {len(self.seeds)} (min {self.min_seeds})",
            f"  Ticks: {self.ticks} (min {self.min_ticks})",
            f"  Rigor: CI95={self.required_ci95}, ES={self.required_effect_size}",
        ]
        return "\n".join(lines)
