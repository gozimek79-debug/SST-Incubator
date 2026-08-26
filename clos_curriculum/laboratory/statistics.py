"""Laboratory Statistics – CI95, Effect Size, Sample Size validation.

v0.7.2 – Scientific integrity:
- compute_ci95 flaguje przypadki deterministyczne/kontrolne (ci95_valid=False)
  i liczbę EFEKTYWNIE niezależnych obserwacji (n_effective), by nie mylić
  powtórzeń identycznego runu ze statystyczną próbą (pseudoreplikacja).
- glass_delta: właściwy effect size przy porównaniu z deterministyczną kontrolą.
"""

import math
from typing import List, Dict, Any, Optional, Tuple


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


# --- SPRINT_v0.11.0.md P0: Analiza mocy statystycznej (BRAMKA) ---
# Dodane ADDYTYWNIE (zero zmiany istniejacych funkcji powyzej). Powod: brak
# wykrytego efektu (Working Memory, v0.10.1 P3) zostal zinterpretowany jako
# "metryka nie dyskryminuje" bez znajomosci mocy testu - to nadinterpretacja
# wyniku negatywnego (zasada nadrzedna 3, SPRINT_v0.11.0.md). Zero zaleznosci
# zewnetrznych (brak scipy) - dystrybuanta t niecentralnego liczona przez
# calkowanie numeryczne (metoda Simpsona) po definicji T=(Z+ncp)/sqrt(V/df),
# Z~N(0,1), V~chi2_df niezalezne - standardowa, podrecznikowa definicja, nie
# przyblizenie ad-hoc. Zweryfikowane w tests/test_power_analysis.py wprost
# przeciwko klasycznym tablicom Cohena (1988): n=64,d=0.5,alpha=.05->moc~0.80;
# n=26,d=0.8->moc~0.80; n=393,d=0.2->moc~0.80.

def _chi2_pdf(v: float, df: float) -> float:
    """Gestosc chi-kwadrat z df stopniami swobody, przez logarytm (stabilne
    numerycznie dla duzych df)."""
    if v <= 0:
        return 0.0
    log_pdf = (df / 2 - 1) * math.log(v) - v / 2 - (df / 2) * math.log(2) - math.lgamma(df / 2)
    return math.exp(log_pdf)


def _std_normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _noncentral_t_cdf(t: float, df: float, ncp: float, n_steps: int = 4000) -> float:
    """P(T<=t) dla T ~ t niecentralny (df stopni swobody, parametr
    niecentralnosci ncp). Calkowanie Simpsona po V~chi2_df w definicji
    T=(Z+ncp)/sqrt(V/df) - nie przyblizenie, dokladna definicja rozkladu,
    z bledem wylacznie z dyskretyzacji calki (n_steps=4000 daje ~4 miejsca
    po przecinku dokladnosci, zweryfikowane przeciwko tablicom Cohena)."""
    v_max = df + 12 * math.sqrt(2 * df) + 50

    def integrand(v: float) -> float:
        if v <= 0:
            return 0.0
        z_thresh = t * math.sqrt(v / df) - ncp
        return _std_normal_cdf(z_thresh) * _chi2_pdf(v, df)

    h = v_max / n_steps
    total = integrand(1e-9) + integrand(v_max)
    for i in range(1, n_steps):
        v = i * h
        coeff = 4 if i % 2 == 1 else 2
        total += coeff * integrand(v)
    return total * h / 3


def _t_critical_value(df: float, alpha: float = 0.05) -> float:
    """Wartosc krytyczna t (dwustronna) dla danego df i alpha, przez
    bisekcje na _student_t_two_tailed_p (juz zwalidowanej funkcji)."""
    lo, hi = 0.0, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2
        p = _student_t_two_tailed_p(mid, df)
        if p > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def power_two_sample_t_test(d: float, n: int, alpha: float = 0.05) -> float:
    """Moc dwupróbkowego testu t (dwustronnego) do wykrycia efektu d przy n
    obserwacji NA GRUPĘ (n1=n2=n, standardowe zalozenie parametryzacji Cohen's
    d - rownej wariancji obu grup; realna analiza w tym projekcie uzywa
    Welch's t-test, ale d samo w sobie jest zdefiniowane przy zalozeniu rownej
    wariancji, wiec analiza mocy dziedziczy to samo zalozenie - standardowa
    praktyka, patrz G*Power/pakiet R `pwr`).

    df = 2n-2, parametr niecentralnosci ncp = d*sqrt(n/2).
    """
    if n < 2:
        return 0.0
    df = 2 * n - 2
    ncp = d * math.sqrt(n / 2)
    tcrit = _t_critical_value(df, alpha)
    p_upper = 1 - _noncentral_t_cdf(tcrit, df, ncp)
    p_lower = _noncentral_t_cdf(-tcrit, df, ncp)
    return max(0.0, min(1.0, p_upper + p_lower))


def minimum_detectable_effect(n: int, alpha: float = 0.05, target_power: float = 0.8) -> float:
    """Najmniejszy Cohen's d wykrywalny przy n/grupe, alpha, przy zadanej mocy
    (domyslnie 0.8) - bisekcja na power_two_sample_t_test (monotoniczna w d
    dla d>0)."""
    lo, hi = 1e-4, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        p = power_two_sample_t_test(mid, n, alpha)
        if p < target_power:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# --- SPRINT_v0.11.0.md P0 (rozszerzenie po audycie): moc ANOVA (Design C) ---
