"""SPRINT_v0.10.1.md P2: kazde nowe srodowisko musi przejsc TRZY testy
(inwariant v0.10, rozszerzony z 2 lekcji x 2 srodowisk na 2 lekcje x N srodowisk):

  (a) regresja L1.1/L1.2 na ISTNIEJACYCH scenariuszach - patrz P2 raport
      (regenerowane reports/academy/*.json, zero zmiany poza metadata/provenance);
      ten plik testuje TYLKO (b)/(c) dla NOWYCH srodowisk, bo (a) jest juz
      zweryfikowana empirycznie przez sam brak zmiany w tamtych artefaktach.
  (b) usuwalnosc obserwatora (observe=True/False) rowniez na nowym srodowisku -
      ten sam podzial Execution/Observation co tests/test_observer_removability.py.
  (c) walidator telemetrii zielony - snapshot_diagnostics bez bledow
      (clos_scientist/telemetry.py, ten sam kod co scripts/validate_observability.py).

NIE uzywa populacji z P3 (bramka jeszcze niezaimplementowana) - wylacznie
istniejace genomy (default, highly_plastic), zeby nie mieszac walidacji
srodowisk z walidacja populacji (dwie osobne bramki, dwa osobne dowody).
"""

import json

import pytest

from clos_academy.lesson_L1_1 import run_pattern_echo
from clos_academy.lesson_L1_2 import run_shock_recovery
from clos_scientist.telemetry import diagnostics_errors

NEW_ENVIRONMENTS = [
    "high_noise_world", "recurring_shock_world", "weak_shock_world",
    "long_stable_shock_world", "unpredictable_world",
]
REUSED_ENVIRONMENT = "drift_world"  # istnial od v0.7.3, zadna lekcja go dotad nie uzyla
ALL_NEW_USAGES = NEW_ENVIRONMENTS + [REUSED_ENVIRONMENT]

GENOMES = ["default", "highly_plastic"]
SEEDS = [1, 2, 3]  # smoke-test mechaniki, NIE badanie statystyczne (to P3, po bramce populacji)

L1_1_EXECUTION_FIELDS = [
    "run_id", "lesson", "genome", "seed", "scenario",
    "primary_endpoint", "mse_stimulus_phase", "mse_silence_phase",
    "memory_decay_rate", "final_energy", "final_entropy", "memory_size", "passed",
]
L1_1_OBSERVATION_FIELDS = ["stability_score", "adaptation_tick", "snapshot_count"]

L1_2_EXECUTION_FIELDS = [
    "run_id", "lesson", "genome", "seed", "scenario",
    "homeostasis_band", "fraction_in_band", "final_energy", "final_entropy", "memory_size",
]
L1_2_SHOCK_ONLY_EXECUTION_FIELDS = ["t_shock", "primary_endpoint", "pre_shock_in_band"]
L1_2_OBSERVATION_FIELDS = ["stability_score", "adaptation_tick", "snapshot_count"]

# ODKRYCIE P2: lesson_L1_2.run_shock_recovery() liczy t_shock/primary_endpoint/
# pre_shock_in_band WYLACZNIE gdy scenario == "shock_world" (dosl. string,
# clos_academy/lesson_L1_2.py:139) - NIE gdy scenariusz jest semantycznie
# "szokowy" (recurring_shock_world, weak_shock_world, long_stable_shock_world
# tez zawieraja pojedyncze/wielokrotne skoki, ale nie sa nazwane doslownie
# "shock_world", wiec endpoint sie nie uruchamia). Zaden z NEW_ENVIRONMENTS
# nie dostaje wiec pol shock-only - to jest granica infrastruktury odkryta w
# tym priorytecie (nazwa-gate, nie property-gate), NIE blad tego testu.
def _l1_2_fields_for(scenario):
    fields = list(L1_2_EXECUTION_FIELDS)
    if scenario == "shock_world":
        fields += L1_2_SHOCK_ONLY_EXECUTION_FIELDS
    return fields


def _strip_telemetry(r):
    return {k: v for k, v in r.items() if k != "telemetry"}


def _subset(result, fields):
    return {k: result[k] for k in fields}


