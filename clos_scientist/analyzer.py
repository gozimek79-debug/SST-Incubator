"""Analyzer v2 – dynamiczny detektor faz na podstawie szeregów czasowych."""

import math
from typing import List, Dict
from clos_kernel.snapshot_engine import Snapshot


def detect_phases(snapshots: List[Snapshot]) -> Dict[str, int]:
    """Wykryj fazy dynamicznie na podstawie entropii i energii.

    - initial_chaos: tick 0 do momentu gdy entropy_volatility < próg
    - adaptation: od spadku entropii do stabilizacji energii
    - convergence: gdy MSE z 10 ticków stabilne (delta < 0.01)

    Args:
        snapshots: Lista snapshotów posortowana po ticku.

    Returns:
        Słownik z tickami przejść fazowych.
    """
    if len(snapshots) < 20:
        return {"initial_chaos": 0, "adaptation": 0, "convergence": 0}

    entropies = [s.entropy for s in snapshots]
    energies = [s.energy for s in snapshots]

    # Faza 1: initial_chaos → trwa dopóki zmienność entropii jest wysoka
    chaos_end = _find_chaos_end(entropies)

    # Faza 2: adaptation → od końca chaosu do stabilizacji energii
    adaptation_start = chaos_end
    adaptation_end = _find_adaptation_end(energies, adaptation_start)

    # Faza 3: convergence → od stabilizacji energii do końca
    convergence_start = _find_convergence_start(entropies, adaptation_end)

    return {
        "initial_chaos": 0,
        "adaptation": adaptation_start if adaptation_start > 0 else _estimate_adaptation(entropies),
        "convergence": convergence_start if convergence_start > adaptation_end else max(adaptation_end, len(snapshots) - 1),
    }


def _find_chaos_end(entropies: List[float], window: int = 10, threshold: float = 0.02) -> int:
    """Szuka punktu gdzie rolling std entropii spada poniżej progu."""
    if len(entropies) < window * 2:
        return 0

    for t in range(window, len(entropies) - window):
        segment = entropies[t:t + window]
        if _std(segment) < threshold:
            return t

    return len(entropies) // 4


def _find_adaptation_end(energies: List[float], start_tick: int, window: int = 10, threshold: float = 0.005) -> int:
    """Szuka punktu gdzie dryft energii stabilizuje się (delta < threshold)."""
    if start_tick >= len(energies) - window:
        return len(energies) - 1

    for t in range(start_tick, len(energies) - window):
        segment = energies[t:t + window]
        energy_range = max(segment) - min(segment)
        if energy_range < threshold:
            return t

    return len(energies) - 1


def _find_convergence_start(entropies: List[float], start_tick: int, window: int = 10, mse_threshold: float = 0.01) -> int:
    """Szuka punktu gdzie MSE z ostatnich N ticków stabilne."""
    if start_tick >= len(entropies) - window:
        return len(entropies) - 1

    for t in range(start_tick, len(entropies) - window):
        segment = entropies[t:t + window]
        mean_val = sum(segment) / len(segment)
        mse_val = sum((v - mean_val) ** 2 for v in segment) / len(segment)
        if mse_val < mse_threshold:
            return t

    return len(entropies) - 1


def _estimate_adaptation(entropies: List[float]) -> int:
    """Szacuje początek adaptacji jako pierwszy znaczący spadek entropii."""
    if len(entropies) < 10:
        return 0

    max_entropy = max(entropies[:len(entropies)//2])
    for t in range(len(entropies)//4, len(entropies)):
        if entropies[t] < max_entropy * 0.8:
            return t

    return len(entropies) // 3


def detect_anomalies(snapshots: List[Snapshot], threshold_sigma: float = 3.0) -> List[int]:
    """Wykryj ticki anomalne."""
    if len(snapshots) < 3:
        return []

    entropies = [s.entropy for s in snapshots]
    mean = sum(entropies) / len(entropies)
    std = _std(entropies)

    if std < 1e-9:
        return []

    threshold = mean + threshold_sigma * std
    return [s.tick for s in snapshots if s.entropy > threshold]


def compute_adaptation_speed(snapshots: List[Snapshot]) -> int:
    """Zwraca tick rozpoczęcia adaptacji."""
    if not snapshots:
        return 0
    entropies = [s.entropy for s in snapshots]
    phases = detect_phases(snapshots)
    return phases.get("adaptation", _estimate_adaptation(entropies))


def _std(values: List[float]) -> float:
    """Odchylenie standardowe."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)