# Dodane ADDYTYWNIE. Powod: audytor zmierzyl OBSERWOWANY Cohen's f per metryka z
# danych v0.10.1 P3 (zamiast zakladac konwencjonalny f), pokazujac ze Working
# Memory ma f_obs~0.265 (efekt sredni), niewykrywalny przy n=10 (moc=0.185), ale
# rozstrzygajacy przy n=30 (moc=0.952). Wymaga dystrybuanty F niecentralnego -
# liczonej WYLACZNIE przez juz zwalidowana _regularized_incomplete_beta (ten sam
# kod co Welch's t-test/power_two_sample_t_test), przez tozsamosc:
#   P(F_df1,df2 <= f) = I_x(df1/2, df2/2), x = df1*f/(df1*f+df2)  [F centralny]
#   P(F'_df1,df2(ncp) <= f) = SUM_j Pois(j; ncp/2) * I_x(df1/2+j, df2/2)  [niecentralny]
# Zero incomplete gamma / chi2 potrzebne osobno. Zwalidowane w
# tests/test_power_analysis.py: dla k=2 grup, power_anova(f=d/2, k=2, n) MUSI
# byc identyczne (do 1e-4) z juz zwalidowanym power_two_sample_t_test(d, n) -
# F z 1 stopniem swobody licznika = t^2 - relacja podrecznikowa, nie zbieg
# okolicznosci.

