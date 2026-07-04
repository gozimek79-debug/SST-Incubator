from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional
from enum import Enum

class Dominance(Enum):
    RECESSIVE = "recessive"
    DOMINANT = "dominant"
    CO_DOMINANT = "co_dominant"

class Gene(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    dominance: Dominance = Dominance.RECESSIVE
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mutable: bool = True
    mutation_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    description: str = ""

    def mutate(self) -> bool:
        import random
        if not self.mutable:
            return False
        if random.random() < self.mutation_rate:
            if isinstance(self.value, (int, float)) and self.min_value is not None and self.max_value is not None:
                delta = (self.max_value - self.min_value) * 0.1
                self.value += random.uniform(-delta, delta)
                self.value = max(self.min_value, min(self.max_value, self.value))
            return True
        return False

    def express(self) -> Any:
        return self.value
