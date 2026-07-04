from typing import List, Tuple
from genome.genome import Genome
from genome.gene import Gene

class GenomeValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "\n".join([f"  - {e}" for e in errors])
        super().__init__(f"Genome validation failed:\n{message}")

class GenomeValidator:
    REQUIRED_GENES = {
        "memory_capacity",
        "learning_rate",
        "homeostasis_target"
    }

    RECOMMENDED_GENES = {
        "prediction_depth",
        "plasticity",
        "decay_rate",
        "attention_threshold",
        "meta_cognition_sensitivity"
    }

    def validate(self, genome: Genome) -> Tuple[bool, List[str]]:
        errors = []

        missing_required = self.REQUIRED_GENES - set(genome.genes.keys())
        if missing_required:
            errors.append(
                f"Missing required genes: {', '.join(sorted(missing_required))}"
            )

        missing_recommended = self.RECOMMENDED_GENES - set(genome.genes.keys())
        if missing_recommended:
            errors.append(
                f"Missing recommended genes: {', '.join(sorted(missing_recommended))}"
            )

        for gene_id, gene in genome.genes.items():
            gene_errors = self._validate_gene(gene_id, gene)
            errors.extend(gene_errors)

        is_valid = len([e for e in errors if "recommended" not in e.lower()]) == 0
        return is_valid, errors

    def _validate_gene(self, gene_id: str, gene: Gene) -> List[str]:
        errors = []

        if gene.min_value is not None and gene.max_value is not None:
            if gene.min_value >= gene.max_value:
                errors.append(
                    f"Gene '{gene_id}': min_value ({gene.min_value}) "
                    f"must be less than max_value ({gene.max_value})"
                )
            if gene.value < gene.min_value or gene.value > gene.max_value:
                errors.append(
                    f"Gene '{gene_id}': value ({gene.value}) "
                    f"outside range [{gene.min_value}, {gene.max_value}]"
                )

        if gene.mutation_rate < 0 or gene.mutation_rate > 1:
            errors.append(
                f"Gene '{gene_id}': mutation_rate must be between 0 and 1"
            )

        return errors

    def validate_or_raise(self, genome: Genome) -> bool:
        is_valid, errors = self.validate(genome)
        if not is_valid:
            raise GenomeValidationError(errors)
        return True
