"""Snapshot Engine – zapis pełnego stanu po każdym ticku.

Zapisuje stan Brain, Kernel i eksperymentu jako JSON.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Snapshot:
    """Pojedynczy snapshot stanu."""
    brain_id: str
    tick: int
    timestamp: str
    seed: Optional[int]
    lifecycle_state: str
    brain_status: str
    entropy: float
    energy: float
    age: int
    step_counter: int


class SnapshotEngine:
    """Silnik snapshotów.

    Po każdym ticku zapisuje pełny stan.
    """

    def __init__(self, storage_path: str = "storage/snapshots"):
        self.storage_path: Path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._snapshots: List[Snapshot] = []

    def create_snapshot(
        self,
        brain_id: str,
        tick: int,
        seed: Optional[int],
        lifecycle_state: str,
        brain_status: str,
        entropy: float,
        energy: float,
        age: int,
        step_counter: int
    ) -> Snapshot:
        """Utwórz nowy snapshot.

        Returns:
            Nowo utworzony snapshot.
        """
        snapshot = Snapshot(
            brain_id=brain_id,
            tick=tick,
            timestamp=datetime.now().isoformat(),
            seed=seed,
            lifecycle_state=lifecycle_state,
            brain_status=brain_status,
            entropy=entropy,
            energy=energy,
            age=age,
            step_counter=step_counter
        )
        self._snapshots.append(snapshot)
        return snapshot

    def save_to_file(self, experiment_id: str) -> Path:
        """Zapisz wszystkie snapshoty do pliku JSON.

        Args:
            experiment_id: ID eksperymentu.

        Returns:
            Ścieżka do zapisanego pliku.
        """
        filepath = self.storage_path / f"{experiment_id}.json"
        data = [asdict(s) for s in self._snapshots]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return filepath

    def load_from_file(self, experiment_id: str) -> List[Snapshot]:
        """Wczytaj snapshoty z pliku.

        Args:
            experiment_id: ID eksperymentu.

        Returns:
            Lista snapshotów.
        """
        filepath = self.storage_path / f"{experiment_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Plik {filepath} nie istnieje.")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._snapshots = [Snapshot(**item) for item in data]
        return self._snapshots

    def get_snapshot(self, tick: int) -> Optional[Snapshot]:
        """Pobierz snapshot dla danego ticka.

        Args:
            tick: Numer ticka.

        Returns:
            Snapshot lub None jeśli nie znaleziono.
        """
        for s in self._snapshots:
            if s.tick == tick:
                return s
        return None

    def get_all_snapshots(self) -> List[Snapshot]:
        """Pobierz wszystkie snapshoty.

        Returns:
            Lista wszystkich snapshotów.
        """
        return self._snapshots.copy()

    def clear(self) -> None:
        """Wyczyść wszystkie snapshoty."""
        self._snapshots.clear()
