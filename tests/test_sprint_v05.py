"""Testy dla Sprint v0.5 – zerowa wariancja i fazy dynamiczne."""

import pytest
import sys
sys.path.insert(0, '.')

from clos_world.scenarios import shock_world, stable_world, noise_world
from clos_scientist.analyzer import detect_phases, _find_chaos_end
from clos_kernel.snapshot_engine import SnapshotEngine


def make_snapshots(entropies, energies=None):
    if energies is None:
        energies = [1.0] * len(entropies)
    se = SnapshotEngine()
    for i, (ent, ene) in enumerate(zip(entropies, energies)):
        se.create_snapshot(
            brain_id="test", tick=i, seed=42,
            lifecycle_state="running", brain_status="ALIVE",
            entropy=ent, energy=ene, age=i, step_counter=i
        )
    return se.get_all_snapshots()


class TestSeedVariance:
    def test_shock_world_different_seeds_produce_different_outputs(self):
        """Różne seedy w shock_world dają różne trajektorie."""
        ticks = list(range(100))
        vals_seed1 = [shock_world(t, seed=1) for t in ticks]
        vals_seed2 = [shock_world(t, seed=2) for t in ticks]
        vals_seed3 = [shock_world(t, seed=3) for t in ticks]

        # Trajektorie muszą się różnić
        assert vals_seed1 != vals_seed2, "Seed 1 i 2 dają identyczne wyniki"
        assert vals_seed1 != vals_seed3, "Seed 1 i 3 dają identyczne wyniki"
        assert vals_seed2 != vals_seed3, "Seed 2 i 3 dają identyczne wyniki"

    def test_noise_world_variance_positive(self):
        """Wariancja noise_world dla różnych seedów > 0."""
        ticks = list(range(50))
        means = []
        for seed in range(1, 6):
            vals = [noise_world(t, seed=seed) for t in ticks]
            means.append(sum(vals) / len(vals))

        variance = sum((m - sum(means)/len(means))**2 for m in means) / (len(means) - 1)
        assert variance > 0, f"Variance is zero: {variance}"

    def test_stable_world_deterministic(self):
        """Stable world nadal deterministyczny – ten sam seed = ten sam wynik."""
        ticks = list(range(30))
        vals1 = [stable_world(t, seed=42) for t in ticks]
        vals2 = [stable_world(t, seed=42) for t in ticks]
        assert vals1 == vals2


class TestDynamicPhases:
    def test_detect_phases_returns_nonzero_adaptation(self):
        """Dla realistycznych danych adaptation nie powinno być 0."""
        # Symuluj realistyczny przebieg: chaos → adaptacja → konwergencja
        entropies = (
            [0.8, 0.75, 0.72, 0.68, 0.65, 0.62, 0.58, 0.55, 0.52, 0.5] +
            [0.48, 0.46, 0.44, 0.43, 0.42, 0.41, 0.4, 0.4, 0.39, 0.39] +
            [0.38, 0.38, 0.37, 0.37, 0.37, 0.36, 0.36, 0.36, 0.36, 0.36]
        )
        snaps = make_snapshots(entropies)
        phases = detect_phases(snaps)

        assert phases["adaptation"] > 0, f"Adaptation is 0: {phases}"
        assert phases["convergence"] > phases["adaptation"], f"Convergence before adaptation: {phases}"

    def test_chaos_end_detected(self):
        """Chaos kończy się gdy zmienność spada."""
        entropies = [0.9, 0.8, 0.7, 0.6, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                     0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        end = _find_chaos_end(entropies, window=5, threshold=0.05)
        assert end > 0, f"Chaos end is 0"

    def test_detect_phases_with_shock(self):
        """Shock z wyraźnym skokiem entropii."""
        entropies = [0.5] * 30
        entropies[15] = 0.95  # Shock
        entropies[16] = 0.7
        entropies[17] = 0.55
        entropies += [0.5] * 12
        snaps = make_snapshots(entropies)
        phases = detect_phases(snaps)

        # Po shocku powinna być wykryta adaptacja
        assert phases["adaptation"] >= 15, f"Adaptation should be after shock: {phases}"
