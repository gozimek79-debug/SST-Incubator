import pytest
import sys
import json
from pathlib import Path
sys.path.insert(0, '.')

from genome.engine import GenomeEngine
from genome.presets import create_default_genome, create_minimal_genome
from birth.engine import BirthEngine
from birth.validator import GenomeValidator, GenomeValidationError
from birth.brain import Brain
from birth.certificate import BirthCertificate
from birth.identity import BrainStatus

@pytest.fixture
def genome_engine():
    return GenomeEngine()

@pytest.fixture
def birth_engine(genome_engine):
    return BirthEngine(genome_engine, log_path="storage/test_birth_log.json")

class TestGenomeValidator:
    def test_valid_default_genome(self):
        validator = GenomeValidator()
        genome = create_default_genome()
        is_valid, errors = validator.validate(genome)
        assert is_valid
        assert len(errors) == 0

    def test_missing_required_genes(self):
        validator = GenomeValidator()
        genome = create_minimal_genome()
        del genome.genes["memory_capacity"]
        is_valid, errors = validator.validate(genome)
        assert not is_valid
        assert any("memory_capacity" in e for e in errors)

    def test_invalid_range(self):
        validator = GenomeValidator()
        genome = create_default_genome()
        genome.genes["memory_capacity"].min_value = 100
        genome.genes["memory_capacity"].max_value = 10
        _, errors = validator.validate(genome)
        assert any("less than max" in e for e in errors)

    def test_value_outside_range(self):
        validator = GenomeValidator()
        genome = create_default_genome()
        genome.genes["memory_capacity"].value = 9999
        _, errors = validator.validate(genome)
        assert any("outside range" in e for e in errors)

    def test_validation_raises(self):
        validator = GenomeValidator()
        genome = create_default_genome()
        del genome.genes["memory_capacity"]
        with pytest.raises(GenomeValidationError):
            validator.validate_or_raise(genome)

class TestBirthEngine:
    def test_create_from_preset(self, birth_engine):
        brain = birth_engine.create_from_preset("default")
        assert brain.identity.status == BrainStatus.ALIVE
        assert brain.cognitive_state.knowledge == 0.0
        assert brain.cognitive_state.experiences == 0
        assert len(brain.cognitive_state.memory) == 0

    def test_unique_brain_ids(self, birth_engine):
        brain1 = birth_engine.create_from_preset("default")
        brain2 = birth_engine.create_from_preset("default")
        assert brain1.identity.brain_id != brain2.identity.brain_id

    def test_genome_expression_applied(self, birth_engine):
        brain = birth_engine.create_from_preset("highly_plastic")
        assert brain.cognitive_state.plasticity > 0.9
        assert "memory_capacity" in brain.expressed_genes

    def test_empty_memory(self, birth_engine):
        brain = birth_engine.create_from_preset("default")
        assert brain.cognitive_state.memory == []

    def test_zero_knowledge(self, birth_engine):
        brain = birth_engine.create_from_preset("default")
        assert brain.cognitive_state.knowledge == 0.0

    def test_birth_certificate(self, birth_engine):
        brain = birth_engine.create_from_preset("default")
        cert = brain.certificate
        assert cert.brain_id == brain.identity.brain_id
        assert cert.knowledge == 0.0
        assert cert.status == "ALIVE"

    def test_birth_logging(self, birth_engine):
        birth_engine.create_from_preset("default")
        log = birth_engine.get_log()
        assert len(log) >= 1
        assert "brain_id" in log[0]

    def test_list_births(self, birth_engine):
        birth_engine.create_from_preset("default")
        birth_engine.create_from_preset("minimal")
        births = birth_engine.list_births()
        assert len(births) == 2

    def test_get_brain(self, birth_engine):
        brain = birth_engine.create_from_preset("default")
        retrieved = birth_engine.get_brain(brain.identity.brain_id)
        assert retrieved is not None
        assert retrieved.identity.brain_id == brain.identity.brain_id

    def test_create_from_genome(self, birth_engine, genome_engine):
        genome = genome_engine.create_genome("default")
        brain = birth_engine.create_from_genome(genome)
        assert brain.identity.genome_id == genome.id

    def test_invalid_genome_rejected(self, birth_engine):
        genome = create_default_genome()
        genome.genes["memory_capacity"].min_value = 100
        genome.genes["memory_capacity"].max_value = 10
        with pytest.raises(GenomeValidationError):
            birth_engine.create_from_genome(genome)

    def test_initial_state_values(self, birth_engine):
        brain = birth_engine.create_from_preset("default")
        assert brain.cognitive_state.energy == 100.0
        assert brain.cognitive_state.age == 0
        assert brain.cognitive_state.step_counter == 0
        assert brain.cognitive_state.entropy == 0.0

    def test_certificate_display(self, birth_engine):
        brain = birth_engine.create_from_preset("default")
        display = brain.certificate.display()
        assert "BIRTH CERTIFICATE" in display
        assert brain.identity.brain_id in display

    def teardown_method(self):
        log_path = Path("storage/test_birth_log.json")
        if log_path.exists():
            log_path.unlink()
