"""Kernel – główna pętla systemu CLOS.

Koordynuje Tick, Scheduler, Lifecycle, Snapshot, EventBus.
"""

from typing import Any, Dict, List, Optional
from .tick_engine import TickEngine
from .scheduler import Scheduler
from .lifecycle import Lifecycle, LifecycleState
from .event_bus import EventBus, Event, SystemEvent
from .snapshot_engine import SnapshotEngine
from .replay_engine import ReplayEngine
from .seed_manager import SeedManager


class Kernel:
    """Główna pętla CLOS.

    Każdy Tick wykonuje:
        Tick Started → Scheduler → Lifecycle → Snapshot → Event Dispatch → Tick Finished
    """

    def __init__(self, seed: Optional[int] = None):
        self.tick_engine: TickEngine = TickEngine(timestep=0.1)
        self.scheduler: Scheduler = Scheduler()
        self.lifecycle: Lifecycle = Lifecycle()
        self.event_bus: EventBus = EventBus()
        self.snapshot_engine: SnapshotEngine = SnapshotEngine()
        self.replay_engine: ReplayEngine = ReplayEngine(self.snapshot_engine)
        self.seed_manager: SeedManager = SeedManager(seed=seed)
        self._brain_id: Optional[str] = None
        self._max_ticks: int = 1000
        self._tick_count: int = 0

    @property
    def brain_id(self) -> Optional[str]:
        """ID aktualnego Brain."""
        return self._brain_id

    @brain_id.setter
    def brain_id(self, value: str) -> None:
        self._brain_id = value

    @property
    def max_ticks(self) -> int:
        """Maksymalna liczba ticków."""
        return self._max_ticks

    @max_ticks.setter
    def max_ticks(self, value: int) -> None:
        self._max_ticks = value

    @property
    def tick_count(self) -> int:
        """Liczba wykonanych ticków."""
        return self._tick_count

    def initialize(self) -> None:
        """Zainicjalizuj Kernel."""
        self.tick_engine.start()
        self.lifecycle = Lifecycle()
        self.lifecycle.transition(LifecycleState.RUNNING)

    def run_tick(self) -> Dict[str, Any]:
        """Wykonaj jeden tick.

        Returns:
            Słownik z wynikami ticka.
        """
        if not self.tick_engine.running:
            raise RuntimeError("Kernel nie jest uruchomiony. Wywołaj initialize().")

        # Tick Started
        tick = self.tick_engine.next_tick()
        self.event_bus.publish(Event(
            event_type=SystemEvent.TICK_STARTED,
            data={"tick_id": tick.tick_id, "time": tick.current_time},
            source="kernel"
        ))

        # Scheduler – wykonaj zaplanowane zadania
        executed_tasks = self.scheduler.execute(tick.tick_id)

        # Lifecycle Update (na razie bez zmian, tylko dla struktury)
        self.event_bus.publish(Event(
            event_type=SystemEvent.LIFECYCLE_CHANGED,
            data={"state": self.lifecycle.state.value},
            source="kernel"
        ))

        # Snapshot – zapisz stan
        snapshot = self.snapshot_engine.create_snapshot(
            brain_id=self._brain_id or "unknown",
            tick=tick.tick_id,
            seed=self.seed_manager.get_seed(),
            lifecycle_state=self.lifecycle.state.value,
            brain_status="RUNNING",
            entropy=0.0,
            energy=100.0,
            age=tick.tick_id,
            step_counter=tick.tick_id
        )
        self.event_bus.publish(Event(
            event_type=SystemEvent.SNAPSHOT_CREATED,
            data={"tick": snapshot.tick},
            source="kernel"
        ))

        # Tick Finished
        self.event_bus.publish(Event(
            event_type=SystemEvent.TICK_FINISHED,
            data={"tick_id": tick.tick_id},
            source="kernel"
        ))

        self._tick_count += 1
        return {
            "tick": tick.tick_id,
            "time": tick.current_time,
            "executed_tasks": executed_tasks,
            "lifecycle": self.lifecycle.state.value,
            "seed": self.seed_manager.get_seed()
        }

    def run(self, ticks: Optional[int] = None) -> List[Dict[str, Any]]:
        """Uruchom główną pętlę.

        Args:
            ticks: Liczba ticków do wykonania (domyślnie max_ticks).

        Returns:
            Lista wyników każdego ticka.
        """
        self.initialize()
        max_run = ticks or self._max_ticks
        results = []
        for _ in range(max_run):
            result = self.run_tick()
            results.append(result)
        self.tick_engine.stop()
        return results

    def stop(self) -> None:
        """Zatrzymaj Kernel."""
        self.tick_engine.stop()
