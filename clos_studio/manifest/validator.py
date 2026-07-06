"""Manifest Validator – sprawdza poprawność manifestu."""

from typing import List, Tuple
from .schema import ExperimentManifest
from genome.presets import create_default_genome, create_minimal_genome, create_highly_plastic_genome
from clos_world.scenarios import list_scenarios

VALID_GENOMES = ["default_v1", "minimal_v1", "highly_plastic_v1"]


class ManifestValidationError(Exception):
    """Błąd walidacji manifestu."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "\n".join(f"  - {e}" for e in errors)
        super().__init__(f"Manifest validation failed:\n{message}")


def validate_manifest(manifest: ExperimentManifest) -> Tuple[bool, List[str]]:
    """Waliduje manifest eksperymentu.

    Args:
        manifest: Manifest do walidacji.

    Returns:
        (czy_poprawny, lista_błędów)
    """
    errors = []

    # Schema version
    if manifest.schema_version < 1:
        errors.append("schema_version must be >= 1")

    # Required fields
    if not manifest.experiment_id:
        errors.append("experiment.id is required")
    if not manifest.description:
        errors.append("experiment.description is required")

    # Genomes
    if not manifest.genomes:
        errors.append("matrix.genomes cannot be empty")
    for genome in manifest.genomes:
        if genome not in VALID_GENOMES:
            errors.append(
                f"Invalid genome '{genome}'. Valid: {', '.join(VALID_GENOMES)}"
            )

    # Check duplicates in genomes
    if len(manifest.genomes) != len(set(manifest.genomes)):
        errors.append("Duplicate genomes in matrix.genomes")

    # Scenarios
    valid_scenarios = list_scenarios()
    if not manifest.scenarios:
        errors.append("matrix.scenarios cannot be empty")
    for scenario in manifest.scenarios:
        if scenario not in valid_scenarios:
            errors.append(
                f"Invalid scenario '{scenario}'. Valid: {', '.join(valid_scenarios)}"
            )

    if len(manifest.scenarios) != len(set(manifest.scenarios)):
        errors.append("Duplicate scenarios in matrix.scenarios")

    # Seeds
    if not manifest.seeds:
        errors.append("matrix.seeds cannot be empty")
    for seed in manifest.seeds:
        if not isinstance(seed, int) or seed < 0:
            errors.append(f"Invalid seed '{seed}'. Must be non-negative integer")

    if len(manifest.seeds) != len(set(manifest.seeds)):
        errors.append("Duplicate seeds in matrix.seeds")

    # Ticks
    if manifest.ticks < 1:
        errors.append("ticks must be >= 1")

    return len(errors) == 0, errors


def validate_or_raise(manifest: ExperimentManifest) -> bool:
    """Waliduje manifest lub rzuca wyjątek.

    Args:
        manifest: Manifest do walidacji.

    Returns:
        True jeśli poprawny.

    Raises:
        ManifestValidationError: Jeśli manifest niepoprawny.
    """
    is_valid, errors = validate_manifest(manifest)
    if not is_valid:
        raise ManifestValidationError(errors)
    return True
