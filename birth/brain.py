from .identity import BrainIdentity, BrainStatus
from .cognitive_state import CognitiveState
from .certificate import BirthCertificate
from typing import Dict, Any

class Brain:
    def __init__(
        self,
        brain_id: str,
        genome_id: str,
        genome_version: str,
        generation: int,
        expressed_genes: Dict[str, Any]
    ):
        self.identity = BrainIdentity(
            brain_id=brain_id,
            genome_id=genome_id,
            genome_version=genome_version,
            generation=generation
        )

        plasticity = expressed_genes.get("plasticity", 0.5)
        meta_cog = expressed_genes.get("meta_cognition_sensitivity", 0.5)
        homeostasis_target = expressed_genes.get("homeostasis_target", 0.5)

        self.cognitive_state = CognitiveState(
            plasticity=plasticity,
            meta_cognition=meta_cog,
            homeostasis=homeostasis_target
        )

        self.certificate = BirthCertificate(
            brain_id=brain_id,
            genome_id=genome_id,
            genome_version=genome_version,
            generation=generation,
            initial_energy=self.cognitive_state.energy,
            initial_homeostasis=self.cognitive_state.homeostasis,
            initial_plasticity=self.cognitive_state.plasticity,
            initial_meta_cognition=self.cognitive_state.meta_cognition
        )

        self.expressed_genes = expressed_genes

    def get_state(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.model_dump(),
            "cognitive_state": self.cognitive_state.summary(),
            "expressed_genes": self.expressed_genes
        }

    def summary(self) -> str:
        return (
            f"{self.identity.summary()}\n"
            f"Knowledge: {self.cognitive_state.knowledge} | "
            f"Experiences: {self.cognitive_state.experiences} | "
            f"Energy: {self.cognitive_state.energy}%"
        )