def _poisson_pmf(j: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if j == 0 else 0.0
    return math.exp(-lam + j * math.log(lam) - math.lgamma(j + 1))


def _central_f_cdf(f: float, df1: float, df2: float) -> float:
    if f <= 0:
        return 0.0
    x = df1 * f / (df1 * f + df2)
    return _regularized_incomplete_beta(df1 / 2, df2 / 2, x)


def _noncentral_f_cdf(f: float, df1: float, df2: float, ncp: float, max_terms: int = 500) -> float:
    if f <= 0:
        return 0.0
    x = df1 * f / (df1 * f + df2)
    lam = ncp / 2
    total = 0.0
    for j in range(max_terms):
        w = _poisson_pmf(j, lam)
        if w < 1e-14 and j > lam:
            break
        total += w * _regularized_incomplete_beta(df1 / 2 + j, df2 / 2, x)
    return total


def _f_critical_value(df1: float, df2: float, alpha: float = 0.05) -> float:
    """Wartosc krytyczna F (jednostronna - test ANOVA odrzuca H0 tylko dla
    DUZYCH F), przez bisekcje na _central_f_cdf."""
    lo, hi = 0.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        p_upper = 1 - _central_f_cdf(mid, df1, df2)
        if p_upper > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def power_anova(f_effect: float, k: int, n: int, alpha: float = 0.05) -> float:
    """Moc jednoczynnikowej ANOVA (omnibus, Design C): k grup (genomow),
    n obserwacji/grupe (zbalansowane), Cohen's f. df1=k-1, df2=k*(n-1),
    ncp=f^2*k*n (Cohen 1988)."""
    if n < 2 or k < 2:
        return 0.0
    df1 = k - 1
    df2 = k * (n - 1)
    ncp = f_effect ** 2 * k * n
    fcrit = _f_critical_value(df1, df2, alpha)
    return max(0.0, min(1.0, 1 - _noncentral_f_cdf(fcrit, df1, df2, ncp)))


def cohens_f_anova(means: List[float], stds: List[float], ns: List[int]) -> Dict[str, Any]:
    """Cohen's f dla jednoczynnikowej ANOVA, z per-grupowych (per-genom) mean/
    std/n - NIE z surowych obserwacji (te czesto juz nie sa przechowywane,
    tylko zagregowane statystyki - patrz reports/population/*.json).

    Konwencja: SD miedzy-grupowe dzielone przez k (populacyjna, k grup
    TRAKTOWANE JAKO KOMPLETNY, USTALONY zestaw do tego konkretnego porownania -
    standardowa konwencja Cohena dla ANOVA o efektach stalych), SD wewnatrz
    jako spula (pooled) z per-grupowych wariancji wazonych stopniami swobody.
    """
    k = len(means)
    if k < 2:
        return {"f": 0.0, "computable": False, "reason": "k<2 grup"}
    grand_mean = sum(m * n for m, n in zip(means, ns)) / sum(ns)
    ss_between_pop = sum((m - grand_mean) ** 2 for m in means) / k
    sd_between = math.sqrt(ss_between_pop)

    df_within = sum(n - 1 for n in ns)
    if df_within <= 0:
        return {"f": None, "computable": False, "reason": "brak stopni swobody wewnatrz-grupowych (wszystkie n<=1)"}
    ss_within = sum((n - 1) * s ** 2 for n, s in zip(ns, stds))
    sd_within = math.sqrt(ss_within / df_within)

    if sd_within < 1e-12:
        return {"f": None, "computable": False, "reason": "zerowa wariancja wewnatrz-grupowa (wszystkie grupy deterministyczne)"}

    return {"f": round(sd_between / sd_within, 6), "computable": True,
            "sd_between": round(sd_between, 6), "sd_within": round(sd_within, 6),
            "k": k, "df_within": df_within}


# --- SPRINT_v0.11.0.md P0 (druga runda): matematyka sekwencyjna (Wariant B) ---
# Dodane ADDYTYWNIE. Uzasadnienie: audytor policzyl koszt/korzysc designu
# sekwencyjnego (interim n=30 -> ewentualne rozszerzenie n=185) - dwa spojrzenia
# na te same (nachodzace) dane sa SKORELOWANE (rho=sqrt(n1/n2)), wiec naiwne
# powtorzenie tego samego progu istotnosci na obu spojrzeniach INFLATUJE blad
# I rodzaju. Wymaga dwuwymiarowego rozkladu normalnego - liczonego przez
# calkowanie numeryczne (Simpson 2D) gestosci dwuwymiarowej normalnej, zero
# scipy. Zwalidowane na przypadkach brzegowych (rho=0: P(oba w granicach) =
# P(pojedynczy)^2 dokladnie; rho=1: P(oba)=P(pojedynczy) dokladnie) oraz
# przeciwko niezaleznemu przeliczeniu audytora (rho=0.4027 dla n1=30,n2=185;
# inflacja bledu I rodzaju bez korekty = 1.9675x, alpha 0.00238->0.004685 -
# zgodnosc do 4 cyfry, patrz tests/test_sequential_analysis.py).

def _bivariate_normal_pdf(z1: float, z2: float, rho: float) -> float:
    denom = 2 * math.pi * math.sqrt(1 - rho ** 2)
    expo = -(z1 ** 2 - 2 * rho * z1 * z2 + z2 ** 2) / (2 * (1 - rho ** 2))
    return math.exp(expo) / denom


def _bivariate_normal_cdf(h: float, k: float, rho: float, n_steps: int = 150, lim: float = 6.0) -> float:
    """P(Z1<=h, Z2<=k) dla standardowego dwuwymiarowego rozkladu normalnego
    z korelacja rho - calkowanie Simpsona 2D. n_steps=150/lim=6.0 dobrane dla
    dokladnosci ~1e-4, wystarczajacej do analizy mocy/inflacji (nie do
    formalnych granic regulacyjnych)."""
    if rho >= 0.999999:
        return _std_normal_cdf(min(h, k))
    if rho <= -0.999999:
        return max(0.0, _std_normal_cdf(h) - _std_normal_cdf(-k))
    if h <= -lim or k <= -lim:
        return 0.0
    hi1, hi2 = min(h, lim), min(k, lim)
    lo1 = lo2 = -lim

    def weights(n):
        w = [1.0] * (n + 1)
        for i in range(1, n):
            w[i] = 4.0 if i % 2 == 1 else 2.0
        return w

    h1s, h2s = (hi1 - lo1) / n_steps, (hi2 - lo2) / n_steps
    w = weights(n_steps)
    total = 0.0
    for i in range(n_steps + 1):
        z1 = lo1 + i * h1s
        row = 0.0
        for j in range(n_steps + 1):
            z2 = lo2 + j * h2s
            row += w[j] * _bivariate_normal_pdf(z1, z2, rho)
        row *= h2s / 3
        total += w[i] * row
    total *= h1s / 3
    return max(0.0, min(1.0, total))


def sequential_correlation(n_interim: int, n_final: int) -> float:
    """rho miedzy statystykami interim i finalnego spojrzenia w grupowo-
    sekwencyjnym designie z nachodzacymi probkami (pierwsze n_interim
    obserwacji sa wspolne dla obu spojrzen) - standardowy wynik teorii
    projektow sekwencyjnych: rho = sqrt(n_interim/n_final)."""
    return math.sqrt(n_interim / n_final)


def naive_two_look_type1_error(alpha_per_look: float, rho: float) -> Dict[str, Any]:
    """Faktyczny blad I rodzaju przy DWOCH spojrzeniach na skorelowane dane,
    KAZDE testowane niezaleznie na poziomie alpha_per_look (BEZ korekty na
    sekwencyjnosc) - to jest dokladnie bledna praktyka, ktorej ten mechanizm
    ma zapobiec wykrywajac. Zwraca alpha faktyczne i wspolczynnik inflacji."""
    c = _t_critical_value_normal_approx(alpha_per_look)
    p_both_within = (_bivariate_normal_cdf(c, c, rho) - _bivariate_normal_cdf(-c, c, rho)
                     - _bivariate_normal_cdf(c, -c, rho) + _bivariate_normal_cdf(-c, -c, rho))
    alpha_actual = 1 - p_both_within
    return {"alpha_per_look": alpha_per_look, "alpha_actual": round(alpha_actual, 6),
            "inflation_factor": round(alpha_actual / alpha_per_look, 4), "rho": round(rho, 4)}


def _t_critical_value_normal_approx(alpha: float) -> float:
    """Wartosc krytyczna z rozkladu normalnego (przyblizenie duzego df) -
    uzywana wylacznie w kontekscie sekwencyjnym (Z-statystyki), nie myl z
    _t_critical_value (dokladna, dla skonczonego df testu t)."""
    lo, hi = 0.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        p_upper = 1 - _std_normal_cdf(mid)
        if 2 * p_upper > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def pocock_boundary(target_alpha: float, rho: float) -> float:
    """Granica Pococka: STALA wartosc krytyczna c (ta sama na obu spojrzeniach)
    taka, ze P(|Z1|>c LUB |Z2|>c) = target_alpha, uwzgledniajac korelacje rho
    miedzy spojrzeniami. Bisekcja na _bivariate_normal_cdf."""
    lo, hi = 0.0, 8.0
    for _ in range(60):
        mid = (lo + hi) / 2
        p_both_within = (_bivariate_normal_cdf(mid, mid, rho) - _bivariate_normal_cdf(-mid, mid, rho)
                         - _bivariate_normal_cdf(mid, -mid, rho) + _bivariate_normal_cdf(-mid, -mid, rho))
        alpha_actual = 1 - p_both_within
        if alpha_actual > target_alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# --- SPRINT_v0.11.0.md, Red Team (2026-07-20): Kruskal-Wallis ---
# Test parami (welch_t_test + benjamini_hochberg) zaklada, ze efekt jest
# MONOTONICZNY miedzy grupami parami - slaby, NIEMONOTONICZNY efekt (np.
# genomy roznia sie w sposob, ktory nie sprowadza sie do "para A > para B"
# konsekwentnie) moze dac 0 istotnych par przy tescie parowym, mimo
# realnego efektu wykrywalnego testem OMNIBUSOWYM na rangach (Kruskal-Wallis).
# To NIE jest sprzecznosc - to dwa rozne pytania (ten sam wzorzec co "ROBUST
# != dyskryminuje", VALIDITY_REPORT.md). Zero scipy - dystrybuanta chi-kwadrat
# liczona calkowaniem numerycznym (Simpson) po _chi2_pdf (juz istniejacej,
# zwalidowanej wyzej). Zwalidowane wprost: 3 grupy [1,2,3]/[4,5,6]/[7,8,9]
# (rangi 1..9 bez remisow) daje H=7.2, df=2 - dla df=2 chi-kwadrat ma
# zamkniety wzor CDF=1-exp(-x/2), p=exp(-3.6)=0.027323722... zgodne co do
# 12 miejsca po przecinku (patrz tests/test_kruskal_wallis.py).

def _chi2_cdf(x: float, df: float, n_steps: int = 2000) -> float:
    """P(X<=x) dla X~chi2_df, calkowanie Simpsona po _chi2_pdf od ~0 do x.
    UWAGA: dla bardzo duzych x (CDF bliskie 1.0) traci precyzje przez
    katastroficzne skracanie w 1-CDF - do p-wartosci w gornym ogonie uzywac
    chi2_survival() ponizej, NIE 1-_chi2_cdf()."""
    if x <= 0:
        return 0.0
    h = x / n_steps
    total = _chi2_pdf(1e-9, df) + _chi2_pdf(x, df)
    for i in range(1, n_steps):
        v = i * h
        total += (4 if i % 2 == 1 else 2) * _chi2_pdf(v, df)
    return (h / 3) * total


def _log_upper_incomplete_gamma_q(a: float, x: float, max_iter: int = 200, eps: float = 1e-14) -> float:
    """log(Q(a,x)), Q = regularyzowana GORNA niepelna funkcja gamma, przez
    ulamek lancuchowy Lentza (Numerical Recipes 6.2) - zbiega szybko i
    stabilnie dokladnie w rezimie x>a (nasz przypadek: gorny ogon chi-kwadrat
    dla duzego H). Liczone w log-przestrzeni, zeby uniknac underflow do 0.0
    kiedy prawdziwe Q jest astronomicznie male (np. 1e-700)."""
    tiny = 1e-300
    b = x + 1 - a
    if abs(b) < tiny:
        b = tiny
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, max_iter):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < eps:
            break
    return -x + a * math.log(x) - math.lgamma(a) + math.log(h)


