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
    # PC KROK 2: ta sama formula co Core (clos_brain/runtime/precision.py
    # compute_error: abs(last_prediction - last_input)), przeliczona przez
    # obserwatora z aktualnego stanu tissue - NIE czytana z
    # prediction_error_buffer (Core obcina go do 100 wpisow, patrz
    # precision.py:27). Dzieki temu snapshoty niosa pelna trajektorie przez
    # caly przebieg, nie tylko ostatnie 100 tickow.
    prediction_error: Optional[float] = None
    # PC-001 B2 (D-005 pkt 5, zasada O-001): WYLACZNIE surowe dane
    # obserwacyjne - tissue.last_prediction/last_input przekazane BEZ
    # przeliczania (zero confidence/uncertainty/hidden state/embedding).
    # Wymagane dla K5 (ablacja surogatowa - podmiana prediction na stala 0.5)
    # i K6 (korelacja Spearmana prediction/input) z ANEKSU 1 - bez tych
    # dwoch pol surowych obie kontrole sa niewykonalne (nie da sie ich
    # odtworzyc z samego prediction_error, bo |a-b| gubi znak i wartosci
    # zrodlowe).
    prediction: Optional[float] = None
    input: Optional[float] = None


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
        step_counter: int,
        prediction_error: Optional[float] = None,
        prediction: Optional[float] = None,
        input: Optional[float] = None
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
            step_counter=step_counter,
            prediction_error=prediction_error,
            prediction=prediction,
            input=input
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
