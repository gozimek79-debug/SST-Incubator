"""Manifest Validator – sprawdza poprawność manifestu (MatrixManifest też)."""

from typing import List, Tuple
from .matrix_schema import MatrixManifest
from clos_world.scenarios import list_scenarios

VALID_GENOMES = ["default_v1", "minimal_v1", "highly_plastic_v1"]


class ManifestValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "\n".join(f"  - {e}" for e in errors)
        super().__init__(f"Manifest validation failed:\n{message}")


def validate_manifest(manifest) -> Tuple[bool, List[str]]:
    """Waliduje manifest (ExperimentManifest lub MatrixManifest).

    Args:
        manifest: Manifest do walidacji.

    Returns:
        (czy_poprawny, lista_błędów)
    """
    errors = []

    if manifest.schema_version < 1:
        errors.append("schema_version must be >= 1")

    if not manifest.experiment_id:
        errors.append("experiment.id is required")
    if not manifest.description:
        errors.append("experiment.description is required")

    if not manifest.genomes:
        errors.append("matrix.genomes cannot be empty")
    for genome in manifest.genomes:
        if genome not in VALID_GENOMES:
            errors.append(f"Invalid genome '{genome}'. Valid: {', '.join(VALID_GENOMES)}")

    if len(manifest.genomes) != len(set(manifest.genomes)):
        errors.append("Duplicate genomes in matrix.genomes")

    valid_scenarios = list_scenarios()
    if not manifest.scenarios:
        errors.append("matrix.scenarios cannot be empty")
    for scenario in manifest.scenarios:
        if scenario not in valid_scenarios:
            errors.append(f"Invalid scenario '{scenario}'. Valid: {', '.join(valid_scenarios)}")

    if len(manifest.scenarios) != len(set(manifest.scenarios)):
        errors.append("Duplicate scenarios in matrix.scenarios")

    if not manifest.seeds:
        errors.append("matrix.seeds cannot be empty")
    for seed in manifest.seeds:
        if not isinstance(seed, int) or seed < 0:
            errors.append(f"Invalid seed '{seed}'. Must be non-negative integer")

    if len(manifest.seeds) != len(set(manifest.seeds)):
        errors.append("Duplicate seeds in matrix.seeds")

    if manifest.ticks < 1:
        errors.append("ticks must be >= 1")

    return len(errors) == 0, errors


def validate_or_raise(manifest) -> bool:
    """Waliduje manifest lub rzuca wyjątek."""
    is_valid, errors = validate_manifest(manifest)
    if not is_valid:
        raise ManifestValidationError(errors)
    return True
