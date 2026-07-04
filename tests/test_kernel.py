import pytest
import sys
sys.path.insert(0, '.')

from clos_kernel.tick_engine import TickEngine
from clos_kernel.scheduler import Scheduler, Frequency
from clos_kernel.seed_manager import SeedManager
from clos_kernel.snapshot_engine import SnapshotEngine, Snapshot
from clos_kernel.replay_engine import ReplayEngine
from clos_kernel.lifecycle import Lifecycle, LifecycleState, LifecycleError
from clos_kernel.event_bus import EventBus, Event, SystemEvent
from clos_kernel.kernel import Kernel


# ==================== Tick Engine ====================

class TestTickEngine:
    def test_start(self):
        te = TickEngine()
        te.start()
        assert te.running
        assert te.tick_id == 0

    def test_stop(self):
        te = TickEngine()
        te.start()
        te.stop()
        assert not te.running

    def test_reset(self):
        te = TickEngine()
        te.start()
        te.next_tick()
        te.next_tick()
        te.reset()
        assert te.tick_id == 0
        assert not te.running

    def test_next_tick(self):
        te = TickEngine()
        te.start()
        tick1 = te.next_tick()
        assert tick1.tick_id == 1
        tick2 = te.next_tick()
        assert tick2.tick_id == 2

    def test_tick_counter(self):
        te = TickEngine()
        te.start()
        for i in range(10):
            te.next_tick()
        assert te.tick_id == 10

    def test_not_running_raises(self):
        te = TickEngine()
        with pytest.raises(RuntimeError):
            te.next_tick()


# ==================== Scheduler ====================

class TestScheduler:
    def test_fast_task(self):
        s = Scheduler()
        executed = []
        s.register("fast_test", lambda t: executed.append(t), Frequency.FAST)
        for tick in range(1, 6):
            s.execute(tick)
        assert executed == [1, 2, 3, 4, 5]

    def test_mid_task(self):
        s = Scheduler()
        executed = []
        s.register("mid_test", lambda t: executed.append(t), Frequency.MID)
        for tick in range(1, 25):
            s.execute(tick)
        assert executed == [10, 20]

    def test_slow_task(self):
        s = Scheduler()
        executed = []
        s.register("slow_test", lambda t: executed.append(t), Frequency.SLOW)
        for tick in range(1, 250):
            s.execute(tick)
        assert executed == [100, 200]

    def test_multiple_frequencies(self):
        s = Scheduler()
        results = []
        s.register("fast", lambda t: results.append(("fast", t)), Frequency.FAST)
        s.register("mid", lambda t: results.append(("mid", t)), Frequency.MID)
        s.register("slow", lambda t: results.append(("slow", t)), Frequency.SLOW)
        
        for tick in range(1, 101):
            s.execute(tick)
        
        assert results[0] == ("fast", 1)
        assert ("mid", 10) in results
        assert ("slow", 100) in results

    def test_unregister(self):
        s = Scheduler()
        executed = []
        s.register("test", lambda t: executed.append(t), Frequency.FAST)
        s.unregister("test")
        s.execute(1)
        assert len(executed) == 0


# ==================== Seed Manager ====================

class TestSeedManager:
    def test_set_seed(self):
        sm = SeedManager()
        sm.set_seed(42)
        assert sm.get_seed() == 42

    def test_get_seed(self):
        sm = SeedManager(123)
        assert sm.get_seed() == 123

    def test_repeatability(self):
        sm1 = SeedManager(42)
        val1 = sm1.random_float()
        
        sm2 = SeedManager(42)
        val2 = sm2.random_float()
        
        assert val1 == val2

    def test_reset(self):
        sm = SeedManager(42)
        first = sm.random_float()
        sm.reset()
        after_reset = sm.random_float()
        assert first == after_reset

    def test_generate(self):
        sm = SeedManager()
        seed = sm.generate()
        assert isinstance(seed, int)
        assert sm.get_seed() == seed


# ==================== Snapshot Engine ====================

