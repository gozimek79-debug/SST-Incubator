"""Execution Queue – rozbija manifest na atomowe runy."""

from typing import List, Dict, Any
from clos_studio.manifest.schema import ExperimentManifest


class ExecutionQueue:
    """Kolejka wykonawcza – sekwencyjna, bez równoległości."""

    def __init__(self, manifest: ExperimentManifest):
        self.manifest = manifest
        self.runs = manifest.get_run_matrix()
        self._current_index = 0

    @property
    def total_runs(self) -> int:
        """Liczba wszystkich runów."""
        return len(self.runs)

    @property
    def current_run(self) -> int:
        """Numer aktualnego runu (1-based)."""
        return self._current_index + 1

    @property
    def is_complete(self) -> bool:
        """Czy wszystkie runy wykonane."""
        return self._current_index >= len(self.runs)

    def get_next(self) -> Dict[str, Any]:
        """Pobierz następny run do wykonania.

        Returns:
            Konfiguracja runu.

        Raises:
            IndexError: Jeśli wszystkie runy wykonane.
        """
        if self.is_complete:
            raise IndexError("All runs already executed")
        run = self.runs[self._current_index]
        self._current_index += 1
        return run

    def get_run_id(self, run_index: int) -> str:
        """Generuje ID runu.

        Args:
            run_index: Indeks runu (0-based).

        Returns:
            ID runu w formacie: EXP_ID_genome_scenario_seedN.
        """
        run = self.runs[run_index]
        exp_id = self.manifest.experiment_id
        genome = run["genome"].replace("_v1", "")
        scenario = run["scenario"].replace("_world", "")
        seed = run["seed"]
        return f"{exp_id}_{genome}_{scenario}_s{seed}"

    def summary(self) -> str:
        """Podsumowanie kolejki."""
        lines = [
            f"Execution Queue: {self.manifest.experiment_id}",
            f"  Total runs: {self.total_runs}",
            f"  Genomes: {self.manifest.genomes}",
            f"  Scenarios: {self.manifest.scenarios}",
            f"  Seeds: {self.manifest.seeds}",
            f"  Ticks per run: {self.manifest.ticks}",
        ]
        return "\n".join(lines)
