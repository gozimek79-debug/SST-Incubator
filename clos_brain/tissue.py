"""BrainTissue – struktura stanu poznawczego.

Brain jest wyłącznie kontenerem danych. Żadnej logiki.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MemoryRecord:
    """Pojedynczy ślad pamięciowy."""
    stimulus_hash: int
    prediction: float
    error: float
    timestamp_tick: int


@dataclass
class BrainTissue:
    """Stan poznawczy Brain.

    Wszystkie pola to surowe dane. Transformacje w osobnych modułach.
    """

    brain_id: str
    genome_id: str

    # Czas
    age: int = 0
    step_counter: int = 0

    # Energia i entropia
    energy: float = 1.0       # 0.0 – 1.0
    entropy: float = 0.0      # 0.0 – 1.0

    # Parametry z genomu
    plasticity: float = 0.5   # 0.0 – 1.0
    homeostasis_target: float = 0.5
    learning_rate: float = 0.1
    decay_rate: float = 0.01
    memory_capacity: int = 100
    prediction_depth: int = 3
    attention_threshold: float = 0.3
    meta_cognition_sensitivity: float = 0.5

    # Pamięć
    memory: List[MemoryRecord] = field(default_factory=list)
    sensory_buffer: List[float] = field(default_factory=list)

    # Bufory metryk (ostatnie N wartości)
    prediction_error_buffer: List[float] = field(default_factory=list)
    precision_history: List[float] = field(default_factory=list)
    entropy_history: List[float] = field(default_factory=list)
    energy_history: List[float] = field(default_factory=list)

    # Metryki pochodne
    precision: float = 0.5
    last_prediction: Optional[float] = None
    last_input: Optional[float] = None

    def summary(self) -> dict:
        """Zwraca podsumowanie stanu."""
        return {
            "brain_id": self.brain_id,
            "age": self.age,
            "energy": round(self.energy, 4),
            "entropy": round(self.entropy, 4),
            "precision": round(self.precision, 4),
            "plasticity": round(self.plasticity, 4),
            "memory_size": len(self.memory),
            "step": self.step_counter,
        }
