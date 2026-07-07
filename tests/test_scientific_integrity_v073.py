"""Testy Scientific Integrity v0.7.3 – Noise + Drift stochastic."""

from clos_world.scenarios import noise_world, drift_world, is_control
from clos_curriculum.laboratory.statistics import compute_ci95

def _series(fn, seed, ticks=120):
    return [fn(t, seed=seed) for t in range(ticks)]

class TestNoiseWorldIntegrity:
    def test_noise_world_varies_by_seed(self):
        a = _series(noise_world, 100)
        b = _series(noise_world, 200)
        assert a != b, "noise_world must vary by seed"

    def test_noise_world_endpoint_variance_positive(self):
        endpoints = [noise_world(119, seed=s) for s in (100,200,300,400,500)]
        stats = compute_ci95(endpoints)
        assert stats["n_effective"] >= 2
        assert stats["ci95_valid"] is True

class TestDriftWorldIntegrity:
    def test_drift_world_varies_by_seed(self):
        a = _series(drift_world, 100)
        b = _series(drift_world, 200)
        assert a != b, "drift_world must vary by seed (v0.7.3 stochastic)"

    def test_drift_world_not_control(self):
        assert not is_control("drift_world"), "drift_world is stochastic, not control"

    def test_drift_world_endpoint_variance_positive(self):
        endpoints = [drift_world(299, seed=s) for s in (100,200,300,400,500)]
        stats = compute_ci95(endpoints)
        assert stats["n_effective"] >= 2
