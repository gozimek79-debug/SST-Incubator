"""Event Bus – komunikacja między modułami przez zdarzenia.

Zero zależności między modułami. Future-proof.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List


class SystemEvent(str, Enum):
    """Standardowe zdarzenia systemu CLOS."""
    TICK_STARTED = "tick_started"
    TICK_FINISHED = "tick_finished"
    SNAPSHOT_CREATED = "snapshot_created"
    LIFECYCLE_CHANGED = "lifecycle_changed"
    BRAIN_BORN = "brain_born"
    BRAIN_DIED = "brain_died"


@dataclass
class Event:
    """Zdarzenie w systemie."""
    event_type: SystemEvent
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""


class EventBus:
    """Centralny system zdarzeń.

    Moduły komunikują się wyłącznie przez EventBus.
    """

    def __init__(self):
        self._subscribers: Dict[SystemEvent, List[Callable]] = {
            event_type: [] for event_type in SystemEvent
        }
        self._history: List[Event] = []

    def subscribe(self, event_type: SystemEvent, callback: Callable) -> None:
        """Subskrybuj typ zdarzenia.

        Args:
            event_type: Typ zdarzenia do nasłuchiwania.
            callback: Funkcja wywoływana przy zdarzeniu.
        """
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: SystemEvent, callback: Callable) -> None:
        """Anuluj subskrypcję.

        Args:
            event_type: Typ zdarzenia.
            callback: Funkcja do usunięcia.
        """
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event) -> None:
        """Opublikuj zdarzenie.

        Args:
            event: Zdarzenie do rozesłania.
        """
        self._history.append(event)
        for callback in self._subscribers[event.event_type]:
            callback(event)

    def get_history(self, event_type: SystemEvent = None) -> List[Event]:
        """Pobierz historię zdarzeń.

        Args:
            event_type: Opcjonalny filtr typu zdarzenia.

        Returns:
            Lista zdarzeń.
        """
        if event_type is not None:
            return [e for e in self._history if e.event_type == event_type]
        return self._history.copy()

    def clear_history(self) -> None:
        """Wyczyść historię zdarzeń."""
        self._history.clear()
