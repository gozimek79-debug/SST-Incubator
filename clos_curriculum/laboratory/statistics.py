"""Laboratory Statistics – CI95, Effect Size, Sample Size validation."""

import math
from typing import List, Dict, Any


def compute_ci95(values: List[float]) -> Dict[str, float]:
    """Oblicza 95% przedział ufności.

    Args:
        values: Lista wartości.

    Returns:
        Słownik z mean, std, ci95_low, ci95_high, n.
    """
    if not values:
        return {"mean": 0, "std": 0, "ci95_low": 0, "ci95_high": 0, "n": 0}

    n = len(values)
    mean = sum(values) / n
    std = math.sqrt(sum((v - mean)**2 for v in values) / (n - 1)) if n > 1 else 0.0
    ci95_margin = 1.96 * std / math.sqrt(n) if n > 1 and std > 0 else 0.0

    return {
        "mean": round(mean, 6),
        "std": round(std, 6),
        "ci95_low": round(mean - ci95_margin, 6),
        "ci95_high": round(mean + ci95_margin, 6),
        "n": n,
    }


def cohens_d(group_a: List[float], group_b: List[float]) -> float:
    """Oblicza Cohen's d (effect size) między dwiema grupami.

    Args:
        group_a: Pierwsza grupa.
        group_b: Druga grupa.

    Returns:
        Wartość Cohen's d.
    """
    if len(group_a) < 2 or len(group_b) < 2:
        return 0.0

    mean_a = sum(group_a) / len(group_a)
    mean_b = sum(group_b) / len(group_b)

    var_a = sum((v - mean_a)**2 for v in group_a) / (len(group_a) - 1)
    var_b = sum((v - mean_b)**2 for v in group_b) / (len(group_b) - 1)

    pooled_std = math.sqrt((var_a + var_b) / 2)
    if pooled_std < 1e-9:
        return 0.0

    return (mean_a - mean_b) / pooled_std


def validate_sample_size(values: List[float], min_n: int = 5) -> Dict[str, Any]:
    """Sprawdza czy próbka jest wystarczająca.

    Args:
        values: Lista wartości.
        min_n: Minimalna liczba próbek.

    Returns:
        Słownik z walidacją.
    """
    n = len(values)
    return {
        "sample_size": n,
        "min_required": min_n,
        "sufficient": n >= min_n,
        "can_compute_ci95": n >= 2,
        "can_compute_effect_size": n >= 3,
    }