@pytest.mark.parametrize("scenario", ALL_NEW_USAGES)
class TestNewEnvironmentObserverRemovability:
    """(b) Inwariant v0.10: Snapshot Engine usuwalny takze na nowym srodowisku."""

    def test_l1_1_execution_fields_identical(self, scenario):
        mismatches = []
        for genome in GENOMES:
            for seed in SEEDS:
                on = run_pattern_echo(genome_preset=genome, seed=seed, scenario=scenario, observe=True)
                off = run_pattern_echo(genome_preset=genome, seed=seed, scenario=scenario, observe=False)
                sub_on = json.dumps(_subset(_strip_telemetry(on), L1_1_EXECUTION_FIELDS), sort_keys=True, default=str)
                sub_off = json.dumps(_subset(_strip_telemetry(off), L1_1_EXECUTION_FIELDS), sort_keys=True, default=str)
                if sub_on != sub_off:
                    mismatches.append(on["run_id"])
        assert not mismatches, (
            f"STOP (SPRINT_v0.10.1.md P2): obserwator zmienil Execution L1.1 na {scenario} w {mismatches}"
        )

    def test_l1_2_execution_fields_identical(self, scenario):
        mismatches = []
        fields = _l1_2_fields_for(scenario)
        for genome in GENOMES:
            for seed in SEEDS:
                on = run_shock_recovery(genome_preset=genome, seed=seed, scenario=scenario, observe=True)
                off = run_shock_recovery(genome_preset=genome, seed=seed, scenario=scenario, observe=False)
                sub_on = json.dumps(_subset(_strip_telemetry(on), fields), sort_keys=True, default=str)
                sub_off = json.dumps(_subset(_strip_telemetry(off), fields), sort_keys=True, default=str)
                if sub_on != sub_off:
                    mismatches.append(on["run_id"])
        assert not mismatches, (
            f"STOP (SPRINT_v0.10.1.md P2): obserwator zmienil Execution L1.2 na {scenario} w {mismatches}"
        )

    def test_observation_fields_still_carry_real_data(self, scenario):
        """Dowod, ze obserwator NIE jest cichym no-opem takze na nowym srodowisku."""
        unchanged = []
        for genome in GENOMES:
            for seed in SEEDS:
                on = run_pattern_echo(genome_preset=genome, seed=seed, scenario=scenario, observe=True)
                off = run_pattern_echo(genome_preset=genome, seed=seed, scenario=scenario, observe=False)
                if _subset(on, L1_1_OBSERVATION_FIELDS) == _subset(off, L1_1_OBSERVATION_FIELDS):
                    unchanged.append(on["run_id"])
        assert not unchanged, f"obserwator nie zmienil observation fields na {scenario} w {unchanged}"


@pytest.mark.parametrize("scenario", ALL_NEW_USAGES)
class TestNewEnvironmentTelemetryValidity:
    """(c) Walidator telemetrii zielony (ta sama logika co scripts/validate_observability.py)."""

    def test_l1_1_snapshot_diagnostics_clean(self, scenario):
        for genome in GENOMES:
            for seed in SEEDS:
                r = run_pattern_echo(genome_preset=genome, seed=seed, scenario=scenario, observe=True)
                errors = diagnostics_errors(r["snapshot_diagnostics"], label=r["run_id"])
                assert not errors, errors

    def test_l1_2_snapshot_diagnostics_clean(self, scenario):
        for genome in GENOMES:
            for seed in SEEDS:
                r = run_shock_recovery(genome_preset=genome, seed=seed, scenario=scenario, observe=True)
                errors = diagnostics_errors(r["snapshot_diagnostics"], label=r["run_id"])
                assert not errors, errors


class TestNewScenariosProduceValidSignal:
    """Kazde nowe srodowisko musi byc CZYSTA funkcja (tick, seed) w [0,1] - ten sam
    kontrakt co wszystkie istniejace scenariusze (clos_world/scenarios.py)."""

    def test_bounded_and_deterministic(self):
        from clos_world.world_runtime import WorldRuntime
        wr = WorldRuntime()
        for scenario in NEW_ENVIRONMENTS:
            run1 = [wr.step(tick=t, seed=7, scenario=scenario) for t in range(60)]
            run2 = [wr.step(tick=t, seed=7, scenario=scenario) for t in range(60)]
            assert run1 == run2, f"{scenario} nie jest deterministyczny dla ustalonego seeda"
            assert all(0.0 <= v <= 1.0 for v in run1), f"{scenario} wyszedl poza [0,1]"