def chi2_survival(x: float, df: float) -> float:
    """P(X>x) dla X~chi2_df - funkcja przezycia liczona BEZPOSREDNIO (gorna
    niepelna gamma), NIE jako 1-_chi2_cdf(x,df) (ktore traci precyzje/daje
    ujemne wyniki przez katastroficzne skracanie, gdy prawdziwe p jest
    ekstremalnie male - dokladnie przypadek duzych H w kruskal_wallis()
    ponizej). Zwalidowane wprost przeciwko zamknietej formie dla df=2
    (survival=exp(-x/2)) w tests/test_kruskal_wallis.py."""
    if x <= 0:
        return 1.0
    log_q = _log_upper_incomplete_gamma_q(df / 2, x / 2)
    return math.exp(log_q) if log_q > -700 else 0.0


def chi2_survival_log10(x: float, df: float) -> float:
    """log10(P(X>x)) - dla p-wartosci zbyt ekstremalnych, zeby exp() nie
    dal underflow do 0.0 (np. p~1e-700). Uzywane do RAPORTOWANIA, gdy
    chi2_survival() zwrocilaby 0.0 (informatywne 'p<1e-300', nie cicha zera)."""
    log_q = _log_upper_incomplete_gamma_q(df / 2, x / 2)
    return log_q / math.log(10)


def kruskal_wallis(groups: List[List[float]]) -> Dict[str, Any]:
    """Test Kruskala-Wallisa (nieparametryczny, oparty na rangach, NIE
    zaklada homoskedastycznosci ani normalnosci) - z korekta na remisy
    (tie correction, standardowa formula podrecznikowa). Zwraca H (po
    korekcie), df, p_value, computable (False gdy <2 grupy z danymi lub
    N<3)."""
    groups = [g for g in groups if g]
    if len(groups) < 2:
        return {"H": None, "df": None, "p_value": None, "computable": False,
                "reason": "mniej niz 2 grupy z danymi"}

    all_vals = [(v, gi) for gi, g in enumerate(groups) for v in g]
    n_total = len(all_vals)
    if n_total < 3:
        return {"H": None, "df": None, "p_value": None, "computable": False,
                "reason": "N<3"}

    all_vals.sort(key=lambda x: x[0])
    ranks = [0.0] * n_total
    tie_group_sizes: List[int] = []
    i = 0
    while i < n_total:
        j = i
        while j + 1 < n_total and all_vals[j + 1][0] == all_vals[i][0]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        if j > i:
            tie_group_sizes.append(j - i + 1)
        i = j + 1

    rank_sums = [0.0] * len(groups)
    for idx, (_, gi) in enumerate(all_vals):
        rank_sums[gi] += ranks[idx]

    h_raw = (12 / (n_total * (n_total + 1))) * sum(
        rs ** 2 / len(groups[gi]) for gi, rs in enumerate(rank_sums)
    ) - 3 * (n_total + 1)

    tie_correction = 1 - sum(t ** 3 - t for t in tie_group_sizes) / (n_total ** 3 - n_total)
    h_corrected = h_raw / tie_correction if tie_correction > 0 else h_raw

    df = len(groups) - 1
    p_value = chi2_survival(h_corrected, df)
    result = {"H": round(h_corrected, 6), "df": df, "p_value": p_value, "computable": True,
              "n_groups": len(groups), "n_total": n_total, "tie_correction": round(tie_correction, 6)}
    if p_value == 0.0:
        # p prawdziwie astronomicznie male (underflow ponizej ~1e-308) -
        # raportuj log10(p), zeby nie zgubic "jak bardzo istotne", nie
        # cichy zera (zasada nadrzedna 1).
        result["p_value_log10"] = round(chi2_survival_log10(h_corrected, df), 2)
    return result


# --- PC-001 B3 (2026-07-28): testy dla 9-warunkowej reguly decyzyjnej ---
# Dodane ADDYTYWNIE. DECYZJA CTO: scipy NIE wchodzi do kodu produkcyjnego -
# zyje POZA repo (nie jest czescia CRITICAL_FILES_PC_001), wiec podbicie
# jego wersji zmienialoby wyniki BEZ zmiany PC_001_BASELINE, unicestwiajac
# gwarancje "te liczby powstaly z tego kodu analizy" (powod, dla ktorego
# PC_001_BASELINE liczony jest jako OSTATNI krok, po B3/B4). scipy jest
# ZALEZNOSCIA TESTOWA WYLACZNIE (patrz tests/test_pc_001_statistics.py) -
# requirements.txt bez zmian, ten sam wzorzec co reszta tego pliku
# (welch_t_test/kruskal_wallis/power_*: zero zaleznosci zewnetrznych).
#
# WZORZEC exact-vs-approx (spojny w calym bloku): male n bez remisow -> ROZKLAD
# DOKLADNY (DP po permutacjach/podzbiorach) - przyblizenie normalne jest zbyt
# niedokladne dla malych n (K3b ma ~7 wstrzasow na przebieg). Remisy obecne
# lub n zbyt duze -> przyblizenie normalne z korekta na remisy i korekta
# ciaglosci (ten sam poziom rygoru co juz istniejace w tym pliku funkcje
# oparte na _noncentral_t_cdf/_chi2_cdf).

