"""Lifecycle Manager – cykl życia organizmu.

Walidowane przejścia między stanami BIRTH → RUNNING → SLEEPING → DEAD.
"""

from enum import Enum, auto
from typing import Dict, List, Optional


class LifecycleState(str, Enum):
    """Stany cyklu życia."""
    BIRTH = "birth"
    RUNNING = "running"
    SLEEPING = "sleeping"
    DEAD = "dead"


class LifecycleError(Exception):
    """Błąd niepoprawnego przejścia stanu."""
    pass


class Lifecycle:
    """Zarządca cyklu życia.

    Dozwolone przejścia:
        BIRTH → RUNNING
        BIRTH → DEAD
        RUNNING → SLEEPING
        RUNNING → DEAD
        SLEEPING → RUNNING
        SLEEPING → DEAD
    """

    VALID_TRANSITIONS: Dict[LifecycleState, List[LifecycleState]] = {
        LifecycleState.BIRTH: [LifecycleState.RUNNING, LifecycleState.DEAD],
        LifecycleState.RUNNING: [LifecycleState.SLEEPING, LifecycleState.DEAD],
        LifecycleState.SLEEPING: [LifecycleState.RUNNING, LifecycleState.DEAD],
        LifecycleState.DEAD: [],  # Stan terminalny
    }

    def __init__(self):
        self._state: LifecycleState = LifecycleState.BIRTH
        self._history: List[LifecycleState] = [self._state]

    @property
    def state(self) -> LifecycleState:
        """Aktualny stan."""
        return self._state

    @property
    def is_alive(self) -> bool:
        """Czy organizm żyje."""
        return self._state != LifecycleState.DEAD

    @property
    def history(self) -> List[LifecycleState]:
        """Historia stanów."""
        return self._history.copy()

    def can_transition(self, target: LifecycleState) -> bool:
        """Sprawdź czy przejście jest dozwolone.

        Args:
            target: Docelowy stan.

        Returns:
            True jeśli przejście jest dozwolone.
        """
        return target in self.VALID_TRANSITIONS.get(self._state, [])

    def transition(self, target: LifecycleState) -> None:
        """Wykonaj przejście stanu.

        Args:
            target: Docelowy stan.

        Raises:
            LifecycleError: Jeśli przejście niedozwolone.
        """
        if not self.can_transition(target):
            raise LifecycleError(
                f"Nie można przejść z {self._state.value} do {target.value}."
                f" Dozwolone: {[s.value for s in self.VALID_TRANSITIONS.get(self._state, [])]}"
            )
        self._state = target
        self._history.append(target)
