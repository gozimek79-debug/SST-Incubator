"""Testy regresji dla BrainRuntime.partial_step() (SPRINT_v0.9.md, Priorytet 2).

Nowy inwariant projektu: chronimy niezmienność ZACHOWANIA systemu, nie
niezmienność plików. test_step_regression porównuje step() na ustalonych
wejściach z tests/golden_step_baseline.json — zlotymi wartościami
wygenerowanymi PRZED dodaniem partial_step() do tego samego pliku (patrz
tests/generate_golden_step_baseline.py, commit eb6d53e). Jeśli ten test
kiedykolwiek zawiedzie, to znaczy, że zachowanie step() się zmieniło -
to jest STOP, nie coś do "naprawienia" przez regenerację baseline.
"""

import json
from pathlib import Path

import pytest

from clos_brain.brain_runtime import BrainRuntime, PipelineStep
from generate_golden_step_baseline import (
    GENOME_PRESET,
    SEED,
    TICKS,
    build_tissue,
    sensory_inputs,
    tissue_snapshot,
)

BASELINE_PATH = Path(__file__).parent / "golden_step_baseline.json"


def _load_baseline():
    with open(BASELINE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _run_step_sequence(inputs, seed=SEED, genome_preset=GENOME_PRESET):
    brain = build_tissue(genome_preset)
    per_tick = []
    for tick, sensory_input in enumerate(inputs):
        brain = BrainRuntime.step(brain, sensory_input=sensory_input, seed=seed, tick=tick)
        per_tick.append({"tick": tick, **tissue_snapshot(brain)})
    return brain, per_tick


def _run_partial_step_sequence(inputs, seed=SEED, genome_preset=GENOME_PRESET, skip=()):
    brain = build_tissue(genome_preset)
    per_tick = []
    for tick, sensory_input in enumerate(inputs):
        brain = BrainRuntime.partial_step(brain, sensory_input=sensory_input, seed=seed, tick=tick, skip=skip)
        per_tick.append({"tick": tick, **tissue_snapshot(brain)})
    return brain, per_tick


class TestStepRegression:
    """step() na ustalonych wejsciach == zlote wartosci baseline."""

    def test_step_regression(self):
        baseline = _load_baseline()
        assert baseline["inputs"]["seed"] == SEED
        assert baseline["inputs"]["genome_preset"] == GENOME_PRESET
        assert baseline["inputs"]["ticks"] == TICKS

        inputs = baseline["inputs"]["sensory_inputs"]
        assert inputs == sensory_inputs(TICKS), (
            "sensory_inputs() daje inna sekwencje niz ta zapisana w baseline - "
            "generator sie zmienil, test nieporownywalny"
        )

        _, per_tick = _run_step_sequence(inputs)
        assert per_tick == baseline["per_tick"], (
            "step() daje inny wynik niz zlote wartosci sprzed partial_step() - "
            "zachowanie sie zmienilo. To jest STOP (SPRINT_v0.9.md, nowy inwariant), "
            "nie regeneruj baseline bez osobnej, jawnej decyzji projektowej."
        )


class TestPartialStepEqualsStep:
    """partial_step(skip=()) == step() (SPRINT_v0.9.md P2, warunek obowiazkowy)."""

    def test_partial_equals_step(self):
        inputs = sensory_inputs(TICKS)
        _, step_ticks = _run_step_sequence(inputs)
        _, partial_ticks = _run_partial_step_sequence(inputs, skip=())
        assert partial_ticks == step_ticks


class TestPartialStepSkipPerceive:
    """Pominiecie PERCEIVE nie aktualizuje bufora sensorycznego."""

    def test_partial_skip_perceive(self):
        brain = build_tissue(GENOME_PRESET)
        brain = BrainRuntime.step(brain, sensory_input=0.5, seed=SEED, tick=0)
        buffer_before = list(brain.sensory_buffer)
        last_input_before = brain.last_input

        brain = BrainRuntime.partial_step(
            brain, sensory_input=None, seed=SEED, tick=1, skip={PipelineStep.PERCEIVE}
        )

        assert brain.sensory_buffer == buffer_before, "bufor sensoryczny musi pozostac niezmieniony w ciszy"
        assert brain.last_input is None, "brak bodzca zewnetrznego -> last_input=None (jak echo_runtime.silent_step)"
        assert last_input_before == 0.5  # sanity: rozne od nowego last_input


class TestPartialStepRejectsOtherSteps:
    """Pominiecie kroku innego niz PERCEIVE -> NotImplementedError."""

    @pytest.mark.parametrize("step", [
        PipelineStep.PREDICT,
        PipelineStep.COMPUTE_ERROR,
        PipelineStep.COMPUTE_PRECISION,
        PipelineStep.REGULATE,
        PipelineStep.UPDATE_MEMORY,
        PipelineStep.APPLY_DECAY,
    ])
    def test_partial_rejects_other_steps(self, step):
        brain = build_tissue(GENOME_PRESET)
        with pytest.raises(NotImplementedError):
            BrainRuntime.partial_step(brain, sensory_input=0.5, seed=SEED, tick=0, skip={step})

    def test_partial_rejects_mixed_skip_with_perceive(self):
        """PERCEIVE + cokolwiek niecertyfikowanego w tym samym skip tez odrzucone."""
        brain = build_tissue(GENOME_PRESET)
        with pytest.raises(NotImplementedError):
            BrainRuntime.partial_step(
                brain, sensory_input=None, seed=SEED, tick=0,
                skip={PipelineStep.PERCEIVE, PipelineStep.PREDICT},
            )