class TestSnapshotEngine:
    def test_create_snapshot(self):
        se = SnapshotEngine()
        snap = se.create_snapshot(
            brain_id="brain_001", tick=1, seed=42,
            lifecycle_state="running", brain_status="ALIVE",
            entropy=0.5, energy=90.0, age=10, step_counter=10
        )
        assert snap.brain_id == "brain_001"
        assert snap.tick == 1
        assert snap.seed == 42

    def test_save_and_load_json(self, tmp_path):
        se = SnapshotEngine(storage_path=str(tmp_path / "snapshots"))
        se.create_snapshot("brain_001", 1, 42, "running", "ALIVE", 0.5, 90.0, 10, 10)
        se.create_snapshot("brain_001", 2, 42, "running", "ALIVE", 0.4, 85.0, 11, 11)
        se.save_to_file("exp_001")
        
        se2 = SnapshotEngine(storage_path=str(tmp_path / "snapshots"))
        loaded = se2.load_from_file("exp_001")
        assert len(loaded) == 2

    def test_get_snapshot(self):
        se = SnapshotEngine()
        se.create_snapshot("brain_001", 5, 42, "running", "ALIVE", 0.5, 90.0, 10, 10)
        snap = se.get_snapshot(5)
        assert snap is not None
        assert snap.tick == 5

    def test_get_nonexistent_tick(self):
        se = SnapshotEngine()
        assert se.get_snapshot(999) is None


# ==================== Replay Engine ====================

class TestReplayEngine:
    def test_goto_tick(self):
        se = SnapshotEngine()
        se.create_snapshot("b1", 10, 42, "running", "ALIVE", 0.5, 90.0, 10, 10)
        se.create_snapshot("b1", 20, 42, "running", "ALIVE", 0.4, 80.0, 20, 20)
        se.create_snapshot("b1", 30, 42, "running", "ALIVE", 0.3, 70.0, 30, 30)
        
        re = ReplayEngine(se)
        snap = re.goto_tick(20)
        assert snap is not None
        assert snap.tick == 20

    def test_step_forward(self):
        se = SnapshotEngine()
        se.create_snapshot("b1", 1, 42, "running", "ALIVE", 0.5, 90.0, 1, 1)
        se.create_snapshot("b1", 2, 42, "running", "ALIVE", 0.5, 90.0, 2, 2)
        
        re = ReplayEngine(se)
        snap = re.step_forward()
        assert snap is not None
        assert snap.tick == 1

    def test_step_back(self):
        se = SnapshotEngine()
        se.create_snapshot("b1", 1, 42, "running", "ALIVE", 0.5, 90.0, 1, 1)
        se.create_snapshot("b1", 2, 42, "running", "ALIVE", 0.5, 90.0, 2, 2)
        
        re = ReplayEngine(se)
        re.step_forward()
        re.step_forward()
        snap = re.step_back()
        assert snap.tick == 1

    def test_current_state(self):
        se = SnapshotEngine()
        se.create_snapshot("b1", 1, 42, "running", "ALIVE", 0.5, 90.0, 1, 1)
        
        re = ReplayEngine(se)
        re.step_forward()
        state = re.current_state()
        assert state.tick == 1


# ==================== Lifecycle ====================

