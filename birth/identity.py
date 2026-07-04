from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
from typing import Optional

class BrainStatus(str, Enum):
    ALIVE = "ALIVE"
    SLEEPING = "SLEEPING"
    STRESSED = "STRESSED"
    DEAD = "DEAD"

class BrainIdentity(BaseModel):
    model_config = ConfigDict(frozen=False)

    brain_id: str
    genome_id: str
    genome_version: str
    generation: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    status: BrainStatus = BrainStatus.ALIVE

    def deactivate(self):
        self.status = BrainStatus.DEAD

    def summary(self) -> str:
        return (
            f"Brain {self.brain_id} | "
            f"Genome: {self.genome_id} v{self.genome_version} | "
            f"Gen {self.generation} | "
            f"Status: {self.status.value}"
        )
