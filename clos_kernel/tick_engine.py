"""Tick Engine – jedyne źródło czasu w CLOS.

Deterministyczny licznik ticków z fixed timestep.
"""

from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class Tick:
    """Pojedynczy tick systemu."""
    tick_id: int
    current_time: float


class TickEngine:
    """Silnik czasu CLOS.

    Odpowiada wyłącznie za zliczanie ticków.
    Brak wielowątkowości. Brak asyncio.
    """

    def __init__(self, timestep: float = 0.1):
        self.timestep: float = timestep
        self._tick_id: int = 0
        self._running: bool = False
        self._start_time: Optional[float] = None
        self._current_tick: Optional[Tick] = None

    @property
    def tick_id(self) -> int:
        """Aktualny numer ticka."""
        return self._tick_id

    @property
    def current_time(self) -> float:
        """Aktualny czas symulacji."""
        if self._current_tick is not None:
            return self._current_tick.current_time
        return 0.0

    @property
    def running(self) -> bool:
        """Czy silnik jest uruchomiony."""
        return self._running

    def start(self) -> None:
        """Uruchom silnik czasu."""
        self._running = True
        self._start_time = time.time()
        self._tick_id = 0
        self._current_tick = Tick(tick_id=0, current_time=0.0)

    def stop(self) -> None:
        """Zatrzymaj silnik czasu."""
        self._running = False

    def next_tick(self) -> Tick:
        """Przejdź do następnego ticka.

        Returns:
            Tick: Nowy tick z zaktualizowanym ID i czasem.

        Raises:
            RuntimeError: Jeśli silnik nie jest uruchomiony.
        """
        if not self._running:
            raise RuntimeError("TickEngine nie jest uruchomiony. Wywołaj start().")
        
        self._tick_id += 1
        self._current_tick = Tick(
            tick_id=self._tick_id,
            current_time=self._tick_id * self.timestep
        )
        return self._current_tick

    def reset(self) -> None:
        """Zresetuj silnik do stanu początkowego."""
        self._tick_id = 0
        self._running = False
        self._start_time = None
        self._current_tick = None
