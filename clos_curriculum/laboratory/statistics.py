"""Laboratory Statistics – CI95, Effect Size, Sample Size validation.

v0.7.2 – Scientific integrity:
- compute_ci95 flaguje przypadki deterministyczne/kontrolne (ci95_valid=False)
  i liczbę EFEKTYWNIE niezależnych obserwacji (n_effective), by nie mylić
  powtórzeń identycznego runu ze statystyczną próbą (pseudoreplikacja).
- glass_delta: właściwy effect size przy porównaniu z deterministyczną kontrolą.
"""

import math
from typing import List, Dict, Any, Optional


def _n_effective(values: List[float]) -> int:
    """Liczba EFEKTYWNIE niezależnych obserwacji (distinct).

    Trzy identyczne wyniki deterministycznego runu to n_effective=1,
    nie n=3 — inaczej sztucznie zawyżamy moc statystyczną.
    """
    return len(set(round(v, 9) for v in values))


def compute_ci95(values: List[float]) -> Dict[str, Any]:
    """Oblicza 95% przedział ufności wraz z flagami ważności.

    Zwraca dodatkowo (v0.7.2):
        deterministic: czy wszystkie wartości są identyczne (std=0).
        ci95_valid:    czy przedział jest sensownym CI (n>=2 i std>0 i n_eff>=2).
        n_effective:   liczba distinct wartości.
        interpretation: krótki opis do raportu.
    """
    if not values:
        return {"mean": 0, "std": 0, "ci95_low": 0, "ci95_high": 0, "n": 0,
                "n_effective": 0, "deterministic": False, "ci95_valid": False,
                "interpretation": "brak danych"}

    n = len(values)
    mean = sum(values) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) if n > 1 else 0.0
    n_eff = _n_effective(values)
    deterministic = std == 0.0 and n > 1
    ci95_valid = n >= 2 and std > 0 and n_eff >= 2
    ci95_margin = 1.96 * std / math.sqrt(n) if ci95_valid else 0.0

    if deterministic:
        interp = ("wynik deterministyczny — CI95 nie ma zastosowania "
                  "(oczekiwane dla środowiska kontrolnego)")
    elif n < 2:
        interp = "n<2 — CI95 niemożliwe"
    elif not ci95_valid:
        interp = "CI95 zdegenerowane (n_effective<2)"
    else:
        interp = "CI95 poprawne"

    return {
        "mean": round(mean, 6),
        "std": round(std, 6),
        "ci95_low": round(mean - ci95_margin, 6),
        "ci95_high": round(mean + ci95_margin, 6),
        "n": n,
        "n_effective": n_eff,
        "deterministic": deterministic,
        "ci95_valid": ci95_valid,
        "interpretation": interp,
    }


def cohens_d(group_a: List[float], group_b: List[float]) -> float:
    """Cohen's d (effect size). Zwraca 0.0 gdy nieobliczalne (n<2 lub pooled std~0).

    UWAGA: przy porównaniu z deterministyczną kontrolą (wariancja=0) użyj
    glass_delta() — Cohen's d z jedną grupą o zerowej wariancji jest mylący.
    """
    if len(group_a) < 2 or len(group_b) < 2:
        return 0.0
    mean_a = sum(group_a) / len(group_a)
    mean_b = sum(group_b) / len(group_b)
    var_a = sum((v - mean_a) ** 2 for v in group_a) / (len(group_a) - 1)
    var_b = sum((v - mean_b) ** 2 for v in group_b) / (len(group_b) - 1)
    pooled_std = math.sqrt((var_a + var_b) / 2)
    if pooled_std < 1e-9:
        return 0.0
    return (mean_a - mean_b) / pooled_std


def glass_delta(control: List[float], experimental: List[float]) -> Dict[str, Any]:
    """Glass's delta — effect size względem grupy kontrolnej.

    Właściwy przy porównaniu warunku eksperymentalnego z deterministyczną
    kontrolą: używa ODCHYLENIA GRUPY EKSPERYMENTALNEJ jako skali, więc
    zerowa wariancja kontroli nie unieważnia porównania.
    """
    if len(experimental) < 2:
        return {"delta": None, "computable": False,
                "reason": "grupa eksperymentalna n<2"}
    mean_c = sum(control) / len(control) if control else 0.0
    mean_e = sum(experimental) / len(experimental)
    var_e = sum((v - mean_e) ** 2 for v in experimental) / (len(experimental) - 1)
    sd_e = math.sqrt(var_e)
    if sd_e < 1e-9:
        return {"delta": None, "computable": False,
                "reason": "grupa eksperymentalna bez wariancji"}
    return {"delta": round((mean_e - mean_c) / sd_e, 6), "computable": True,
            "reason": "OK"}


def metrology_report(values: List[float], control: bool = False,
                     label: str = "") -> Dict[str, Any]:
    """Pełny blok metrologiczny dla jednego warunku.

    Args:
        values: obserwacje (np. metryka per seed).
        control: czy warunek jest deterministycznym środowiskiem kontrolnym.
                 Jeśli True, CI95 jest jawnie oznaczone jako nie-dotyczy.
    """
    ci = compute_ci95(values)
    is_control_flag = control or ci["deterministic"]
    if is_control_flag:
        ci["ci95_valid"] = False
        ci["interpretation"] = ("środowisko kontrolne / deterministyczne — "
                                "CI95 nie dotyczy, zerowa wariancja oczekiwana")
    return {
        "label": label,
        "control_environment": bool(control),
        **ci,
        "sample_size": validate_sample_size(values),
    }


def validate_sample_size(values: List[float], min_n: int = 5) -> Dict[str, Any]:
    """Sprawdza czy próbka jest wystarczająca (używa n_effective)."""
    n = len(values)
    n_eff = _n_effective(values)
    return {
        "sample_size": n,
        "n_effective": n_eff,
        "min_required": min_n,
        "sufficient": n_eff >= min_n,
        "can_compute_ci95": n_eff >= 2,
        "can_compute_effect_size": n_eff >= 3,
        "pseudoreplication_warning": n_eff < n,
    }
