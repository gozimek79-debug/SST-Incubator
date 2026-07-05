"""Replay – pobiera Snapshot dla konkretnego ticka.

Nie odtwarza Brain. Nie symuluje. Tylko renderuje snapshot.
"""

from typing import Optional
from clos_kernel.snapshot_engine import Snapshot


class ReplayController:
    """Kontroler replay – jedynie pobiera snapshoty."""

    def __init__(self):
        self._snapshots = []
        self._current_index = -1

    def load_snapshots(self, snapshots: list) -> None:
        """Wczytaj listę snapshotów.

        Args:
            snapshots: Lista snapshotów.
        """
        self._snapshots = sorted(snapshots, key=lambda s: s.tick)
        self._current_index = 0 if self._snapshots else -1

    def goto_tick(self, tick: int) -> Optional[Snapshot]:
        """Przejdź do konkretnego ticka.

        Args:
            tick: Numer ticka.

        Returns:
            Snapshot lub None.
        """
        for i, s in enumerate(self._snapshots):
            if s.tick == tick:
                self._current_index = i
                return s
        return None

    def get_current_snapshot(self) -> Optional[Snapshot]:
        """Pobierz aktualny snapshot.

        Returns:
            Aktualny snapshot lub None.
        """
        if 0 <= self._current_index < len(self._snapshots):
            return self._snapshots[self._current_index]
        return None

    @property
    def min_tick(self) -> int:
        """Minimalny tick."""
        return self._snapshots[0].tick if self._snapshots else 0

    @property
    def max_tick(self) -> int:
        """Maksymalny tick."""
        return self._snapshots[-1].tick if self._snapshots else 0

    @property
    def total_ticks(self) -> int:
        """Liczba snapshotów."""
        return len(self._snapshots)
