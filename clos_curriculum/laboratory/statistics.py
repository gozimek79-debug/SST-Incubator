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


# --- SPRINT_v0.10.1.md P1/P3: Welch's t-test + Benjamini-Hochberg FDR ---
# Dodane ADDYTYWNIE (zero zmiany istniejacych funkcji powyzej) dla korekty na
# wielokrotne porownania w walidacji populacyjnej (publications/
# preregistration_v0_10_1_population.json, sekcja metrology.
# multiple_comparisons_correction). Zero zaleznosci zewnetrznych (brak scipy w
# requirements.txt) - regularyzowana niezupelna funkcja beta liczona ulamkiem
# lancuchowym (Numerical Recipes, standardowy algorytm), nie przyblizenie.

def _betacf(a: float, b: float, x: float) -> float:
    """Ulamek lancuchowy dla niezupelnej funkcji beta (Numerical Recipes 6.4)."""
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_bt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    bt = math.exp(log_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def _student_t_two_tailed_p(t: float, df: float) -> float:
    """P(|T| >= |t|) dla Studenta z df stopniami swobody, dwustronne."""
    if df <= 0:
        return 1.0
    x = df / (df + t * t)
    prob_one_side = _regularized_incomplete_beta(df / 2.0, 0.5, x)
    return max(0.0, min(1.0, prob_one_side))


def welch_t_test(group_a: List[float], group_b: List[float]) -> Dict[str, Any]:
    """Welch's t-test (nie zaklada rownych wariancji) - zwraca p-value dwustronne.

    Uzywane WYLACZNIE do korekty wielokrotnych porownan w walidacji
    populacyjnej (nie do PASS/FAIL pojedynczej lekcji - tam effect size/CI95
    pozostaja glowna miara, zgodnie z reszta tego modulu).
    """
    n_a, n_b = len(group_a), len(group_b)
    if n_a < 2 or n_b < 2:
        return {"t": None, "df": None, "p_value": None, "computable": False,
                "reason": "n<2 w co najmniej jednej grupie"}
    mean_a = sum(group_a) / n_a
    mean_b = sum(group_b) / n_b
    var_a = sum((v - mean_a) ** 2 for v in group_a) / (n_a - 1)
    var_b = sum((v - mean_b) ** 2 for v in group_b) / (n_b - 1)
    se_a, se_b = var_a / n_a, var_b / n_b
    denom = se_a + se_b
    if denom < 1e-300:
        return {"t": None, "df": None, "p_value": None, "computable": False,
                "reason": "obie grupy zerowa wariancja - t niezdefiniowany (patrz glass_delta/deterministic)"}
    t = (mean_a - mean_b) / math.sqrt(denom)
    df = denom ** 2 / ((se_a ** 2) / (n_a - 1) + (se_b ** 2) / (n_b - 1))
    p_value = _student_t_two_tailed_p(t, df)
    return {"t": round(t, 6), "df": round(df, 4), "p_value": round(p_value, 8), "computable": True}


def benjamini_hochberg(p_values: List[float], q: float = 0.05) -> List[bool]:
    """Korekta Benjamini-Hochberg FDR. Zwraca liste bool (ta sama kolejnosc co
    wejscie): True = istotne PO korekcie na wielokrotne porownania.

    Procedura: posortuj p rosnaco: p_(1)<=...<=p_(m). Znajdz najwieksze k takie,
    ze p_(k) <= (k/m)*q. Odrzuc H0 (uznaj za istotne) dla wszystkich p_(1..k).
    """
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(range(m), key=lambda i: p_values[i])
    threshold_k = -1
    for rank, idx in enumerate(indexed, start=1):
        if p_values[idx] <= (rank / m) * q:
            threshold_k = rank
    significant = [False] * m
    for rank, idx in enumerate(indexed, start=1):
        if rank <= threshold_k:
            significant[idx] = True
    return significant
