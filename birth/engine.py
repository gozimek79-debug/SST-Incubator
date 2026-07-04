import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from genome.genome import Genome
from genome.engine import GenomeEngine
from .brain import Brain
from .validator import GenomeValidator, GenomeValidationError
from .certificate import BirthCertificate

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("BirthEngine")

class BirthEngine:
    def __init__(self, genome_engine: GenomeEngine, log_path: str = "storage/birth_log.json"):
        self.genome_engine = genome_engine
        self.validator = GenomeValidator()
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.births: Dict[str, Brain] = {}

    def create_from_preset(self, preset: str, generation: int = 1) -> Brain:
        genome = self.genome_engine.create_genome(preset)
        return self.create_from_genome(genome, generation)

    def create_from_genome(self, genome: Genome, generation: int = 1) -> Brain:
        self.validator.validate_or_raise(genome)

        brain_id = f"brain_{uuid.uuid4().hex[:12]}"
        expressed = genome.express_all()

        brain = Brain(
            brain_id=brain_id,
            genome_id=genome.id,
            genome_version=genome.version,
            generation=generation,
            expressed_genes=expressed
        )

        self.births[brain_id] = brain
        self._log_birth(brain, genome)
        logger.info(f"Brain born: {brain.summary()}")

        return brain

    def _log_birth(self, brain: Brain, genome: Genome):
        log_entry = {
            "brain_id": brain.identity.brain_id,
            "genome_id": genome.id,
            "genome_version": genome.version,
            "preset": genome.name,
            "generation": brain.identity.generation,
            "timestamp": brain.identity.created_at.isoformat(),
            "status": brain.identity.status.value,
            "plasticity": brain.cognitive_state.plasticity,
            "homeostasis": brain.cognitive_state.homeostasis,
            "meta_cognition": brain.cognitive_state.meta_cognition
        }

        existing_logs = []
        if self.log_path.exists():
            with open(self.log_path, 'r', encoding='utf-8') as f:
                try:
                    existing_logs = json.load(f)
                except json.JSONDecodeError:
                    existing_logs = []

        existing_logs.append(log_entry)

        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(existing_logs, f, indent=2, ensure_ascii=False, default=str)

    def get_brain(self, brain_id: str) -> Optional[Brain]:
        return self.births.get(brain_id)

    def get_certificate(self, brain_id: str) -> Optional[BirthCertificate]:
        brain = self.get_brain(brain_id)
        if brain:
            return brain.certificate
        return None

    def list_births(self) -> list:
        return [
            {
                "brain_id": bid,
                "genome": b.identity.genome_id,
                "status": b.identity.status.value,
                "created": b.identity.created_at.isoformat()
            }
            for bid, b in self.births.items()
        ]

    def get_log(self) -> list:
        if self.log_path.exists():
            with open(self.log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
