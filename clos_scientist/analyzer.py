"""Analyzer – detekcja faz poznawczych i anomalii.

Model 3-fazowy: INITIAL CHAOS → ADAPTATION → CONVERGENCE.
"""

import math
from typing import List, Dict, Tuple
from clos_kernel.snapshot_engine import Snapshot


def detect_phases(snapshots: List[Snapshot]) -> Dict[str, int]:
    """Wykryj fazy w przebiegu eksperymentu.

    Args:
        snapshots: Lista snapshotów posortowana po ticku.

    Returns:
        Słownik: {"initial_chaos": tick, "adaptation": tick, "convergence": tick}
    """
    if not snapshots:
        return {"initial_chaos": 0, "adaptation": 0, "convergence": 0}

    entropies = [s.entropy for s in snapshots]

    # Faza 1: Initial Chaos – od tick 0
    initial_chaos_tick = 0

    # Faza 2: Adaptation – gdy entropia zaczyna spadać
    adaptation_tick = _find_adaptation_start(entropies)

    # Faza 3: Convergence – gdy entropia się stabilizuje
    convergence_tick = _find_convergence_start(entropies, adaptation_tick)

    return {
        "initial_chaos": initial_chaos_tick,
        "adaptation": adaptation_tick,
        "convergence": convergence_tick
    }


def detect_anomalies(snapshots: List[Snapshot], threshold_sigma: float = 3.0) -> List[int]:
    """Wykryj ticki anomalne.

    Anomalia: wartość entropii > mean + threshold_sigma * std

    Args:
        snapshots: Lista snapshotów.
        threshold_sigma: Próg w odchyleniach standardowych.

    Returns:
        Lista numerów ticków z anomaliami.
    """
    if len(snapshots) < 3:
        return []

    entropies = [s.entropy for s in snapshots]
    mean = sum(entropies) / len(entropies)
    std = _std(entropies)

    if std < 1e-9:
        return []

    threshold = mean + threshold_sigma * std
    anomalies = []

    for s in snapshots:
        if s.entropy > threshold:
            anomalies.append(s.tick)

    return anomalies


def compute_adaptation_speed(snapshots: List[Snapshot]) -> int:
    """Oszacuj tick, w którym system zaczął się adaptować.

    Args:
        snapshots: Lista snapshotów.

    Returns:
        Numer ticka rozpoczęcia adaptacji.
    """
    if not snapshots:
        return 0

    entropies = [s.entropy for s in snapshots]
    return _find_adaptation_start(entropies)


def _find_adaptation_start(entropies: List[float], window: int = 10) -> int:
    """Znajdź tick, gdzie entropia zaczyna spadać (początek adaptacji).

    Szuka punktu gdzie: rolling_mean(entropy[t:t+window]) < rolling_mean(entropy[0:window])
    """
    if len(entropies) < window * 2:
        return 0

    initial_mean = sum(entropies[:window]) / window

    for t in range(window, len(entropies) - window):
        current_mean = sum(entropies[t:t + window]) / window
        if current_mean < initial_mean * 0.9:
            return t

    return 0


def _find_convergence_start(entropies: List[float], adaptation_tick: int, window: int = 20) -> int:
    """Znajdź tick, gdzie entropia się stabilizuje (początek konwergencji).

    Szuka punktu gdzie rolling_std < próg.
    """
    if len(entropies) < adaptation_tick + window:
        return len(entropies) - 1 if entropies else 0

    for t in range(adaptation_tick, len(entropies) - window):
        segment = entropies[t:t + window]
        if _std(segment) < 0.01:
            return t

    return len(entropies) - 1 if entropies else 0


def _std(values: List[float]) -> float:
    """Odchylenie standardowe."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)