# --- Agregacja blokowa (B4C-05 v8): jednostka analizy = 1 wartosc per seed ---
# ZNALEZISKO CTO: identyczna agregacja (23 genomy -> 1 srednia per blok
# seedowy) istniala DOTAD wylacznie jako execution_package_v0_11/runners/
# power_analysis_b4b.py::_block_means - plik POZA CRITICAL_FILES_PC_001
# (wykluczony formalnie, B4B-03 pkt 5: jednorazowy symulator analizy mocy,
# nie kod stosowany przy kazdym przebiegu). Funkcja, ktora ustala JEDNOSTKE
# ANALIZY calej rodziny testow (kazda komorka BH-FDR operuje na "1 wartosc
# per blok seedowy", nie na 23*N surowych wartosciach - patrz publications/
# pc_001_bh_family.json), lezala poza zasiegiem Hard-Halt: zamiana sum/len
# na mediane zmienilaby wejscie KAZDEGO testu w rodzinie bez zmiany
# PC_001_BASELINE. Ta sama klasa bledu co lista 51/52 (B5-00) i K4 (B4C-05
# v3) - tym razem we WLASNEJ instrukcji CTO ("uzyj _block_means").
#
# WARIANT C (ten sam wzorzec co trzy runnery pilota, B4C-01): power_analysis_
# b4b.py NIE jest edytowany - wyprodukowal juz zacommitowany artefakt B4b,
# edycja (nawet czysto importowa) zerwalaby prowieniencje. Ta funkcja jest
# NIEZALEZNA, KANONICZNA kopia w pliku nalezacym do rejestru - test spojnosci
# (tests/test_pc_001_statistics.py::TestBlockMeansConsistency) dowodzi
# rownowaznosci na danych losowych, nie konsolidacja.
def block_means(columns: List[List[float]]) -> List[float]:
    """Srednia w obrebie kazdej kolumny (bloku seeda) po wszystkich genomach
    w bloku. KRYTYCZNE: zaden test w rodzinie BH-FDR nie dostaje surowych
    23*N wartosci per-genom wprost - to bylaby pseudo-replikacja (23
    skorelowane obserwacje w bloku wygladajace dla testu jak 23 niezalezne).
    Test dostaje N wartosci - po jednej na blok/seed, ktora JEST jednostka
    analizy (patrz power_analysis_b4b.py::_block_means, docstring, ktory
    ustalil ten kontrakt podczas analizy mocy B4b)."""
    return [sum(col) / len(col) for col in columns]


# --- Nachylenie liniowe (B4C-2 (03): Warunek A/K1-A/K4-A/K5-A - beta trendu) ---


class DegenerateInputError(Exception):
    """Podniesiony przez linear_slope(), gdy var(t) == 0 (wszystkie ticki
    identyczne) - nachylenie jest matematycznie niezdefiniowane (dzielenie
    przez zero). WYJATEK, nigdy NaN ani None przepuszczone dalej do testu
    statystycznego (B4C-2 (03), decyzja CTO pkt 4)."""


def linear_slope(ticks: List[float], values: List[float]) -> float:
    """beta = cov(t, y) / var(t) - zwykle OLS, WYLACZNIE nachylenie (B4C-2
    (03), decyzja CTO). Celowo WEZSZY kontrakt niz pelna regresja: bez
    interceptu, R^2, p-value - Warunek A (i K1-A/K4-A/K5-A, ta sama funkcja)
    potrzebuje wylacznie nachylenia, nic wiecej. Nazwa 'linear_slope', NIE
    'linear_regression' - mniej powierzchni do niezamierzonej interpretacji.

    FUNKCJA MATEMATYCZNA OGOLNA - bez wiedzy o PC-001, bez wymogu kompletnej/
    identycznej siatki tickow. Ten wymog (semantyka protokolu: komorka
    nieobliczalna przy niepelnej siatce -> INCONCLUSIVE) mieszka w warstwie
    protokolu (w2_endpoint/evaluator), NIE tutaj - statistics.py jest
    biblioteka ogolna, tak jak reszta funkcji w tym pliku.

    Jedyny warunek, jaki ta funkcja egzekwuje: var(t) != 0. Zdegenerowane t
    (wszystkie wartosci identyczne) -> DegenerateInputError, nigdy NaN.
    Wymaga len(ticks) == len(values) >= 2 (dwa punkty to minimum, by
    nachylenie mialo sens; przy n<2 var(t) i tak wyszlaby z jednego punktu
    lub bledu dlugosci - sprawdzone jawnie dla czytelnego komunikatu)."""
    if len(ticks) != len(values):
        raise ValueError(f"len(ticks)={len(ticks)} != len(values)={len(values)}")
    n = len(ticks)
    if n < 2:
        raise DegenerateInputError(f"n={n} < 2 - nachylenie wymaga co najmniej dwoch punktow")
    mean_t = sum(ticks) / n
    mean_y = sum(values) / n
    cov_ty = sum((t - mean_t) * (y - mean_y) for t, y in zip(ticks, values)) / n
    var_t = sum((t - mean_t) ** 2 for t in ticks) / n
    if var_t == 0:
        raise DegenerateInputError(
            f"var(t) == 0 (wszystkie {n} tickow identyczne, t={ticks[0]!r}) - "
            "nachylenie niezdefiniowane (dzielenie przez zero)"
        )
    return cov_ty / var_t


