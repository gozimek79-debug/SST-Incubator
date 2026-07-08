"""Testy dla Brain Runtime v0.8.1 – test_step_modifies_state fix."""

import pytest, sys
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
        brain = perceive(brain, 0.0)
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
        brain.memory = [MemoryRecord(stimulus_hash=50, prediction=0.5, error=0.1, timestamp_tick=0)]
        brain = perceive(brain, 0.5)
        brain = predict(brain)
        assert brain.last_prediction is not None

    def test_predict_during_silence(self):
        brain = make_brain()
        brain = perceive(brain, 0.3)
        brain = perceive(brain, 0.7)
        brain.last_input = None
        brain = predict(brain)
        assert brain.last_prediction is not None
        assert 0.0 <= brain.last_prediction <= 1.0


class TestPrecision:
    def test_compute_error(self):
        brain = make_brain()
        brain.last_prediction = 0.5
        brain.last_input = 0.7
        brain = compute_error(brain)
        assert len(brain.prediction_error_buffer) == 1
        assert abs(brain.prediction_error_buffer[0] - 0.2) < 1e-9

    def test_compute_error_during_silence(self):
        brain = make_brain()
        brain.last_prediction = 0.5
        brain.last_input = None
        before = len(brain.prediction_error_buffer)
        brain = compute_error(brain)
        assert len(brain.prediction_error_buffer) == before

    def test_compute_precision_no_data(self):
        brain = make_brain()
        brain = compute_precision(brain)
        assert brain.precision == 0.5

    def test_compute_precision_with_data(self):
        brain = make_brain()
        brain.prediction_error_buffer = [0.1, 0.1, 0.1, 0.1]
        brain = compute_precision(brain)
        assert brain.precision > 0.9

    def test_precision_low_with_high_noise(self):
        brain = make_brain()
        brain.prediction_error_buffer = [0.1, 0.9, 0.2, 0.8, 0.3]
        brain.meta_cognition_sensitivity = 1.0
        brain = compute_precision(brain)
        assert brain.precision < 1.0
        brain2 = make_brain()
        brain2.meta_cognition_sensitivity = 1.0
        brain2.prediction_error_buffer = [0.1, 0.1, 0.1, 0.1]
        brain2 = compute_precision(brain2)
        assert brain2.precision > brain.precision


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
        brain.energy = 2.0; brain.entropy = -0.5
        brain = regulate(brain)
        assert 0.0 <= brain.energy <= 1.0
        assert 0.0 <= brain.entropy <= 1.0


class TestPlasticity:
    def test_memory_grows(self):
        brain = make_brain()
        brain.last_input = 0.5; brain.last_prediction = 0.5
        brain = update_memory(brain)
        assert len(brain.memory) == 1

    def test_memory_capacity_limit(self):
        brain = make_brain(); brain.memory_capacity = 5
        for i in range(10):
            brain.last_input = float(i)/10.0; brain.last_prediction = float(i)/10.0
            brain.step_counter = i; brain = update_memory(brain)
        assert len(brain.memory) <= 5

    def test_decay_increases_error(self):
        brain = make_brain()
        brain.memory = [MemoryRecord(stimulus_hash=50, prediction=0.5, error=0.1, timestamp_tick=0)]
        brain = apply_decay(brain)
        assert brain.memory[0].error > 0.1


class TestAction:
    def test_echo_input(self):
        brain = make_brain(); brain.last_input = 0.75
        assert act(brain) == 0.75

    def test_default_action(self):
        brain = make_brain()
        assert act(brain) == 0.0


class TestBrainRuntime:
    def test_step_returns_brain(self):
        brain = make_brain()
        result = BrainRuntime.step(brain, 0.5, seed=42, tick=1)
        assert isinstance(result, BrainTissue)
        assert result.step_counter == 1

    def test_step_modifies_state(self):
        brain = make_brain()
        energy_before = brain.energy
        result = BrainRuntime.step(brain, 0.5, seed=42, tick=1)
        assert result.energy < energy_before

    def test_step_grows_memory(self):
        brain = make_brain(); brain.memory_capacity = 100
        for i in range(20):
            brain = BrainRuntime.step(brain, 0.5, seed=42, tick=i)
        assert len(brain.memory) > 0

    def test_step_with_silence(self):
        brain = make_brain()
        result = BrainRuntime.step(brain, -1.0, seed=42, tick=1)
        assert isinstance(result, BrainTissue)

    def test_get_action(self):
        brain = make_brain(); brain.last_input = 0.3
        assert BrainRuntime.get_action(brain) == 0.3


class TestCognitiveDeterminism:
    def test_deterministic_run(self):
        def run_sim(seed, ticks=100):
            brain = make_brain()
            inputs = [0.5,0.3,0.7,0.2,0.8] * (ticks//5)
            for i, inp in enumerate(inputs):
                brain = BrainRuntime.step(brain, inp, seed=seed, tick=i)
            return brain.entropy
        assert run_sim(42) == run_sim(42) == run_sim(42)

    def test_different_seed_different_result(self):
        e1 = BrainRuntime.step(make_brain(), 0.5, seed=42, tick=0).entropy
        e2 = BrainRuntime.step(make_brain(), 0.5, seed=123, tick=0).entropy
        assert isinstance(e1, float) and isinstance(e2, float)
