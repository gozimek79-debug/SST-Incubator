"""Replay Engine – odtwarzanie historii eksperymentu.

Potrafi odczytać snapshoty, przejść do wybranego ticka, przeglądać historię.
"""

from typing import List, Optional
from .snapshot_engine import Snapshot, SnapshotEngine


class ReplayEngine:
    """Silnik odtwarzania.

    Na razie replay nie odtwarza świata – jedynie zapisane snapshoty.
    """

    def __init__(self, snapshot_engine: SnapshotEngine):
        self._snapshot_engine: SnapshotEngine = snapshot_engine
        self._current_index: int = -1

    def _get_snapshots(self) -> List[Snapshot]:
        """Pobierz snapshoty bezpośrednio z silnika."""
        return self._snapshot_engine.get_all_snapshots()

    def load(self, experiment_id: str) -> None:
        """Wczytaj snapshoty z pliku.

        Args:
            experiment_id: ID eksperymentu.
        """
        self._snapshot_engine.load_from_file(experiment_id)
        self._current_index = 0 if self._get_snapshots() else -1

    def goto_tick(self, tick: int) -> Optional[Snapshot]:
        """Przejdź do konkretnego ticka.

        Args:
            tick: Numer ticka.

        Returns:
            Snapshot dla danego ticka lub None.
        """
        snapshots = self._get_snapshots()
        for i, snapshot in enumerate(snapshots):
            if snapshot.tick == tick:
                self._current_index = i
                return snapshot
        return None

    def step_forward(self) -> Optional[Snapshot]:
        """Przejdź o jeden tick do przodu.

        Returns:
            Następny snapshot lub None jeśli koniec.
        """
        snapshots = self._get_snapshots()
        if self._current_index + 1 < len(snapshots):
            self._current_index += 1
            return snapshots[self._current_index]
        # Jeśli jeszcze nie zaczęliśmy, zacznij od pierwszego
        if self._current_index == -1 and snapshots:
            self._current_index = 0
            return snapshots[0]
        return None

    def step_back(self) -> Optional[Snapshot]:
        """Przejdź o jeden tick do tyłu.

        Returns:
            Poprzedni snapshot lub None jeśli początek.
        """
        snapshots = self._get_snapshots()
        if self._current_index - 1 >= 0:
            self._current_index -= 1
            return snapshots[self._current_index]
        return None

    def current_state(self) -> Optional[Snapshot]:
        """Pobierz aktualny stan.

        Returns:
            Aktualny snapshot lub None.
        """
        snapshots = self._get_snapshots()
        if 0 <= self._current_index < len(snapshots):
            return snapshots[self._current_index]
        return None

    @property
    def total_ticks(self) -> int:
        """Liczba wszystkich ticków."""
        return len(self._get_snapshots())

    @property
    def current_tick(self) -> int:
        """Aktualny numer ticka."""
        snapshot = self.current_state()
        return snapshot.tick if snapshot else -1
