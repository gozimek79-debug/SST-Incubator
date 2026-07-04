from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List

class CognitiveState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    knowledge: float = 0.0
    experiences: int = 0
    memory: List[Any] = Field(default_factory=list)
    prediction_state: float = 0.0
    attention: float = 0.0
    plasticity: float = 0.5
    homeostasis: float = 0.5
    meta_cognition: float = 0.5
    entropy: float = 0.0
    energy: float = 100.0
    age: int = 0
    step_counter: int = 0

    def summary(self) -> Dict[str, Any]:
        return {
            "knowledge": self.knowledge,
            "experiences": self.experiences,
            "memory_size": len(self.memory),
            "prediction_state": self.prediction_state,
            "attention": self.attention,
            "plasticity": self.plasticity,
            "homeostasis": self.homeostasis,
            "meta_cognition": self.meta_cognition,
            "entropy": self.entropy,
            "energy": self.energy,
            "age": self.age,
            "step_counter": self.step_counter
        }
