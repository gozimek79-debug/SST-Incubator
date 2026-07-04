import pytest
import sys
sys.path.insert(0, '.')

from genome.gene import Gene, Dominance
from genome.genome import Genome
from genome.presets import create_default_genome, create_minimal_genome, create_highly_plastic_genome
from genome.engine import GenomeEngine

def test_gene_creation():
    gene = Gene(id="test", name="Test Gene", value=0.5)
    assert gene.id == "test"
    assert gene.value == 0.5
    assert gene.dominance == Dominance.RECESSIVE

def test_gene_expression():
    gene = Gene(id="test", name="Test Gene", value=42)
    assert gene.express() == 42

def test_genome_creation():
    genome = create_default_genome()
    assert len(genome.genes) == 8
    assert "memory_capacity" in genome.genes

def test_genome_expression():
    genome = create_default_genome()
    expressed = genome.express_all()
    assert expressed["memory_capacity"] == 100
    assert expressed["learning_rate"] == 0.1

def test_genome_mutation():
    genome = create_default_genome()
    original_value = genome.genes["learning_rate"].value
    for _ in range(1000):
        genome.mutate_all()
    assert genome.genes["learning_rate"].value != original_value

def test_genome_engine():
    engine = GenomeEngine()
    genome = engine.create_genome("default")
    assert genome.id == "default_v1"
    engine.save_genome(genome)
    loaded = engine.load_genome("default_v1")
    assert loaded is not None
    assert loaded.name == genome.name

def test_minimal_genome():
    genome = create_minimal_genome()
    assert len(genome.genes) == 3

def test_highly_plastic_genome():
    genome = create_highly_plastic_genome()
    assert genome.genes["plasticity"].value > 0.9
