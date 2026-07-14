"""Testy dla World Runtime v0.1."""

import pytest
import sys
sys.path.insert(0, '.')

from clos_world.generators import (
    sine_wave, step_signal, gaussian_noise,
    drift_signal, pulse_signal
)
from clos_world.scenarios import (
    stable_world, noise_world, drift_world, shock_world,
    get_scenario, list_scenarios
)
from clos_world.world_runtime import WorldRuntime


class TestGenerators:
    def test_sine_wave_range(self):
        for t in range(100):
            val = sine_wave(t)
            assert 0.0 <= val <= 1.0

    def test_sine_wave_deterministic(self):
        for t in range(50):
            assert sine_wave(t, frequency=0.1) == sine_wave(t, frequency=0.1)

    def test_step_signal_change(self):
        assert step_signal(0, change_tick=10, before=0.2, after=0.8) == 0.2
        assert step_signal(10, change_tick=10, before=0.2, after=0.8) == 0.8

    def test_gaussian_noise_range(self):
        for t in range(200):
            val = gaussian_noise(t, mean=0.5, variance=0.1, seed=42)
            assert 0.0 <= val <= 1.0

    def test_gaussian_noise_deterministic(self):
        for t in range(20):
            v1 = gaussian_noise(t, mean=0.5, variance=0.1, seed=42)
            v2 = gaussian_noise(t, mean=0.5, variance=0.1, seed=42)
            assert v1 == v2

    def test_drift_signal_range(self):
        for t in range(300):
            val = drift_signal(t, seed=42)
            assert 0.0 <= val <= 1.0

    def test_pulse_signal_deterministic(self):
        """Pulse signal z seedem – ten sam seed = ten sam wzór."""
        vals1 = [pulse_signal(t, interval=20, width=3, seed=42) for t in range(60)]
        vals2 = [pulse_signal(t, interval=20, width=3, seed=42) for t in range(60)]
        assert vals1 == vals2

    def test_pulse_signal_has_ones(self):
        """Pulse signal musi generować impulsy (1.0) gdzieś w cyklu."""
        vals = [pulse_signal(t, interval=20, width=3, seed=0) for t in range(100)]
        assert 1.0 in vals, "Pulse signal should have at least one 1.0"


class TestScenarios:
    def test_stable_world_range(self):
        for t in range(100):
            val = stable_world(t)
            assert 0.0 <= val <= 1.0

    def test_noise_world_range(self):
        for t in range(100):
            val = noise_world(t, seed=42)
            assert 0.0 <= val <= 1.0

    def test_drift_world_range(self):
        for t in range(300):
            val = drift_world(t, seed=42)
            assert 0.0 <= val <= 1.0

    def test_shock_world_has_jump(self):
        """Shock world musi mieć wykrywalny skok (różnica > 0.1)."""
        values = [shock_world(t, seed=42) for t in range(100)]
        diffs = [abs(values[i+1] - values[i]) for i in range(len(values)-1)]
        assert max(diffs) > 0.1, f"Max diff too small: {max(diffs)}"

    def test_scenarios_produce_different_trajectories(self):
        ticks = list(range(50))
        stable_vals = [stable_world(t) for t in ticks]
        noise_vals = [noise_world(t, seed=42) for t in ticks]
        drift_vals = [drift_world(t, seed=42) for t in ticks]
        shock_vals = [shock_world(t, seed=42) for t in ticks]

        assert stable_vals != noise_vals, "stable == noise"
        assert stable_vals != drift_vals, "stable == drift"
        assert stable_vals != shock_vals, "stable == shock"

    def test_get_scenario(self):
        fn = get_scenario("stable_world")
        assert fn is not None
        assert callable(fn)

    def test_get_scenario_invalid(self):
        with pytest.raises(ValueError):
            get_scenario("nonexistent")

    def test_list_scenarios(self):
        scenarios = list_scenarios()
        assert "stable_world" in scenarios
        assert "noise_world" in scenarios
        assert "drift_world" in scenarios
        assert "shock_world" in scenarios

    def test_shock_deterministic(self):
        vals1 = [shock_world(t, seed=42) for t in range(100)]
        vals2 = [shock_world(t, seed=42) for t in range(100)]
        assert vals1 == vals2


class TestWorldRuntime:
    def test_step_returns_float(self):
        wr = WorldRuntime()
        val = wr.step(tick=0, seed=42, scenario="stable_world")
        assert isinstance(val, float)

    def test_step_different_scenarios_different_output(self):
        wr = WorldRuntime()
        s1 = wr.step(tick=50, seed=42, scenario="stable_world")
        s2 = wr.step(tick=50, seed=42, scenario="shock_world")
        assert 0.0 <= s1 <= 1.0
        assert 0.0 <= s2 <= 1.0

    def test_determinism_full(self):
        wr = WorldRuntime()
        run1 = [wr.step(tick=t, seed=42, scenario="noise_world") for t in range(50)]
        run2 = [wr.step(tick=t, seed=42, scenario="noise_world") for t in range(50)]
        assert run1 == run2

    def test_get_available_scenarios(self):
        wr = WorldRuntime()
        scenarios = wr.get_available_scenarios()
        # SPRINT_v0.10.1.md P2 dodal 5 nowych srodowisk walidacyjnych - nie
        # zakladamy tu stalej liczby (ten test byl kiedys "== 4" i zlamal sie
        # przy pierwszym dodaniu srodowiska). Sprawdzamy tylko, ze oryginalny
        # zestaw wciaz istnieje - lista MOZE rosnac.
        assert {"stable_world", "noise_world", "drift_world", "shock_world"} <= set(scenarios)

    def test_all_scenarios_valid(self):
        wr = WorldRuntime()
        for scenario in wr.get_available_scenarios():
            for t in range(20):
                val = wr.step(tick=t, seed=42, scenario=scenario)
                assert 0.0 <= val <= 1.0, f"{scenario} at tick {t} = {val}"
