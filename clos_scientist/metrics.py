"""Metrics Engine – obliczenia numeryczne na snapshotach."""

import math
from typing import List, Dict
from clos_kernel.snapshot_engine import Snapshot


def stability_index(snapshots: List[Snapshot]) -> float:
    """SI = 1 / (std(entropy) + std(error) + 1e-6).

    Args:
        snapshots: Lista snapshotów.

    Returns:
        Wartość SI – im wyższa, tym stabilniejszy system.
    """
    if len(snapshots) < 2:
        return 0.0

    entropies = [s.entropy for s in snapshots]
    std_entropy = _std(entropies)

    # Używamy energy jako proxy error (w snapshotach nie ma bezpośredniego error)
    errors = [abs(1.0 - s.energy) for s in snapshots]
    std_error = _std(errors)

    return 1.0 / (std_entropy + std_error + 1e-6)


def mse(snapshots: List[Snapshot]) -> float:
    """Mean Squared Error – MSE = mean((energy - 1.0)^2).

    Args:
        snapshots: Lista snapshotów.

    Returns:
        Wartość MSE.
    """
    if not snapshots:
        return 0.0

    errors = [(1.0 - s.energy) ** 2 for s in snapshots]
    return sum(errors) / len(errors)


def energy_drift(snapshots: List[Snapshot]) -> float:
    """Zmiana energii od początku do końca.

    Args:
        snapshots: Lista snapshotów.

    Returns:
        energy_final - energy_initial
    """
    if len(snapshots) < 2:
        return 0.0

    return snapshots[-1].energy - snapshots[0].energy


def entropy_volatility(snapshots: List[Snapshot]) -> float:
    """Odchylenie standardowe krzywej entropii.

    Args:
        snapshots: Lista snapshotów.

    Returns:
        std(entropy_curve).
    """
    if len(snapshots) < 2:
        return 0.0

    entropies = [s.entropy for s in snapshots]
    return _std(entropies)


def memory_growth_rate(snapshots: List[Snapshot]) -> float:
    """Tempo wzrostu pamięci.

    Args:
        snapshots: Lista snapshotów.

    Returns:
        Δ(step_counter) / T – proxy dla memory growth.
    """
    if len(snapshots) < 2:
        return 0.0

    T = len(snapshots)
    delta = snapshots[-1].step_counter - snapshots[0].step_counter
    return delta / T if T > 0 else 0.0


def compute_all_metrics(snapshots: List[Snapshot]) -> Dict[str, float]:
    """Oblicz wszystkie metryki.

    Args:
        snapshots: Lista snapshotów.

    Returns:
        Słownik z wszystkimi metrykami.
    """
    return {
        "stability_index": round(stability_index(snapshots), 4),
        "mse": round(mse(snapshots), 4),
        "energy_drift": round(energy_drift(snapshots), 4),
        "entropy_volatility": round(entropy_volatility(snapshots), 4),
        "memory_growth_rate": round(memory_growth_rate(snapshots), 4)
    }


def _std(values: List[float]) -> float:
    """Oblicz odchylenie standardowe."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)
