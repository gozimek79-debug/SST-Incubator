"""Regresja: Snapshot Engine jako Read-Only Observer (SPRINT_v0.10.md P2).

Formalizacja dowodu usuwalnosci z docs/spec_snapshot_observer.md (P1, ad-hoc).
Test poprawnosci CTO: usuniecie obserwatora (observe=False) NIE MOZE zmienic
zadnego pola Execution Pipeline (world.step/brain_rt.step/silent_step) - tylko
pola jawnie zdefiniowane jako f(snapshots) (Observation Pipeline) wolno
zmienic, i one MUSZA sie zmienic (dowod, ze obserwator faktycznie dostarcza
dane, nie jest cichym no-opem).

JAKAKOLWIEK roznica w polach Execution = STOP wedlug SPRINT_v0.10.md P2.
"""

import json

import pytest

from clos_academy.lesson_L1_1 import run_pattern_echo
from clos_academy.lesson_L1_2 import run_shock_recovery

L1_1_EXECUTION_FIELDS = [
    "run_id", "lesson", "genome", "seed", "scenario",
    "primary_endpoint", "mae_stimulus_phase", "mae_silence_phase",  # SPRINT_v0.11.0.md P1: bylo mse_*
    "memory_decay_rate", "final_energy", "final_entropy", "memory_size", "passed",
]
L1_1_OBSERVATION_FIELDS = ["stability_score", "adaptation_tick", "snapshot_count"]

L1_2_EXECUTION_FIELDS = [
    "run_id", "lesson", "genome", "seed", "scenario",
    "homeostasis_band", "fraction_in_band", "final_energy", "final_entropy", "memory_size",
]
L1_2_SHOCK_ONLY_EXECUTION_FIELDS = ["t_shock", "primary_endpoint", "pre_shock_in_band"]
L1_2_OBSERVATION_FIELDS = ["stability_score", "adaptation_tick", "snapshot_count"]


def _strip_telemetry(r):
    return {k: v for k, v in r.items() if k != "telemetry"}


def _subset(result, fields):
    return {k: result[k] for k in fields}


class TestL11ObserverRemovability:
    """L1.1: 40/40 (2 genomy x 2 scenariusze x 10 seedow) - macierz identyczna z publish_L1_1.py."""

    GENOMES = ["default", "highly_plastic"]
    SCENARIOS = ["noise_world", "stable_world"]
    SEEDS = list(range(1, 11))

    @classmethod
    def _run_matrix(cls, observe):
        results = []
        for genome in cls.GENOMES:
            for scenario in cls.SCENARIOS:
                for seed in cls.SEEDS:
                    r = run_pattern_echo(genome_preset=genome, seed=seed, scenario=scenario, observe=observe)
                    results.append(_strip_telemetry(r))
        return results

    @classmethod
    def setup_class(cls):
        cls.results_on = cls._run_matrix(observe=True)
        cls.results_off = cls._run_matrix(observe=False)

    def test_execution_fields_identical_40_of_40(self):
        assert len(self.results_on) == 40 and len(self.results_off) == 40
        mismatches = []
        for i, (a, b) in enumerate(zip(self.results_on, self.results_off)):
            sub_a = json.dumps(_subset(a, L1_1_EXECUTION_FIELDS), sort_keys=True, default=str)
            sub_b = json.dumps(_subset(b, L1_1_EXECUTION_FIELDS), sort_keys=True, default=str)
            if sub_a != sub_b:
                mismatches.append(a["run_id"])
        assert not mismatches, (
            f"STOP (SPRINT_v0.10.md P2): obserwator zmienil pola Execution w runach {mismatches} - "
            "to jest ingerencja w Execution Pipeline, niedozwolona przez Warunek 1/2 CTO"
        )

    def test_observation_fields_change_when_observed(self):
        """Dowod, ze obserwator faktycznie dostarcza dane (nie cichy no-op)."""
        unchanged = []
        for a, b in zip(self.results_on, self.results_off):
            sub_a = _subset(a, L1_1_OBSERVATION_FIELDS)
            sub_b = _subset(b, L1_1_OBSERVATION_FIELDS)
            if sub_a == sub_b:
                unchanged.append(a["run_id"])
        assert not unchanged, (
            f"obserwator nie zmienil observation fields w runach {unchanged} - "
            "podejrzenie ze create_snapshot() nie jest faktycznie wolane"
        )


class TestL12ObserverRemovability:
    """L1.2: podzbior macierzy (2 genomy x 3 seedy x 2 scenariusze) - primary endpoint + reszta execution."""

    GENOMES = ["default", "highly_plastic"]
    SCENARIOS = ["shock_world", "stable_world"]
    SEEDS = [1, 2, 3]

    @classmethod
    def _run_matrix(cls, observe):
        results = []
        for genome in cls.GENOMES:
            for scenario in cls.SCENARIOS:
                for seed in cls.SEEDS:
                    r = run_shock_recovery(genome_preset=genome, seed=seed, scenario=scenario, observe=observe)
                    results.append(_strip_telemetry(r))
        return results

    @classmethod
    def setup_class(cls):
        cls.results_on = cls._run_matrix(observe=True)
        cls.results_off = cls._run_matrix(observe=False)

    def _execution_fields_for(self, result):
        fields = list(L1_2_EXECUTION_FIELDS)
        if result["scenario"] == "shock_world":
            fields += L1_2_SHOCK_ONLY_EXECUTION_FIELDS
        return fields

    def test_execution_fields_identical(self):
        mismatches = []
        for a, b in zip(self.results_on, self.results_off):
            fields = self._execution_fields_for(a)
            sub_a = json.dumps(_subset(a, fields), sort_keys=True, default=str)
            sub_b = json.dumps(_subset(b, fields), sort_keys=True, default=str)
            if sub_a != sub_b:
                mismatches.append(a["run_id"])
        assert not mismatches, (
            f"STOP (SPRINT_v0.10.md P2): obserwator zmienil pola Execution L1.2 w runach {mismatches}"
        )

    def test_primary_endpoint_identical_shock_world(self):
        """Warunek explicite z SPRINT_v0.10.md P2: 'L1.2: primary endpoint identyczny'."""
        shock_on = [r for r in self.results_on if r["scenario"] == "shock_world"]
        shock_off = [r for r in self.results_off if r["scenario"] == "shock_world"]
        assert len(shock_on) == len(shock_off) == 6
        for a, b in zip(shock_on, shock_off):
            assert a["primary_endpoint"] == b["primary_endpoint"], a["run_id"]

    def test_observation_fields_change_when_observed(self):
        unchanged = []
        for a, b in zip(self.results_on, self.results_off):
            sub_a = _subset(a, L1_2_OBSERVATION_FIELDS)
            sub_b = _subset(b, L1_2_OBSERVATION_FIELDS)
            if sub_a == sub_b:
                unchanged.append(a["run_id"])
        assert not unchanged, (
            f"obserwator nie zmienil observation fields w runach {unchanged} w L1.2"
        )
