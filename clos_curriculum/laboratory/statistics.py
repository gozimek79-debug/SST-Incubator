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