class TestLifecycle:
    def test_valid_transition_birth_to_running(self):
        lc = Lifecycle()
        assert lc.state == LifecycleState.BIRTH
        lc.transition(LifecycleState.RUNNING)
        assert lc.state == LifecycleState.RUNNING

    def test_valid_transition_running_to_sleeping(self):
        lc = Lifecycle()
        lc.transition(LifecycleState.RUNNING)
        lc.transition(LifecycleState.SLEEPING)
        assert lc.state == LifecycleState.SLEEPING

    def test_valid_transition_sleeping_to_running(self):
        lc = Lifecycle()
        lc.transition(LifecycleState.RUNNING)
        lc.transition(LifecycleState.SLEEPING)
        lc.transition(LifecycleState.RUNNING)
        assert lc.state == LifecycleState.RUNNING

    def test_running_to_dead(self):
        lc = Lifecycle()
        lc.transition(LifecycleState.RUNNING)
        lc.transition(LifecycleState.DEAD)
        assert lc.state == LifecycleState.DEAD

    def test_block_dead_to_running(self):
        lc = Lifecycle()
        lc.transition(LifecycleState.RUNNING)
        lc.transition(LifecycleState.DEAD)
        with pytest.raises(LifecycleError):
            lc.transition(LifecycleState.RUNNING)

    def test_block_dead_to_anything(self):
        lc = Lifecycle()
        lc.transition(LifecycleState.DEAD)
        with pytest.raises(LifecycleError):
            lc.transition(LifecycleState.SLEEPING)

    def test_history(self):
        lc = Lifecycle()
        lc.transition(LifecycleState.RUNNING)
        lc.transition(LifecycleState.SLEEPING)
        assert len(lc.history) == 3


# ==================== Event Bus ====================

class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(SystemEvent.TICK_STARTED, handler)
        bus.publish(Event(event_type=SystemEvent.TICK_STARTED, data={"tick": 1}))
        assert len(received) == 1
        assert received[0].data["tick"] == 1

    def test_unsubscribe(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(SystemEvent.TICK_STARTED, handler)
        bus.unsubscribe(SystemEvent.TICK_STARTED, handler)
        bus.publish(Event(event_type=SystemEvent.TICK_STARTED, data={"tick": 1}))
        assert len(received) == 0

    def test_multiple_subscribers(self):
        bus = EventBus()
        r1, r2 = [], []

        bus.subscribe(SystemEvent.TICK_FINISHED, lambda e: r1.append(e))
        bus.subscribe(SystemEvent.TICK_FINISHED, lambda e: r2.append(e))
        bus.publish(Event(event_type=SystemEvent.TICK_FINISHED, data={}))
        assert len(r1) == 1
        assert len(r2) == 1

    def test_history(self):
        bus = EventBus()
        bus.publish(Event(event_type=SystemEvent.TICK_STARTED, data={"tick": 1}))
        bus.publish(Event(event_type=SystemEvent.TICK_FINISHED, data={"tick": 1}))
        
        history = bus.get_history()
        assert len(history) == 2
        
        filtered = bus.get_history(SystemEvent.TICK_STARTED)
        assert len(filtered) == 1


# ==================== Kernel ====================

class TestKernel:
    def test_full_tick_loop(self):
        kernel = Kernel(seed=42)
        kernel.brain_id = "test_brain"
        kernel.max_ticks = 5
        results = kernel.run()
        assert len(results) == 5

    def test_deterministic_run(self):
        kernel1 = Kernel(seed=123)
        kernel1.brain_id = "brain_001"
        kernel1.max_ticks = 10
        results1 = kernel1.run()

        kernel2 = Kernel(seed=123)
        kernel2.brain_id = "brain_001"
        kernel2.max_ticks = 10
        results2 = kernel2.run()

        for r1, r2 in zip(results1, results2):
            assert r1["tick"] == r2["tick"]
            assert r1["time"] == r2["time"]
            assert r1["lifecycle"] == r2["lifecycle"]

    def test_snapshot_after_tick(self):
        kernel = Kernel(seed=42)
        kernel.brain_id = "brain_test"
        kernel.max_ticks = 3
        kernel.run()
        
        snapshots = kernel.snapshot_engine.get_all_snapshots()
        assert len(snapshots) >= 3

    def test_event_after_tick(self):
        kernel = Kernel(seed=42)
        kernel.brain_id = "brain_test"
        kernel.max_ticks = 2
        kernel.run()
        
        history = kernel.event_bus.get_history(SystemEvent.TICK_STARTED)
        assert len(history) >= 2

    def test_run_tick_single(self):
        kernel = Kernel(seed=42)
        kernel.brain_id = "brain_test"
        kernel.initialize()
        result = kernel.run_tick()
        assert result["tick"] == 1
        assert "executed_tasks" in result
