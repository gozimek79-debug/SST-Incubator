"""Scenariusze eksperymentalne CLOS v0.7.3."""

import random
from .generators import sine_wave, gaussian_noise, step_signal

CONTROL_ENVIRONMENTS = {"stable_world"}

def is_control(name: str) -> bool:
    return name in CONTROL_ENVIRONMENTS

def stable_world(tick: int, seed: int = 0) -> float:
    return sine_wave(tick, frequency=0.1, amplitude=0.4)

def noise_world(tick: int, seed: int = 0) -> float:
    signal = sine_wave(tick, frequency=0.1, amplitude=0.3)
    noise = gaussian_noise(tick, mean=0.0, variance=0.05, seed=seed)
    return max(0.0, min(1.0, signal + noise))

def drift_world(tick: int, seed: int = 0) -> float:
    """DRIFT_WORLD v0.7.3 – stochastyczny dryft zalezny od seedu."""
    import math
    rng = random.Random(seed)
    phase_shift = rng.uniform(0, 2 * math.pi)
    noise_amplitude = rng.uniform(0.01, 0.05)
    progress = min(1.0, tick / 300)
    freq = 0.05 + 0.45 * progress
    signal = 0.5 + 0.3 * math.sin(2 * math.pi * freq * tick + phase_shift)
    noise = gaussian_noise(tick, mean=0.0, variance=noise_amplitude, seed=seed)
    return max(0.0, min(1.0, signal + noise))

def shock_world(tick: int, seed: int = 0) -> float:
    rng = random.Random(seed)
    shock_tick = rng.randint(20, 80)
    shock_magnitude = rng.uniform(0.3, 0.9)
    if tick < shock_tick: return 0.2
    elif tick == shock_tick: return shock_magnitude
    else:
        noise = gaussian_noise(tick, mean=0.0, variance=0.02, seed=seed)
        return max(0.1, min(1.0, shock_magnitude * 0.8 + noise))

SCENARIOS = {"stable_world":stable_world,"noise_world":noise_world,"drift_world":drift_world,"shock_world":shock_world}
def get_scenario(name: str):
    if name not in SCENARIOS: raise ValueError(f"Unknown: {name}")
    return SCENARIOS[name]
def list_scenarios(): return list(SCENARIOS.keys())
