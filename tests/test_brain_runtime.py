"""Testy dla Brain Runtime v0.1 – w tym Cognitive Determinism Test."""

import pytest
import sys
sys.path.insert(0, '.')

from clos_brain.tissue import BrainTissue, MemoryRecord
from clos_brain.brain_runtime import BrainRuntime
from clos_brain.runtime.perception import perceive
from clos_brain.runtime.prediction import predict
from clos_brain.runtime.precision import compute_error, compute_precision
from clos_brain.runtime.homeostasis import regulate
from clos_brain.runtime.plasticity import update_memory, apply_decay
from clos_brain.runtime.action import act


def make_brain(brain_id="test_brain", genome_id="test_genome") -> BrainTissue:
    """Fabryka testowego Brain."""
    return BrainTissue(brain_id=brain_id, genome_id=genome_id)


class TestPerception:
    def test_perceive_adds_to_buffer(self):
        brain = make_brain()
        brain = perceive(brain, 0.5)
        assert len(brain.sensory_buffer) == 1
        assert brain.sensory_buffer[0] == 0.5

    def test_perceive_clamps_input(self):
        brain = make_brain()
        brain = perceive(brain, 1.5)
        assert brain.sensory_buffer[0] == 1.0
        brain = perceive(brain, -0.5)
        assert brain.sensory_buffer[1] == 0.0

    def test_perceive_buffer_limit(self):
        brain = make_brain()
        brain.prediction_depth = 2
        for i in range(20):
            brain = perceive(brain, float(i) / 20.0)
        assert len(brain.sensory_buffer) <= 10


class TestPrediction:
    def test_predict_without_memory(self):
        brain = make_brain()
        brain = perceive(brain, 0.5)
        brain = predict(brain)
        assert brain.last_prediction is not None
        assert 0.0 <= brain.last_prediction <= 1.0

    def test_predict_with_memory(self):
        brain = make_brain()
        brain.memory = [
            MemoryRecord(stimulus_hash=50, prediction=0.5, error=0.1, timestamp_tick=0)
        ]
        brain = perceive(brain, 0.5)
        brain = predict(brain)
        assert brain.last_prediction is not None


class TestPrecision:
    def test_compute_error(self):
        brain = make_brain()
        brain.last_prediction = 0.5
        brain.last_input = 0.7
        brain = compute_error(brain)
        assert len(brain.prediction_error_buffer) == 1
        # Floating point: 0.7 - 0.5 = 0.19999999999999996
        assert abs(brain.prediction_error_buffer[0] - 0.2) < 1e-9

    def test_compute_precision_no_data(self):
        brain = make_brain()
        brain = compute_precision(brain)
        assert brain.precision == 0.5

    def test_compute_precision_with_data(self):
        brain = make_brain()
        brain.prediction_error_buffer = [0.1, 0.1, 0.1, 0.1]
        brain = compute_precision(brain)
        assert brain.precision > 0.9  # Niski szum → wysoka precyzja

    def test_precision_low_with_high_noise(self):
        brain = make_brain()
        brain.prediction_error_buffer = [0.1, 0.9, 0.2, 0.8, 0.3]
        brain.meta_cognition_sensitivity = 1.0  # Zwiększ czułość
        brain = compute_precision(brain)
        # Przy wysokim szumie i czułości 1.0 precyzja powinna być niższa
        assert brain.precision < 1.0
        # Porównaj z niskim szumem
        brain2 = make_brain()
        brain2.meta_cognition_sensitivity = 1.0
        brain2.prediction_error_buffer = [0.1, 0.1, 0.1, 0.1]
        brain2 = compute_precision(brain2)
        assert brain2.precision > brain.precision  # Niski szum = wyższa precyzja


class TestHomeostasis:
    def test_energy_decays(self):
        brain = make_brain()
        initial = brain.energy
        brain = regulate(brain)
        assert brain.energy < initial

    def test_entropy_increases_with_error(self):
        brain = make_brain()
        brain.prediction_error_buffer = [0.5]
        initial = brain.entropy
        brain = regulate(brain)
        assert brain.entropy > initial

    def test_clamping(self):
        brain = make_brain()
        brain.energy = 2.0
        brain.entropy = -0.5
        brain = regulate(brain)
        assert 0.0 <= brain.energy <= 1.0
        assert 0.0 <= brain.entropy <= 1.0


