from .genome import Genome
from .gene import Gene, Dominance

def create_default_genome() -> Genome:
    return Genome(
        id="default_v1",
        name="Default Genome v1",
        description="Standardowy genom dla CLOS v0.1",
        genes={
            "memory_capacity": Gene(
                id="memory_capacity",
                name="Pojemność pamięci",
                value=100,
                min_value=10,
                max_value=1000,
                dominance=Dominance.DOMINANT,
                mutation_rate=0.02,
                description="Maksymalna liczba elementów w pamięci"
            ),
            "learning_rate": Gene(
                id="learning_rate",
                name="Tempo uczenia",
                value=0.1,
                min_value=0.01,
                max_value=1.0,
                mutation_rate=0.05,
                description="Szybkość adaptacji"
            ),
            "prediction_depth": Gene(
                id="prediction_depth",
                name="Głębokość predykcji",
                value=3,
                min_value=1,
                max_value=10,
                dominance=Dominance.CO_DOMINANT,
                mutation_rate=0.01,
                description="Jak daleko w przyszłość Brain próbuje przewidywać"
            ),
            "homeostasis_target": Gene(
                id="homeostasis_target",
                name="Cel homeostazy",
                value=0.5,
                min_value=0.0,
                max_value=1.0,
                dominance=Dominance.RECESSIVE,
                mutation_rate=0.03,
                description="Optymalny poziom homeostazy"
            ),
            "plasticity": Gene(
                id="plasticity",
                name="Plastyczność",
                value=0.8,
                min_value=0.1,
                max_value=1.0,
                mutation_rate=0.04,
                description="Zdolność do reorganizacji połączeń"
            ),
            "decay_rate": Gene(
                id="decay_rate",
                name="Tempo zanikania pamięci",
                value=0.01,
                min_value=0.001,
                max_value=0.1,
                mutation_rate=0.02,
                description="Jak szybko zanikają nieużywane ślady pamięciowe"
            ),
            "attention_threshold": Gene(
                id="attention_threshold",
                name="Próg uwagi",
                value=0.3,
                min_value=0.0,
                max_value=1.0,
                mutation_rate=0.03,
                description="Minimalny poziom istotności bodźca"
            ),
            "meta_cognition_sensitivity": Gene(
                id="meta_cognition_sensitivity",
                name="Czułość metapoznania",
                value=0.5,
                min_value=0.1,
                max_value=1.0,
                dominance=Dominance.CO_DOMINANT,
                mutation_rate=0.02,
                description="Jak dokładnie Brain ocenia własną precyzję"
            )
        }
    )

def create_minimal_genome() -> Genome:
    return Genome(
        id="minimal_v1",
        name="Minimal Genome v1",
        description="Minimalny genom z podstawowymi genami",
        genes={
            "memory_capacity": Gene(id="memory_capacity", name="Pojemność pamięci", value=50, min_value=10, max_value=500),
            "learning_rate": Gene(id="learning_rate", name="Tempo uczenia", value=0.05, min_value=0.01, max_value=0.5),
            "homeostasis_target": Gene(id="homeostasis_target", name="Cel homeostazy", value=0.5, min_value=0.0, max_value=1.0)
        }
    )

def create_highly_plastic_genome() -> Genome:
    g = create_default_genome()
    g.id = "highly_plastic_v1"
    g.name = "Highly Plastic Genome v1"
    g.description = "Genom o podwyższonej plastyczności i tempie uczenia"
    g.genes["plasticity"].value = 0.95
    g.genes["learning_rate"].value = 0.3
    g.genes["memory_capacity"].value = 500
    g.genes["decay_rate"].value = 0.05
    return g