def _rank_with_ties(values: List[float]) -> Tuple[List[float], List[int]]:
    """Rangi (srednia dla remisow) + rozmiary grup remisowych.

    NIEZALEZNA kopia logiki rankingu z kruskal_wallis() powyzej - CELOWO nie
    refaktoryzowana do wspolnego helpera uzywanego przez obie funkcje: kruskal_
    wallis jest juz przetestowana i uzywana w produkcji (v0.11), a wydzielenie
    wspolnego helpera wymagaloby zmiany JEJ kodu, ryzykujac regresje dla
    korzysci ograniczonej do ~15 linii duplikacji. Ten sam wzorzec ostroznosci
    co "nie ruszamy Core" w innych czesciach tego projektu."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    tie_group_sizes: List[int] = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        if j > i:
            tie_group_sizes.append(j - i + 1)
        i = j + 1
    return ranks, tie_group_sizes


# --- Wilcoxon signed-rank (warunek B: W_early vs W_late per seed/genom) ---

def _wilcoxon_null_distribution(n: int) -> Tuple[List[int], int]:
    """DP: counts[s] = liczba kombinacji znakow (z 2^n) dajacych sume rang
    dodatnich = s, przy BRAKU remisow (rangi = calkowite 1..n). Wydzielone
    z _wilcoxon_exact_p (B4C-05 v7, tryb jednostronny) - JEDNA implementacja
    DP, uzywana przez dwustronny i jednostronny wariant, zeby nie duplikowac
    logiki rozkladu zerowego."""
    max_sum = n * (n + 1) // 2
    counts = [0] * (max_sum + 1)
    counts[0] = 1
    running_total = 0
    for r in range(1, n + 1):
        running_total += r
        for s in range(min(running_total, max_sum), r - 1, -1):
            counts[s] += counts[s - r]
    return counts, 2 ** n


def _wilcoxon_exact_p(w_plus: float, n: int, alternative: str = "two-sided") -> float:
    """p-value dokladne (rozklad zerowy W+ przy braku remisow).

    'two-sided' (domyslne, ZACHOWANIE BEZ ZMIAN wzgledem wersji sprzed B4C-05
    v7): 2*min(p_le, p_ge). 'greater' (H1: mediana roznic > 0): p_ge = P(W+ >=
    obserwowane). 'less' (H1: mediana roznic < 0): p_le = P(W+ <= obserwowane).
    Potwierdzone empirycznie przeciw scipy.stats.wilcoxon(alternative=...) -
    patrz tests/test_pc_001_statistics.py."""
    counts, total_perms = _wilcoxon_null_distribution(n)
    w_plus_int = int(round(w_plus))
    p_le = sum(counts[:w_plus_int + 1]) / total_perms
    p_ge = sum(counts[w_plus_int:]) / total_perms
    if alternative == "greater":
        return min(1.0, p_ge)
    if alternative == "less":
        return min(1.0, p_le)
    return min(1.0, 2 * min(p_le, p_ge))


def wilcoxon_signed_rank(pairs: List[Tuple[float, float]], exact_max_n: int = 25,
                          alternative: str = "two-sided") -> Dict[str, Any]:
    """Test Wilcoxona dla par (warunek B, Aneks 1: W_early vs W_late per
    seed/genom). Rozniece zerowe (pary identyczne) ODRZUCANE przed rankingiem
    - konwencja 'wilcox' (standardowa, domyslna w scipy.stats.wilcoxon).

    Rozklad DOKLADNY (DP) gdy n<=exact_max_n i brak remisow; inaczej
    przyblizenie normalne z korekta na remisy i korekta ciaglosci.

    alternative (B4C-05 v7, dodane PRZED B5 - domyslna wartosc 'two-sided'
    zachowuje BIT W BIT poprzednie zachowanie dla kazdego istniejacego
    wywolujacego, patrz tests/test_pc_001_statistics.py::TestWilcoxonAlternativeRegression):
      'two-sided' (domyslne) - statistic=min(W+,W-), p dwustronne.
      'greater'  - H1: mediana roznic (a-b) > 0. Uzycie: K3a-warunek1
                   (publications/pc_001_bh_family.json) - kierunkowosc wynika
                   z PREREJESTROWANEJ hipotezy ("po wstrzasie PE rosnie"),
                   NIE z tego, ze jednostronny test daje mniejsze p.
      'less'     - H1: mediana roznic (a-b) < 0.
    Dla 'greater'/'less' statistic=W+ (konwencja scipy - zweryfikowane
    empirycznie: scipy.stats.wilcoxon(..., alternative='greater'/'less')
    zwraca to samo 'statistic', rozne 'pvalue' - inaczej niz przy 'two-sided',
    gdzie statistic=min(W+,W-)).
    """
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError(f"alternative musi byc 'two-sided', 'greater' lub 'less', dostano {alternative!r}")

    diffs = [a - b for a, b in pairs]
    nonzero = [d for d in diffs if d != 0]
    n_zero = len(diffs) - len(nonzero)
    n = len(nonzero)
    if n == 0:
        return {"statistic": None, "p_value": None, "computable": False,
                "reason": "wszystkie roznice sa zerowe (lub brak par)",
                "n_zero_dropped": n_zero, "n": 0, "alternative": alternative}

    abs_d = [abs(d) for d in nonzero]
    ranks, tie_group_sizes = _rank_with_ties(abs_d)
    w_plus = sum(r for r, d in zip(ranks, nonzero) if d > 0)
    w_minus = sum(r for r, d in zip(ranks, nonzero) if d < 0)
    statistic = w_plus if alternative in ("greater", "less") else min(w_plus, w_minus)
    has_ties = len(tie_group_sizes) > 0

    if n <= exact_max_n and not has_ties:
        p_value = _wilcoxon_exact_p(w_plus, n, alternative)
        method = "exact"
    else:
        mean = n * (n + 1) / 4
        var = n * (n + 1) * (2 * n + 1) / 24 - sum(t ** 3 - t for t in tie_group_sizes) / 48
        if var <= 0:
            return {"statistic": round(statistic, 6), "p_value": None, "computable": False,
                    "reason": "wariancja <=0 (zbyt duzo remisow wzgledem n)",
                    "n_zero_dropped": n_zero, "n": n, "alternative": alternative}
        # BEZ korekty ciaglosci - zweryfikowane wprost przeciwko
        # scipy.stats.wilcoxon(mode='approx'): domyslny tryb scipy NIE
        # stosuje korekty ciaglosci (correction=False domyslnie), w
        # odroznieniu od Manna-Whitneya ponizej (scipy uzywa correction
        # domyslnie TAM). Zgodnosc do 1e-6 wymaga podazania za scipy per
        # test, nie jednolitej wlasnej konwencji - patrz
        # tests/test_pc_001_statistics.py. Jednostronne p (greater/less)
        # NIE walidowane przeciw scipy przy remisach (B4C-05 v7 ZAKAZ:
        # remisy sa oddzielnym regime'em, gdzie scipy method="exact" po
        # cichu ignoruje remisy - patrz docstring TestWilcoxonAlternativeRegression).
        z = (w_plus - mean) / math.sqrt(var)
        if alternative == "greater":
            p_value = max(0.0, min(1.0, 1 - _std_normal_cdf(z)))
        elif alternative == "less":
            p_value = max(0.0, min(1.0, _std_normal_cdf(z)))
        else:
            p_value = max(0.0, min(1.0, 2 * (1 - _std_normal_cdf(abs(z)))))
        method = "normal_approx"

    return {"statistic": round(statistic, 6), "w_plus": round(w_plus, 6),
            "w_minus": round(w_minus, 6), "p_value": round(p_value, 8),
            "computable": True, "n": n, "n_zero_dropped": n_zero,
            "method": method, "has_ties": has_ties, "alternative": alternative}


# --- Kendall tau-b (K3b-1: trend recovery_i przez kolejne wstrzasy) ---

def _inversions_distribution(n: int) -> List[int]:
    """counts[k] = liczba permutacji n elementow z DOKLADNIE k inwersjami
    (liczby Mahoniana), przez mnozenie wielomianow
    prod_{i=1}^{n} (1+x+...+x^{i-1}) - standardowa funkcja tworzaca."""
    counts = [1]
    for i in range(2, n + 1):
        new_counts = [0] * (len(counts) + i - 1)
        for k in range(i):
            for s, c in enumerate(counts):
                new_counts[s + k] += c
        counts = new_counts
    return counts


def _kendall_exact_p(n_discordant: int, n: int) -> float:
    total_perms = math.factorial(n)
    dist = _inversions_distribution(n)
    p_le = sum(dist[:n_discordant + 1]) / total_perms
    p_ge = sum(dist[n_discordant:]) / total_perms
    return min(1.0, 2 * min(p_le, p_ge))


def kendall_tau(x: List[float], y: List[float], exact_max_n: int = 30) -> Dict[str, Any]:
    """Kendall's tau-b (korekta na remisy w OBU zmiennych) - K3b-1: trend
    recovery_i przez kolejne wstrzasy w recurring_shock_world (~7/przebieg).

    Rozklad DOKLADNY (liczby Mahoniana - DP wielomianowe) gdy n<=exact_max_n
    i brak remisow w x ORAZ y; inaczej przyblizenie normalne z pelna korekta
    na remisy (formula Kendall & Gibbons, standardowa - ta sama, ktorej uzywa
    R cor.test(method='kendall')).
    """
    n = len(x)
    if n != len(y):
        raise ValueError("x i y musza miec te sama dlugosc")
    if n < 2:
        return {"tau": None, "p_value": None, "computable": False,
                "reason": "n<2", "n": n}

    n_c = n_d = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            if dx == 0 or dy == 0:
                continue
            if (dx > 0) == (dy > 0):
                n_c += 1
            else:
                n_d += 1

    _, tie_sizes_x = _rank_with_ties(x)
    _, tie_sizes_y = _rank_with_ties(y)
    n0 = n * (n - 1) / 2
    n1 = sum(t * (t - 1) / 2 for t in tie_sizes_x)
    n2 = sum(t * (t - 1) / 2 for t in tie_sizes_y)
    denom = math.sqrt((n0 - n1) * (n0 - n2))
    if denom < 1e-12:
        return {"tau": None, "p_value": None, "computable": False,
                "reason": "mianownik zerowy (wszystkie wartosci remisowe w x lub y)", "n": n}
    tau = (n_c - n_d) / denom

    has_ties = bool(tie_sizes_x or tie_sizes_y)
    if n <= exact_max_n and not has_ties:
        p_value = _kendall_exact_p(n_d, n)
        method = "exact"
    else:
        v0 = n * (n - 1) * (2 * n + 5)
        vt = sum(t * (t - 1) * (2 * t + 5) for t in tie_sizes_x)
        vu = sum(t * (t - 1) * (2 * t + 5) for t in tie_sizes_y)
        v1_x = sum(t * (t - 1) * (t - 2) for t in tie_sizes_x)
        v1_y = sum(t * (t - 1) * (t - 2) for t in tie_sizes_y)
        v2_x = sum(t * (t - 1) for t in tie_sizes_x)
        v2_y = sum(t * (t - 1) for t in tie_sizes_y)
        var_s = (v0 - vt - vu) / 18.0
        if n > 2:
            var_s += (v1_x * v1_y) / (9.0 * n * (n - 1) * (n - 2))
        var_s += (v2_x * v2_y) / (2.0 * n * (n - 1))
        if var_s <= 0:
            return {"tau": round(tau, 6), "p_value": None, "computable": False,
                    "reason": "wariancja <=0 (zbyt duzo remisow wzgledem n)", "n": n}
        s_stat = n_c - n_d
        z = s_stat / math.sqrt(var_s)
        p_value = max(0.0, min(1.0, 2 * (1 - _std_normal_cdf(abs(z)))))
        method = "normal_approx"

    return {"tau": round(tau, 6), "p_value": round(p_value, 8), "computable": True,
            "n": n, "n_concordant": n_c, "n_discordant": n_d,
            "method": method, "has_ties": has_ties}


# --- Spearman rho (K6: korelacja prediction/input) ---

def spearman_rho(x: List[float], y: List[float]) -> Dict[str, Any]:
    """Korelacja Spearmana (Pearson na rangach, srednia ranga dla remisow -
    obsluguje remisy natywnie, bez osobnej formuly). p-value przez
    przyblizenie t-rozkladem (t=rho*sqrt((n-2)/(1-rho^2)), df=n-2) - TA SAMA
    metoda, ktorej scipy.stats.spearmanr uzywa domyslnie (nie tylko dla
    duzych n) - reuzywa juz zwalidowana _student_t_two_tailed_p z tego pliku."""
    n = len(x)
    if n != len(y):
        raise ValueError("x i y musza miec te sama dlugosc")
    if n < 3:
        return {"rho": None, "p_value": None, "computable": False,
                "reason": "n<3 (df=n-2 wymaga n>=3)", "n": n}

    rx, _ = _rank_with_ties(x)
    ry, _ = _rank_with_ties(y)
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    cov = sum((a - mean_rx) * (b - mean_ry) for a, b in zip(rx, ry))
    var_rx = sum((a - mean_rx) ** 2 for a in rx)
    var_ry = sum((b - mean_ry) ** 2 for b in ry)
    denom = math.sqrt(var_rx * var_ry)
    if denom < 1e-12:
        return {"rho": None, "p_value": None, "computable": False,
                "reason": "brak wariancji w rangach x lub y (wszystkie remisy)", "n": n}
    rho = cov / denom
    rho = max(-1.0, min(1.0, rho))

    if abs(rho) >= 1.0 - 1e-12:
        p_value = 0.0
    else:
        t = rho * math.sqrt((n - 2) / (1 - rho ** 2))
        p_value = _student_t_two_tailed_p(t, n - 2)

    return {"rho": round(rho, 6), "p_value": round(p_value, 8), "computable": True, "n": n}


# --- Mann-Whitney U (K4: separacja shock_world vs pure_noise_world) ---

def _subset_sum_with_count_distribution(n_total: int, subset_size: int) -> Dict[int, int]:
    """{suma: liczba podzbiorow} rozmiaru subset_size z {1,...,n_total} -
    DP 0/1 (jak w Wilcoxonie, z dodatkowym wymiarem 'ile elementow wybrano').
    Uzywane do dokladnego rozkladu zerowego Mann-Whitney U (subset_size=n_a,
    n_total=n_a+n_b) - suma rang losowego podzbioru rozmiaru n_a z {1..N}."""
    dp: List[Dict[int, int]] = [dict() for _ in range(subset_size + 1)]
    dp[0][0] = 1
    for r in range(1, n_total + 1):
        for k in range(min(subset_size, r), 0, -1):
            prev = dp[k - 1]
            if not prev:
                continue
            cur = dp[k]
            for s, c in prev.items():
                ns = s + r
                cur[ns] = cur.get(ns, 0) + c
    return dp[subset_size]


def mann_whitney_u(a: List[float], b: List[float], exact_max_product: int = 1000) -> Dict[str, Any]:
    """Test Manna-Whitneya (rank-sum, dwie proby niezalezne) - K4: separacja
    shock_world vs pure_noise_world.

    Rozklad DOKLADNY (DP na sumach podzbiorow rang) gdy n_a*n_b<=
    exact_max_product i brak remisow; inaczej przyblizenie normalne z korekta
    na remisy i korekta ciaglosci.
    """
    n_a, n_b = len(a), len(b)
    if n_a == 0 or n_b == 0:
        return {"statistic": None, "p_value": None, "computable": False,
                "reason": "co najmniej jedna grupa pusta", "n_a": n_a, "n_b": n_b}

    combined = a + b
    ranks, tie_group_sizes = _rank_with_ties(combined)
    r_a = sum(ranks[:n_a])
    u_a = r_a - n_a * (n_a + 1) / 2
    u_b = n_a * n_b - u_a
    # KONWENCJA: statistic = u_a (dla PIERWSZEJ probki, "a") - dokladnie tak,
    # jak scipy.stats.mannwhitneyu zwraca .statistic (U dla pierwszej tablicy
    # argumentu, NIE min(U_a,U_b)) - zweryfikowane wprost w
    # tests/test_pc_001_statistics.py.
    statistic = u_a
    has_ties = len(tie_group_sizes) > 0
    n_total = n_a + n_b

    if n_a * n_b <= exact_max_product and not has_ties:
        dist = _subset_sum_with_count_distribution(n_total, n_a)
        total_subsets = sum(dist.values())
        r_a_int = int(round(r_a))
        p_le = sum(c for s, c in dist.items() if s <= r_a_int) / total_subsets
        p_ge = sum(c for s, c in dist.items() if s >= r_a_int) / total_subsets
        p_value = min(1.0, 2 * min(p_le, p_ge))
        method = "exact"
    else:
        mean_u = n_a * n_b / 2
        tie_term = sum(t ** 3 - t for t in tie_group_sizes)
        var_u = (n_a * n_b / 12.0) * ((n_total + 1) - tie_term / (n_total * (n_total - 1)))
        if var_u <= 0:
            return {"statistic": round(statistic, 6), "p_value": None, "computable": False,
                    "reason": "wariancja <=0 (zbyt duzo remisow wzgledem n)",
                    "n_a": n_a, "n_b": n_b}
        cont_corr = 0.5 if u_a > mean_u else (-0.5 if u_a < mean_u else 0.0)
        z = (u_a - mean_u - cont_corr) / math.sqrt(var_u)
        p_value = max(0.0, min(1.0, 2 * (1 - _std_normal_cdf(abs(z)))))
        method = "normal_approx"

    return {"statistic": round(statistic, 6), "u_a": round(u_a, 6), "u_b": round(u_b, 6),
            "p_value": round(p_value, 8), "computable": True, "n_a": n_a, "n_b": n_b,
            "method": method, "has_ties": has_ties}
