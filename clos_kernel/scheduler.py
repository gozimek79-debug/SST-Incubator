"""Scheduler – harmonogram uruchamiania modułów.

Trzy częstotliwości: FAST (co tick), MID (co 10), SLOW (co 100).
"""

from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class Frequency(str, Enum):
    """Częstotliwość wykonania."""
    FAST = "fast"    # co tick
    MID = "mid"      # co 10 ticków
    SLOW = "slow"    # co 100 ticków


class ScheduledTask:
    """Zadanie w harmonogramie."""

    def __init__(self, name: str, callback: Callable, frequency: Frequency):
        self.name: str = name
        self.callback: Callable = callback
        self.frequency: Frequency = frequency
        self.execution_count: int = 0

    @property
    def interval(self) -> int:
        """Interwał wykonania w tickach."""
        intervals = {
            Frequency.FAST: 1,
            Frequency.MID: 10,
            Frequency.SLOW: 100,
        }
        return intervals[self.frequency]

    def should_execute(self, tick_id: int) -> bool:
        """Sprawdź czy zadanie powinno się wykonać.

        Args:
            tick_id: Aktualny numer ticka.

        Returns:
            True jeśli zadanie powinno się wykonać.
        """
        if self.interval == 0:
            return False
        return tick_id % self.interval == 0


class Scheduler:
    """Harmonogram zadań.

    Uruchamia zadania zgodnie z ich częstotliwością.
    """

    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}

    def register(self, name: str, callback: Callable, frequency: Frequency) -> None:
        """Zarejestruj nowe zadanie.

        Args:
            name: Nazwa zadania.
            callback: Funkcja do wykonania.
            frequency: Częstotliwość wykonania.
        """
        self._tasks[name] = ScheduledTask(
            name=name,
            callback=callback,
            frequency=frequency
        )

    def unregister(self, name: str) -> None:
        """Usuń zadanie.

        Args:
            name: Nazwa zadania do usunięcia.
        """
        self._tasks.pop(name, None)

    def execute(self, tick_id: int) -> List[str]:
        """Wykonaj zadania zaplanowane na ten tick.

        Args:
            tick_id: Aktualny numer ticka.

        Returns:
            Lista nazw wykonanych zadań.
        """
        executed = []
        for task in self._tasks.values():
            if task.should_execute(tick_id):
                task.callback(tick_id)
                task.execution_count += 1
                executed.append(task.name)
        return executed

    def get_tasks(self) -> Dict[str, ScheduledTask]:
        """Pobierz wszystkie zarejestrowane zadania.

        Returns:
            Słownik nazwa → zadanie.
        """
        return self._tasks.copy()

    def clear(self) -> None:
        """Usuń wszystkie zadania."""
        self._tasks.clear()
