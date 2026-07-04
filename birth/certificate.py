from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Dict, Any

class BirthCertificate(BaseModel):
    model_config = ConfigDict(frozen=True)

    brain_id: str
    genome_id: str
    genome_version: str
    generation: int
    created_at: datetime = Field(default_factory=datetime.now)
    initial_energy: float
    initial_homeostasis: float
    initial_plasticity: float
    initial_meta_cognition: float
    knowledge: float = 0.0
    experience_count: int = 0
    status: str = "ALIVE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brain_id": self.brain_id,
            "genome_id": self.genome_id,
            "genome_version": self.genome_version,
            "generation": self.generation,
            "created_at": self.created_at.isoformat(),
            "initial_energy": self.initial_energy,
            "initial_homeostasis": self.initial_homeostasis,
            "initial_plasticity": self.initial_plasticity,
            "initial_meta_cognition": self.initial_meta_cognition,
            "knowledge": self.knowledge,
            "experience_count": self.experience_count,
            "status": self.status
        }

    def display(self) -> str:
        lines = [
            "=" * 50,
            "BIRTH CERTIFICATE",
            "=" * 50,
            f"Brain ID:        {self.brain_id}",
            f"Genome ID:       {self.genome_id}",
            f"Genome Version:  {self.genome_version}",
            f"Generation:      {self.generation}",
            f"Created:         {self.created_at.isoformat()}",
            f"Initial Energy:  {self.initial_energy}",
            f"Homeostasis:     {self.initial_homeostasis}",
            f"Plasticity:      {self.initial_plasticity}",
            f"Meta-Cognition:  {self.initial_meta_cognition}",
            f"Knowledge:       {self.knowledge}",
            f"Experiences:     {self.experience_count}",
            f"Status:          {self.status}",
            "=" * 50
        ]
        return "\n".join(lines)
