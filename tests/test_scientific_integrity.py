"""Testy WAŻNOŚCI NAUKOWEJ (v0.7.2).

Różnią się od testów jednostkowych: nie sprawdzają, czy kod się wykonuje,
lecz czy eksperyment MA SENS. Zielony kod przy martwej zmiennej scenariusza
(bug z v0.4/v0.5) przeszedłby testy jednostkowe — te testy by go złapały.
"""

from clos_world.scenarios import stable_world, shock_world, is_control
from clos_curriculum.laboratory.statistics import (
    compute_ci95, glass_delta, validate_sample_size, metrology_report,
)


def _series(fn, seed, ticks=120):
    return [fn(t, seed=seed) for t in range(ticks)]


class TestControlEnvironment:
    def test_stable_world_is_declared_control(self):
        assert is_control("stable_world") is True

    def test_stable_world_deterministic_across_seeds(self):
        # OCZEKIWANE: kontrola daje identyczny przebieg dla każdego seedu.
        a = _series(stable_world, 100)
        b = _series(stable_world, 200)
        c = _series(stable_world, 999)
        assert a == b == c, "Środowisko kontrolne musi być deterministyczne"


class TestStochasticScenario:
    def test_shock_world_varies_by_seed(self):
        # Scenariusz stochastyczny MUSI reagować na seed (inaczej martwa zmienna).
        a = _series(shock_world, 100)
        b = _series(shock_world, 200)
        assert a != b, "shock_world musi zależeć od seedu (realna wariancja)"

    def test_shock_world_endpoint_variance_positive(self):
        endpoints = [shock_world(119, seed=s) for s in (100, 200, 300, 400, 500)]
        stats = compute_ci95(endpoints)
        assert stats["n_effective"] >= 2
        assert stats["ci95_valid"] is True


class TestMetrologyGuards:
    def test_ci95_flags_deterministic_as_invalid(self):
        stats = compute_ci95([2.2089, 2.2089, 2.2089])
        assert stats["deterministic"] is True
        assert stats["ci95_valid"] is False
        assert stats["n_effective"] == 1

    def test_ci95_real_interval_is_valid(self):
        stats = compute_ci95([1.0, 2.0, 3.0, 4.0, 5.0])
        assert stats["ci95_valid"] is True
        assert stats["ci95_low"] < stats["mean"] < stats["ci95_high"]

    def test_sample_size_detects_pseudoreplication(self):
        check = validate_sample_size([0.84, 0.84, 0.84])
        assert check["pseudoreplication_warning"] is True
        assert check["n_effective"] == 1

    def test_glass_delta_works_against_zero_variance_control(self):
        control = [2.20, 2.20, 2.20]          # deterministyczna kontrola
        experimental = [1.9, 2.1, 1.8, 2.0]   # warunek stochastyczny
        res = glass_delta(control, experimental)
        assert res["computable"] is True
        assert res["delta"] is not None

    def test_metrology_report_marks_control(self):
        rep = metrology_report([2.2089, 2.2089, 2.2089], control=True, label="L0.1")
        assert rep["control_environment"] is True
        assert rep["ci95_valid"] is False


class TestRegressionGuards:
    def test_kernel_imports(self):
        # Regresja: brak importu typing.List psuł zbieranie testów na HEAD.
        from clos_kernel.kernel import Kernel
        assert Kernel is not None
