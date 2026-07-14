"""SPRINT_v0.10.1.md P3: bramka regresyjna dla wstrzykiwania genome_params.

Dowod tego samego typu co observe=True/False (v0.10 P1/P2,
tests/test_observer_removability.py): dodanie NOWEGO, opcjonalnego parametru
(genome_params=None domyslnie) do run_pattern_echo()/run_shock_recovery() NIE
MOZE zmienic ANI JEDNEJ liczby dla istniejacych presetow (default,
highly_plastic) wzgledem kodu SPRZED tej zmiany. Wymagane wprost przez
publications/preregistration_v0_10_1_population.json,
implementation_plan_gate_for_p3.additive_genome_injection.
"""

import json

import pytest

from clos_academy.lesson_L1_1 import run_pattern_echo
from clos_academy.lesson_L1_2 import run_shock_recovery

# Zlote wartosci - primary endpoint znany i zaraportowany od v0.9/v0.10
# (RAPORT_v0.10.md, tabela regresji): L1.1 default/highly_plastic mean MSE@50,
# L1.2 default mean recovery_time. Jesli te liczby sie zmienia, to jest STOP.
KNOWN_L1_1_MEANS = {"default": 0.156712, "highly_plastic": 0.173229}
KNOWN_L1_2_DEFAULT_RECOVERY_MEAN = 15.4


def _strip_telemetry(r):
    return {k: v for k, v in r.items() if k != "telemetry"}


class TestGenomeParamsNoneIsNoOp:
    """genome_params=None (domyslne) musi dac dokladnie to, co kod PRZED dodaniem
    tego parametru - zero roznicy, nie tylko 'w przyblizeniu'."""

    def test_l1_1_matches_committed_report(self):
        with open("reports/academy/L1_1_pattern_echo.json", encoding="utf-8") as f:
            committed = json.load(f)

        for genome in ("default", "highly_plastic"):
            for seed in range(1, 11):
                fresh = run_pattern_echo(genome_preset=genome, seed=seed, scenario="noise_world")
                matching = next(
                    r for r in committed["results"]
                    if r["genome"] == genome and r["seed"] == seed and r["scenario"] == "noise_world"
                )
                assert _strip_telemetry(fresh) == matching, (
                    f"STOP (SPRINT_v0.10.1.md P3): genome_params=None zmienil wynik L1.1 "
                    f"{genome}/seed={seed} wzgledem juz zacommitowanego raportu"
                )

    def test_l1_2_matches_committed_report(self):
        with open("reports/academy/L1_2_shock_recovery.json", encoding="utf-8") as f:
            committed = json.load(f)

        for genome in ("default", "highly_plastic"):
            for seed in range(1, 11):
                fresh = run_shock_recovery(genome_preset=genome, seed=seed, scenario="shock_world")
                matching = next(
                    r for r in committed["results"]
                    if r["genome"] == genome and r["seed"] == seed and r["scenario"] == "shock_world"
                )
                assert _strip_telemetry(fresh) == matching, (
                    f"STOP (SPRINT_v0.10.1.md P3): genome_params=None zmienil wynik L1.2 "
                    f"{genome}/seed={seed} wzgledem juz zacommitowanego raportu"
                )

    def test_l1_1_primary_endpoint_means_unchanged(self):
        for genome, expected_mean in KNOWN_L1_1_MEANS.items():
            values = [
                run_pattern_echo(genome_preset=genome, seed=s, scenario="noise_world")["primary_endpoint"]["value"]
                for s in range(1, 11)
            ]
            mean = round(sum(values) / len(values), 6)
            assert mean == expected_mean, f"{genome}: mean={mean} != zlota wartosc {expected_mean}"

    def test_l1_2_default_recovery_time_mean_unchanged(self):
        values = []
        for s in range(1, 11):
            r = run_shock_recovery(genome_preset="default", seed=s, scenario="shock_world")
            pe = r["primary_endpoint"]
            if not pe["censored"]:
                values.append(pe["value"])
        mean = round(sum(values) / len(values), 6)
        assert mean == KNOWN_L1_2_DEFAULT_RECOVERY_MEAN


class TestGenomeParamsOverridesOnlyFiveFields:
    """Gdy genome_params JEST podany, musi nadpisac WYLACZNIE te 5 pol - reszta
    (final_energy, final_entropy, memory_size, telemetry, primary_endpoint)
    nadal wynika normalnie z Execution (world+brain_rt), nie z genome_params."""

    def test_custom_params_change_tissue_but_not_crash(self):
        custom = {
            "plasticity": 0.5, "learning_rate": 0.2, "decay_rate": 0.03,
            "homeostasis_target": 0.4, "memory_capacity": 300,
        }
        r = run_pattern_echo(genome_preset="default", seed=1, scenario="noise_world",
                              genome_params=custom, genome_label="pop_test_001")
        assert r["genome"] == "pop_test_001"
        assert r["run_id"] == "L1.1_pop_test_001_s1_noise_world"
        assert isinstance(r["primary_endpoint"]["value"], float)

    def test_custom_params_give_different_result_than_default(self):
        """Genom z realnie innymi parametrami MUSI dac inny wynik - inaczej
        genome_params byloby cichym no-opem (ten sam blad, ktory P1/P2 sprawdzal
        dla obserwatora, teraz dla wstrzykiwania genomu)."""
        baseline = run_pattern_echo(genome_preset="default", seed=1, scenario="noise_world")
        custom = run_pattern_echo(
            genome_preset="default", seed=1, scenario="noise_world",
            genome_params={"plasticity": 0.15, "learning_rate": 0.9, "decay_rate": 0.09,
                            "homeostasis_target": 0.9, "memory_capacity": 15},
        )
        assert baseline["primary_endpoint"]["value"] != custom["primary_endpoint"]["value"], (
            "genome_params nie zmienil wyniku - podejrzenie cichego no-opa"
        )
