"""SPRINT_v0.11.0.md P2: name-gate -> property-gate + wyjatki opisowe.

Trzy rzeczy do udowodnienia (zadanie CTO, zasada nadrzedna 1 "cisza gorsza
niz blad" + zasada nadrzedna 4 "regression gate"):

  (a) weak_shock_world i long_stable_shock_world TERAZ licza primary_endpoint
      (naprawiony name-gate) - wczesniej byly cicho pomijane.
  (b) recurring_shock_world nadal go NIE liczy - to prawdziwy brak
      zastosowania konstruktu (wielokrotne perturbacje), nie regresja bledu.
  (c) naruszenie domeny okna sustained-in-band podnosi jawny
      RecoveryWindowOutOfDomainError (metric/scenario/condition/reason), nie
      cichy brak wyniku ani niejasny KeyError.

Regresja bytow istniejacych (shock_world) jest osobno pokryta przez
tests/test_genome_params_regression.py (0.156712/0.173229/15.4) i
tests/test_observer_removability.py - ten plik NIE ich duplikuje.
"""

import pytest

from clos_academy.lesson_L1_2 import (
    RecoveryWindowOutOfDomainError,
    _validate_recovery_window_domain,
    run_shock_recovery,
)
from clos_world.scenarios import has_single_perturbation, single_perturbation_tick

SEEDS = list(range(1, 11))


class TestNameGateFixedToPropertyGate:
    """(a) Scenariusze semantycznie jednoperturbacyjne teraz licza endpoint."""

    @pytest.mark.parametrize("scenario", ["weak_shock_world", "long_stable_shock_world"])
    def test_now_produces_primary_endpoint(self, scenario):
        for seed in SEEDS:
            r = run_shock_recovery(genome_preset="default", seed=seed, scenario=scenario)
            assert "primary_endpoint" in r, (
                f"{scenario} seed={seed}: primary_endpoint wciaz cicho pomijany "
                "(name-gate NIE naprawiony)"
            )
            assert "t_shock" in r and "pre_shock_in_band" in r

    def test_registry_agrees_with_has_single_perturbation(self):
        assert has_single_perturbation("shock_world")
        assert has_single_perturbation("weak_shock_world")
        assert has_single_perturbation("long_stable_shock_world")


class TestRecurringShockRemainsNotApplicable:
    """(b) Wielokrotna perturbacja nie pasuje do modelu "jeden t_shock" -
    to jest prawdziwy brak zastosowania konstruktu, NIE regresja bledu."""

    def test_has_single_perturbation_false(self):
        assert not has_single_perturbation("recurring_shock_world")

    def test_no_primary_endpoint_and_no_exception(self):
        for seed in SEEDS:
            r = run_shock_recovery(genome_preset="default", seed=seed, scenario="recurring_shock_world")
            assert "primary_endpoint" not in r
            assert "t_shock" not in r


class TestRecoveryWindowDomainException:
    """(c) Naruszenie domeny okna -> wyjatek opisowy, nie cichy/niejasny blad."""

    def test_boundary_t_shock_150_is_still_valid(self):
        _validate_recovery_window_domain("long_stable_shock_world", t_shock=150)  # nie podnosi

    def test_t_shock_151_raises_with_full_description(self):
        with pytest.raises(RecoveryWindowOutOfDomainError) as exc_info:
            _validate_recovery_window_domain("long_stable_shock_world", t_shock=151)
        err = exc_info.value
        assert err.metric == "recovery_time"
        assert err.scenario == "long_stable_shock_world"
        assert "t_shock" in err.condition
        assert "151" in str(err)

    def test_boundary_t_shock_10_is_still_valid(self):
        _validate_recovery_window_domain("shock_world", t_shock=10)  # nie podnosi

    def test_t_shock_9_raises_pre_shock_condition(self):
        with pytest.raises(RecoveryWindowOutOfDomainError) as exc_info:
            _validate_recovery_window_domain("shock_world", t_shock=9)
        err = exc_info.value
        assert err.metric == "pre_shock_in_band"
        assert "N" in err.condition

    def test_existing_scenarios_never_violate_domain_across_all_seeds(self):
        """shock_world (max t_shock=80), weak_shock_world (max=80) i
        long_stable_shock_world (max=150) musza zostac w domenie dla KAZDEGO
        seeda uzywanego w projekcie - to jest wlasnie powod, dla ktorego te
        zakresy zostaly tak zaprojektowane (patrz docstringi w scenarios.py)."""
        for scenario in ("shock_world", "weak_shock_world", "long_stable_shock_world"):
            for seed in range(1, 51):
                t_shock = single_perturbation_tick(scenario, seed)
                _validate_recovery_window_domain(scenario, t_shock)  # nie moze podniesc