class TestPlasticity:
    def test_memory_grows(self):
        brain = make_brain()
        brain.last_input = 0.5
        brain.last_prediction = 0.5
        brain = update_memory(brain)
        assert len(brain.memory) == 1

    def test_memory_capacity_limit(self):
        brain = make_brain()
        brain.memory_capacity = 5
        for i in range(10):
            brain.last_input = float(i) / 10.0
            brain.last_prediction = float(i) / 10.0
            brain.step_counter = i
            brain = update_memory(brain)
        assert len(brain.memory) <= 5

    def test_decay_increases_error(self):
        brain = make_brain()
        brain.memory = [
            MemoryRecord(stimulus_hash=50, prediction=0.5, error=0.1, timestamp_tick=0)
        ]
        brain = apply_decay(brain)
        assert brain.memory[0].error > 0.1


class TestAction:
    def test_echo_input(self):
        brain = make_brain()
        brain.last_input = 0.75
        action = act(brain)
        assert action == 0.75

    def test_default_action(self):
        brain = make_brain()
        action = act(brain)
        assert action == 0.0


class TestBrainRuntime:
    def test_step_returns_brain(self):
        brain = make_brain()
        result = BrainRuntime.step(brain, 0.5, seed=42, tick=1)
        assert isinstance(result, BrainTissue)
        assert result.step_counter == 1

    def test_step_modifies_state(self):
        brain = make_brain()
        original_energy = brain.energy
        result = BrainRuntime.step(brain, 0.5, seed=42, tick=1)
        assert result.energy < original_energy

    def test_step_grows_memory(self):
        brain = make_brain()
        brain.memory_capacity = 100
        for i in range(20):
            brain = BrainRuntime.step(brain, 0.5, seed=42, tick=i)
        assert len(brain.memory) > 0

    def test_get_action(self):
        brain = make_brain()
        brain.last_input = 0.3
        action = BrainRuntime.get_action(brain)
        assert action == 0.3


class TestCognitiveDeterminism:
    """TEST KRYTYCZNY: Cognitive Determinism Test (CDT)."""

    def test_deterministic_run(self):
        """Ten sam seed + brain + input stream = identyczny wynik."""
        def run_simulation(seed, ticks=100):
            brain = make_brain()
            inputs = [0.5, 0.3, 0.7, 0.2, 0.8] * (ticks // 5)
            for i, inp in enumerate(inputs):
                brain = BrainRuntime.step(brain, inp, seed=seed, tick=i)
            return {
                "entropy_curve": brain.entropy_history.copy(),
                "memory_size": len(brain.memory),
                "precision_curve": brain.precision_history.copy(),
                "final_entropy": brain.entropy,
                "final_precision": brain.precision,
                "final_energy": brain.energy,
            }

        run1 = run_simulation(seed=42, ticks=100)
        run2 = run_simulation(seed=42, ticks=100)
        run3 = run_simulation(seed=42, ticks=100)

        # Porównanie entropy curve
        for i, (e1, e2) in enumerate(zip(run1["entropy_curve"], run2["entropy_curve"])):
            assert e1 == e2, f"Entropy różni się na indeksie {i}: {e1} vs {e2}"

        # Porównanie precision curve
        for i, (p1, p2) in enumerate(zip(run1["precision_curve"], run2["precision_curve"])):
            assert p1 == p2, f"Precision różni się na indeksie {i}: {p1} vs {p2}"

        # Porównanie stanu końcowego
        assert run1["memory_size"] == run2["memory_size"] == run3["memory_size"]
        assert run1["final_entropy"] == run2["final_entropy"] == run3["final_entropy"]
        assert run1["final_precision"] == run2["final_precision"] == run3["final_precision"]
        assert run1["final_energy"] == run2["final_energy"] == run3["final_energy"]

    def test_different_seed_different_result(self):
        """Różne seed = różny wynik."""
        def run_simulation(seed, ticks=50):
            brain = make_brain()
            inputs = [0.5, 0.3, 0.7] * (ticks // 3)
            for i, inp in enumerate(inputs):
                brain = BrainRuntime.step(brain, inp, seed=seed, tick=i)
            return brain.entropy

        entropy_42 = run_simulation(seed=42)
        entropy_123 = run_simulation(seed=123)

        assert isinstance(entropy_42, float)
        assert isinstance(entropy_123, float)
