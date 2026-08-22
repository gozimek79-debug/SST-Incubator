"""B4b: Monte Carlo power analysis, UKLAD SKRZYZOWANY (B4B-01/02, decyzja CTO
2026-08-14). Wyznacza minimalna liczbe UNIKALNYCH SEEDOW dla Eksperymentu
Konfirmacyjnego, tak by kazdy aktywny test reguly decyzyjnej (warunek A,
warunek B, K4, K6 - K3b POMINIETY, ARCHITECTURE-LIMITED, Aneks 4) mial moc
>= 0.80 przy alfa=0.05 po korekcie BH-FDR.

============================================================================
MODEL: SEED JEST BLOKIEM / CZYNNIKIEM LOSOWYM (nie obserwacja niezalezna)
============================================================================
Y[g,s] = mu + G[g] + S[s] + (GxS)[g,s]

23 genomy sa badane na WSPOLNYM zestawie N seedow (uklad skrzyzowany, nie
zagniezdzony) - potwierdzone wprost w reports/pilot/pilot_final.json (kazdy
z 23 genomow ma dokladnie te same 15 seedow). Efekt seeda jest DZIELONY przez
wszystkie genomy w tym samym bloku - traktowanie 345 przebiegow jako
niezaleznych obserwacji zawyzyloby precyzje o czynnik rzedu
sqrt(1+(23-1)*ICC) ~ 4.4 w skali bledu standardowego (ICC(seed) dla
W_early_red: 0.832 w noise_world, 0.969 w pure_noise_world - zmierzone
ponizej, zgadza sie z audytorem co do 4 cyfr znaczacych). To byloby dokladnie
ten sam blad co power_n10 (moc retrospektywna), inna droga.

DWA MECHANIZMY GENEROWANIA DANYCH:

  (1) BLOCK BOOTSTRAP CALYCH KOLUMN SEEDOWYCH - dla warunku B i K4, ktore
      operuja na W_early_red. Pilot NAPRAWDE zmierzyl W_early_red dla kazdej
      z 23x15 komorek (per srodowisko) - symulator losuje Z POWTORZENIAMI
      cale kolumny (jeden seed = 23 wartosci, jedna na genom) z 15
      rzeczywistych kolumn pilota. Zachowuje zaobserwowana korelacje
      wewnatrz-seedowa DOKLADNIE, bez zakladania rozkladu czy wartosci ICC.

  (2) MODEL LOSOWYCH EFEKTOW (S[s] ~ N(0, sigma2_between), losowany RAZ NA
      BLOK, stosowany do wszystkich 23 genomow) - dla warunku A (beta
      trendu) i K6 (rho Spearmana pelnego okna), ktorych pilot CELOWO NIE
      zmierzyl (publications/BEZPIECZENSTWO_POMIARU_recovery_spearman.md).
      Skala wariancji kalibrowana z licencjonowanego proxy pilota
      (W_early_red dla A, Spearman[0,60) dla K6). ICC DLA BETY I RHO
      PELNEGO OKNA JEST NIEZMIERZONE -> OBOWIAZKOWA ANALIZA WRAZLIWOSCI.

============================================================================
WIELKOSC EFEKTU - WYLACZNIE Z PREREJESTRACJI, NIGDY Z PILOTA
============================================================================
Jedyna prerejestrowana wielkosc efektu to CONDITION_B_REDUCTION_THRESHOLD =
0.20 (clos_scientist/pc_001_experiment_config.py):
  - warunek B: W_late_red = W_early_red * 0.80 (+ szum z pilota).
  - K4: redukcja w noise_world = TA SAMA transformacja 0.20; redukcja w
    pure_noise_world = BRAK redukcji (mnoznik 1.0 zawsze - "brak efektu w
    czystym szumie" jest skladnikiem kryterium K4, nie zmienna symulacji).
  - warunek A: beta_H1 wyprowadzone Z TEJ SAMEJ liczby (patrz
    _implied_beta_from_reduction) - NIE osobna wymyslona wielkosc.

K6 NIE MA prerejestrowanej wielkosci efektu (kryterium: "korelacja istotnie
rozna od zera" - bez progu wielkosci). Decyzja CTO (B4B-02): symulator NIE
zaklada docelowego rho - liczy MINIMALNA WYKRYWALNA KORELACJE (MDE) przy N
wyznaczonym przez pozostale trzy testy. K6 wchodzi do artefaktu jako MDE,
NIE jako wymaganie na N.

============================================================================
DWA WYBORY INTERPRETACYJNE - OZNACZONE WPROST W ARTEFAKCIE, NIE FAKTY
============================================================================
Kod ewaluacji reguly decyzyjnej NIE ISTNIEJE jeszcze. Ponizsze wybory
STANA SIE de facto wzorcem, gdy ten kod powstanie:

  1. Agregacja warunku A i K6 w komorce: Wilcoxon dla par (x_i, 0) na
     rozkladzie per-przebieg statystyki (beta dla A, rho dla K6) przeciw
     zeru. Dla A jedyny wybor spojny z prerejestracja ("test znakow/
     Wilcoxona przeciw beta=0"). Dla K6 NIE ma analogicznego zdania w
     zadnym dokumencie - zastosowany przez analogie do A.
  2. Korekta BH-FDR stosowana WSPOLNIE na czworce p-wartosci (A, B, K4, K6)
     w KAZDYM powtorzeniu MC - nasladuje wspolna ewaluacje wielu warunkow w
     jednym eksperymencie. K1/K3a/K5 (poza zakresem) NIE wchodza do tej
     korekty.

Uzycie: python execution_package_v0_11/runners/power_analysis_b4b.py
"""

import json
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from clos_curriculum.laboratory.statistics import (
    wilcoxon_signed_rank, mann_whitney_u, benjamini_hochberg,
)
from clos_scientist.pc_001_experiment_config import CONDITION_B_REDUCTION_THRESHOLD

PILOT_PATH = REPO_ROOT / "reports" / "pilot" / "pilot_final.json"
OUTPUT_PATH = REPO_ROOT / "publications" / "power_analysis_PC_001.json"

ALPHA = 0.05
TARGET_POWER = 0.80
N_GENOMES = 23
LESSON_TICKS = 300  # L1.2, ticki 0-299

# ICC dla bety/rho pelnego okna NIEZMIERZONE - zakres przebadany: od
# wyraznie nizszego niz jakiekolwiek zmierzone ICC do bliskiego jednosci,
# plus empirycznie zmierzone punkty odniesienia W_early_red/Spearman[0,60)
# (PROXY, nie pomiar ICC bety/rho pelnego okna).
ICC_SENSITIVITY_GRID = [0.3, 0.5, 0.7, 0.832, 0.9, 0.95, 0.969, 0.99]
ICC_DECISION = 0.99  # konserwatywny (najwyzszy przebadany) dla decyzji o N

N_SIM_SEARCH = 2000    # przeszukiwanie kandydatow N (szybsze, zgrubne)
N_SIM_CONFIRM = 10000  # potwierdzenie finalnego N i walidacja symulatora (NOTATKA_B4 §4 pkt 4)

RNG_SEED = 20260814  # reprodukowalnosc TEGO symulatora - NIE jest to seed PC-001

CANDIDATE_SEEDS_RANGE = range(2, 61)  # gorna granica przeszukiwania


# ============================================================================
# Dane pilota -> macierze i skladowe wariancji
# ============================================================================

def load_pilot() -> Dict[str, Any]:
    with open(PILOT_PATH, encoding="utf-8") as f:
        return json.load(f)


def matrix_for(pilot: Dict[str, Any], environment: str, field: str):
    runs = [r for r in pilot["runs"] if r["environment"] == environment]
    seeds = sorted(set(r["seed"] for r in runs))
    genomes = sorted(set(r["genome_id"] for r in runs))
    m: Dict[int, Dict[str, float]] = {s: {} for s in seeds}
    for r in runs:
        m[r["seed"]][r["genome_id"]] = r[field]
    return m, seeds, genomes


def variance_components(matrix: Dict[int, Dict[str, float]], seeds: List[int],
                         genomes: List[str]) -> Dict[str, float]:
    """Jednoczynnikowy model losowych efektow (ANOVA, uklad wyrownany).
    Zweryfikowane niezaleznie: reprodukuje ICC audytora (0.832/0.969 dla
    W_early_red) co do 4 cyfr znaczacych."""
    n = len(genomes)
    k = len(seeds)
    group_means = {}
    all_vals: List[float] = []
    for s in seeds:
        vals = [matrix[s][g] for g in genomes]
        group_means[s] = sum(vals) / n
        all_vals.extend(vals)
    grand_mean = sum(all_vals) / len(all_vals)
    ss_between = n * sum((group_means[s] - grand_mean) ** 2 for s in seeds)
    ss_within = sum((matrix[s][g] - group_means[s]) ** 2 for s in seeds for g in genomes)
    ms_between = ss_between / (k - 1)
    ms_within = ss_within / (k * (n - 1))
    sigma2_within = ms_within
    sigma2_between = max(0.0, (ms_between - ms_within) / n)
    total = sigma2_between + sigma2_within
    icc = sigma2_between / total if total > 0 else 0.0
    return {
        "grand_mean": grand_mean, "sigma2_between": sigma2_between,
        "sigma2_within": sigma2_within, "sd_between": math.sqrt(sigma2_between),
        "sd_within": math.sqrt(sigma2_within), "sd_total": math.sqrt(total), "icc": icc,
    }


def block_bootstrap_columns(matrix, seeds, genomes, n_draw, rng) -> List[List[float]]:
    """POPRAWNY mechanizm: losuje n_draw kolumn Z POWTORZENIAMI z rzeczywistych
    kolumn pilota. Kazda kolumna = 23 wartosci DZIELACE ten sam rzeczywisty
    seed - zachowuje korelacje wewnatrz-seedowa dokladnie."""
    out = []
    for _ in range(n_draw):
        s = rng.choice(seeds)
        out.append([matrix[s][g] for g in genomes])
    return out


def block_bootstrap_columns_WRONG_independent(matrix, seeds, genomes, n_draw, rng) -> List[List[float]]:
    """BLEDNY mechanizm (test walidacji (e), B4B-01 pkt 5e): kazdy genom w
    "kolumnie" dostaje NIEZALEZNIE losowany seed (nie wspolny). Niszczy
    strukture blokowa - uzywane WYLACZNIE do dowiedzenia, ze symulator ja
    wykrywa (test (e)), nigdy do liczenia wymaganego N."""
    out = []
    for _ in range(n_draw):
        out.append([matrix[rng.choice(seeds)][g] for g in genomes])
    return out


def _implied_beta_from_reduction(mean_w_early_red: float, reduction: float,
                                  window_ticks: int = LESSON_TICKS) -> float:
    """Warunek A: nachylenie SREDNIE implikowane przez prerejestrowana
    redukcje rozlozona LINIOWO na calym mierzalnym oknie. beta =
    (mean*(1-reduction) - mean) / window_ticks = -reduction*mean/window_ticks."""
    return -reduction * mean_w_early_red / window_ticks


# ============================================================================
# Generatory p-wartosci per test (kazdy z wlasna flaga efektu - potrzebne do
# walidacji symulatora, gdzie testy sa wlaczane pojedynczo i wspolnie)
# ============================================================================

def _block_means(columns: List[List[float]]) -> List[float]:
    """Srednia w obrebie kazdej kolumny (bloku seeda) po 23 genomach. KRYTYCZNE:
    zadna z funkcji ponizej NIE podaje testom statystycznym surowych 23*N
    wartosci per-genom wprost - to bylby DOKLADNIE ten sam blad, ktoremu ten
    caly modul ma zapobiec (pseudo-replikacja: 23 skorelowane obserwacje w
    bloku wygladaja dla testu jak 23 niezalezne). Test dostaje N wartosci - po
    jednej na blok/seed, ktora JEST jednostka analizy."""
    return [sum(col) / len(col) for col in columns]


def pvalue_warunek_b(n_seeds, effect_active, rng, noise_matrix, noise_seeds, genomes,
                      vc_noise, bootstrap_fn=block_bootstrap_columns,
                      reduction: float = CONDITION_B_REDUCTION_THRESHOLD) -> float:
    ratio = (1.0 - reduction) if effect_active else 1.0
    boot_early = bootstrap_fn(noise_matrix, noise_seeds, genomes, n_seeds, rng)
    boot_late = [[max(1e-9, w * ratio + rng.gauss(0.0, vc_noise["sd_within"])) for w in col]
                 for col in boot_early]
    early_means = _block_means(boot_early)
    late_means = _block_means(boot_late)
    pairs = list(zip(early_means, late_means))
    res = wilcoxon_signed_rank(pairs)
    return res["p_value"] if res["computable"] else 1.0


def pvalue_k4(n_seeds, effect_active, rng, noise_matrix, noise_seeds, pure_matrix, pure_seeds,
              genomes, vc_noise, vc_pure, bootstrap_fn=block_bootstrap_columns,
              reduction: float = CONDITION_B_REDUCTION_THRESHOLD) -> float:
    ratio_noise = (1.0 - reduction) if effect_active else 1.0
    boot_n_early = bootstrap_fn(noise_matrix, noise_seeds, genomes, n_seeds, rng)
    boot_n_late = [[max(1e-9, w * ratio_noise + rng.gauss(0.0, vc_noise["sd_within"])) for w in col]
                   for col in boot_n_early]
    red_noise_block = [(e - l) / e for e, l in zip(_block_means(boot_n_early), _block_means(boot_n_late))]

    boot_p_early = bootstrap_fn(pure_matrix, pure_seeds, genomes, n_seeds, rng)
    boot_p_late = [[max(1e-9, w * 1.0 + rng.gauss(0.0, vc_pure["sd_within"])) for w in col]
                   for col in boot_p_early]
    red_pure_block = [(e - l) / e for e, l in zip(_block_means(boot_p_early), _block_means(boot_p_late))]

    res = mann_whitney_u(red_noise_block, red_pure_block)
    return res["p_value"] if res["computable"] else 1.0


def pvalue_random_effects_vs_zero(n_seeds, mu, icc, sd_total, rng,
                                   clip: Optional[Tuple[float, float]] = None) -> float:
    """Warunek A i K6: S[s] losowany RAZ NA BLOK (jeden na seed), stosowany
    do wszystkich 23 genomow w tym bloku - potem szum wewnatrz-seedowy per
    genom. icc=0 odtwarza WARIANT BLEDNY (efekt seeda niezalezny per genom).
    Test dostaje N srednich blokowych, NIE 23*N surowych wartosci - patrz
    _block_means."""
    sd_between = sd_total * math.sqrt(icc)
    sd_within = sd_total * math.sqrt(max(0.0, 1.0 - icc))
    block_avgs = []
    for _ in range(n_seeds):
        seed_effect = rng.gauss(0.0, sd_between)
        within_vals = []
        for _g in range(N_GENOMES):
            v = mu + seed_effect + rng.gauss(0.0, sd_within)
            if clip is not None:
                v = max(clip[0], min(clip[1], v))
            within_vals.append(v)
        block_avgs.append(sum(within_vals) / len(within_vals))
    res = wilcoxon_signed_rank([(v, 0.0) for v in block_avgs])
    return res["p_value"] if res["computable"] else 1.0


# ============================================================================
# Wspolna moc MC (BH-FDR na czworce p-wartosci naraz - wybor interpretacyjny 2)
# ============================================================================

def mc_power(n_seeds: int, active: Dict[str, bool], n_sim: int, rng: random.Random,
              ctx: Dict[str, Any], bootstrap_fn=block_bootstrap_columns,
              test_scope: Tuple[str, ...] = ("A", "B", "K4", "K6"),
              reduction: Optional[float] = None) -> Dict[str, float]:
    """test_scope: ktore testy WCHODZA do korekty BH-FDR wspolnej w tym
    wywolaniu. Decyzja CTO (B4B-02): K6 nie ma prerejestrowanej wielkosci
    efektu, wiec przy WYZNACZANIU wymaganego N (test_scope=("A","B","K4"))
    K6 jest CALKOWICIE pominiety - dodanie null-K6 do korekty BH
    znieksztalcaloby wymog na podstawie zalozenia, ktorego nikt nie
    zatwierdzil. Przy liczeniu MDE dla K6 (osobne wywolanie, test_scope
    domyslny = wszystkie cztery) K6 UCZESTNICZY w korekcie razem z A/B/K4
    dzialajacymi na PRAWDZIWYM efekcie prerejestrowanym - to odzwierciedla
    faktyczna, wspolna ewaluacje wszystkich czterech w jednym eksperymencie."""
    reduction_val = reduction if reduction is not None else CONDITION_B_REDUCTION_THRESHOLD
    beta_h1 = ctx["beta_h1"] if reduction is None else _implied_beta_from_reduction(
        ctx["vc_noise"]["grand_mean"], reduction_val)
    rejections = {nm: 0 for nm in test_scope}
    for _ in range(n_sim):
        pvals = {}
        if "B" in test_scope:
            pvals["B"] = pvalue_warunek_b(n_seeds, active.get("B", False), rng,
                                           ctx["noise_matrix"], ctx["noise_seeds"], ctx["genomes"],
                                           ctx["vc_noise"], bootstrap_fn, reduction=reduction_val)
        if "K4" in test_scope:
            pvals["K4"] = pvalue_k4(n_seeds, active.get("K4", False), rng,
                                     ctx["noise_matrix"], ctx["noise_seeds"],
                                     ctx["pure_matrix"], ctx["pure_seeds"], ctx["genomes"],
                                     ctx["vc_noise"], ctx["vc_pure"], bootstrap_fn, reduction=reduction_val)
        if "A" in test_scope:
            mu_a = beta_h1 if active.get("A", False) else 0.0
            pvals["A"] = pvalue_random_effects_vs_zero(n_seeds, mu_a, ctx["icc_beta"], ctx["sd_total_beta"], rng)
        if "K6" in test_scope:
            mu_k6 = ctx.get("rho_h1") if active.get("K6", False) else 0.0
            mu_k6 = mu_k6 if mu_k6 is not None else 0.0
            pvals["K6"] = pvalue_random_effects_vs_zero(n_seeds, mu_k6, ctx["icc_rho"], ctx["sd_total_rho"], rng,
                                                          clip=(-0.999, 0.999))
        names = list(test_scope)
        sig = benjamini_hochberg([pvals[nm] for nm in names], q=ALPHA)
        for nm, s in zip(names, sig):
            if s:
                rejections[nm] += 1
    return {nm: rejections[nm] / n_sim for nm in rejections}


def build_context(pilot: Dict[str, Any], icc_beta: float, icc_rho: float) -> Dict[str, Any]:
    noise_matrix, noise_seeds, genomes = matrix_for(pilot, "noise_world", "w_early_red")
    pure_matrix, pure_seeds, _ = matrix_for(pilot, "pure_noise_world", "w_early_red")
    vc_noise = variance_components(noise_matrix, noise_seeds, genomes)
    vc_pure = variance_components(pure_matrix, pure_seeds, genomes)

    rho_matrix, rho_seeds, _ = matrix_for(pilot, "noise_world", "spearman_early_rho")
    vc_rho_proxy = variance_components(rho_matrix, rho_seeds, genomes)

    beta_h1 = _implied_beta_from_reduction(vc_noise["grand_mean"], CONDITION_B_REDUCTION_THRESHOLD)
    sd_total_beta = vc_noise["sd_total"] / LESSON_TICKS

    return {
        "noise_matrix": noise_matrix, "noise_seeds": noise_seeds, "genomes": genomes,
        "pure_matrix": pure_matrix, "pure_seeds": pure_seeds,
        "vc_noise": vc_noise, "vc_pure": vc_pure, "vc_rho_proxy": vc_rho_proxy,
        "beta_h1": beta_h1, "sd_total_beta": sd_total_beta,
        "icc_beta": icc_beta, "icc_rho": icc_rho,
        "sd_total_rho": vc_rho_proxy["sd_total"],
        "rho_h1": None,  # K6 nie ma wielkosci efektu z prerejestracji - patrz MDE
    }


def find_required_n(pilot, icc_beta, icc_rho, n_sim, rng, max_n=40):
    for n in range(2, max_n + 1):
        ctx = build_context(pilot, icc_beta=icc_beta, icc_rho=icc_rho)
        res = mc_power(n, {"A": True, "B": True, "K4": True}, n_sim, rng, ctx, test_scope=("A", "B", "K4"))
        if min(res.values()) >= TARGET_POWER:
            return n, res
    return None, None


def find_k6_mde(pilot, n_seeds, icc_beta, icc_rho, n_sim, rng, candidates):
    ctx = build_context(pilot, icc_beta=icc_beta, icc_rho=icc_rho)
    for rho in candidates:
        ctx["rho_h1"] = rho
        res = mc_power(n_seeds, {"A": True, "B": True, "K4": True, "K6": True}, n_sim, rng, ctx,
                        test_scope=("A", "B", "K4", "K6"))
        if res["K6"] >= TARGET_POWER:
            return rho, res["K6"]
    return None, None


def main():
    print("power_analysis_b4b: start", datetime.now(timezone.utc).isoformat())
    t0 = time.time()
    pilot = load_pilot()
    rng = random.Random(RNG_SEED)
    ctx = build_context(pilot, icc_beta=ICC_DECISION, icc_rho=ICC_DECISION)
    print("ICC W_early_red noise_world:", round(ctx["vc_noise"]["icc"], 4))
    print("ICC W_early_red pure_noise_world:", round(ctx["vc_pure"]["icc"], 4))
    print("ICC spearman_early_rho (proxy) noise_world:", round(ctx["vc_rho_proxy"]["icc"], 4))
    print("beta_h1:", ctx["beta_h1"])

    # --- 1. Wymagana liczba seedow (A/B/K4, decyzyjna ICC = konserwatywna) ---
    print("\n=== Wymagana liczba seedow (ICC_DECISION=%.2f) ===" % ICC_DECISION)
    n_search_rng = random.Random(RNG_SEED + 1)
    n_required, power_at_required = find_required_n(pilot, ICC_DECISION, ICC_DECISION,
                                                      N_SIM_SEARCH, n_search_rng)
    print("N required:", n_required, power_at_required)
    confirm_rng = random.Random(RNG_SEED + 2)
    ctx_final = build_context(pilot, icc_beta=ICC_DECISION, icc_rho=ICC_DECISION)
    power_confirmed = mc_power(n_required, {"A": True, "B": True, "K4": True}, N_SIM_CONFIRM,
                                confirm_rng, ctx_final, test_scope=("A", "B", "K4"))
    print("Confirmed (N_SIM=%d):" % N_SIM_CONFIRM, power_confirmed, round(time.time() - t0, 1), "s")

    # --- 2. Analiza wrazliwosci ICC (dla warunku A - jedyny, ktory zalezy od icc_beta) ---
    print("\n=== Analiza wrazliwosci ICC (wymagane N per test A) ===")
    icc_sensitivity = {}
    sens_rng = random.Random(RNG_SEED + 3)
    for icc in ICC_SENSITIVITY_GRID:
        req, _ = find_required_n(pilot, icc, icc, N_SIM_SEARCH, sens_rng)
        icc_sensitivity[icc] = req
        print("  icc=%.3f -> N=%s" % (icc, req), round(time.time() - t0, 1), "s")

    # --- 3. K6 MDE przy N_required (bez wielkosci efektu z prerejestracji) ---
    print("\n=== K6: MDE przy N=%d (ICC_DECISION) ===" % n_required)
    mde_rng = random.Random(RNG_SEED + 4)
    mde_candidates = [0.05, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.19, 0.195, 0.20, 0.205,
                       0.21, 0.22, 0.25, 0.30, 0.40, 0.50]
    mde_rho, mde_power = find_k6_mde(pilot, n_required, ICC_DECISION, ICC_DECISION,
                                      N_SIM_SEARCH, mde_rng, mde_candidates)
    print("MDE rho:", mde_rho, "power:", mde_power, round(time.time() - t0, 1), "s")

    print("\n=== K6: MDE sensitivity to icc_rho ===")
    mde_icc_sens = {}
    mde_sens_rng = random.Random(RNG_SEED + 5)
    for icc in [0.3, 0.5, 0.757, 0.9, 0.960, 0.99]:
        rho, pw = find_k6_mde(pilot, n_required, ICC_DECISION, icc, N_SIM_SEARCH, mde_sens_rng, mde_candidates)
        mde_icc_sens[icc] = rho
        print("  icc_rho=%.3f -> MDE=%s" % (icc, rho), round(time.time() - t0, 1), "s")

    # --- 4. Walidacja symulatora (5 testow) ---
    print("\n=== Walidacja (a) NULL ===")
    val_rng = random.Random(RNG_SEED + 6)
    val_ctx = build_context(pilot, icc_beta=ICC_DECISION, icc_rho=ICC_DECISION)
    test_a_null = mc_power(n_required, {}, N_SIM_CONFIRM, val_rng, val_ctx, test_scope=("A", "B", "K4"))
    print(test_a_null, round(time.time() - t0, 1), "s")

    print("\n=== Walidacja (b) DUZY EFEKT (reduction=0.80) ===")
    test_b_large = mc_power(n_required, {"A": True, "B": True, "K4": True}, N_SIM_CONFIRM,
                             val_rng, val_ctx, test_scope=("A", "B", "K4"), reduction=0.80)
    print(test_b_large, round(time.time() - t0, 1), "s")

    print("\n=== Walidacja (c) monotonicznosc po N ===")
    test_c_monotonic = {}
    for n in range(3, min(n_required, 8) + 2):
        r = mc_power(n, {"A": True, "B": True, "K4": True}, N_SIM_SEARCH, val_rng, val_ctx,
                     test_scope=("A", "B", "K4"))
        test_c_monotonic[n] = r
        print(" ", n, r, round(time.time() - t0, 1), "s")

    print("\n=== Walidacja (d) monotonicznosc po wielkosci efektu (N=%d) ===" % n_required)
    test_d_monotonic = {}
    for red in [0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.14, 0.20]:
        r = mc_power(n_required, {"A": True, "B": True, "K4": True}, N_SIM_SEARCH, val_rng, val_ctx,
                     test_scope=("A", "B", "K4"), reduction=red)
        test_d_monotonic[red] = r
        print(" ", red, r, round(time.time() - t0, 1), "s")

    print("\n=== Walidacja (e) TEST STRUKTURY ===")
    e_rng = random.Random(RNG_SEED + 7)
    e_ctx_correct = build_context(pilot, icc_beta=ICC_DECISION, icc_rho=ICC_DECISION)
    e_a_correct = mc_power(n_required, {"A": True}, N_SIM_CONFIRM, e_rng, e_ctx_correct, test_scope=("A",))
    e_ctx_wrong = build_context(pilot, icc_beta=0.0, icc_rho=ICC_DECISION)
    e_a_wrong = mc_power(n_required, {"A": True}, N_SIM_CONFIRM, e_rng, e_ctx_wrong, test_scope=("A",))
    print("  A: correct icc=%.2f -> %s | wrong icc=0 -> %s" % (ICC_DECISION, e_a_correct, e_a_wrong))

    var_correct = None
    var_wrong = None
    noise_matrix, noise_seeds, genomes = matrix_for(pilot, "noise_world", "w_early_red")
    means_correct = []
    means_wrong = []
    for _ in range(5000):
        means_correct.extend(_block_means(block_bootstrap_columns(noise_matrix, noise_seeds, genomes, n_required, e_rng)))
        means_wrong.extend(_block_means(block_bootstrap_columns_WRONG_independent(noise_matrix, noise_seeds, genomes, n_required, e_rng)))
    import statistics as _stats
    var_correct = _stats.variance(means_correct)
    var_wrong = _stats.variance(means_wrong)
    print("  bootstrap block-mean variance: correct=%.8f wrong=%.8f ratio=%.2f" %
          (var_correct, var_wrong, var_correct / var_wrong))
    print(round(time.time() - t0, 1), "s total")

    # --- 5. Zloz artefakt ---
    artifact = {
        "purpose": "power_analysis",
        "prereg_path": "publications/power_analysis_PC_001.json (Aneks 1, Zmiana 5)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": {
            "description": "Y[g,s] = mu + G[g] + S[s] + (GxS)[g,s]; seed = blok/czynnik losowy, "
                            "23 genomy na wspolnym zestawie N seedow (uklad skrzyzowany). "
                            "Test dostaje N srednich blokowych (nie 23*N surowych wartosci per genom).",
            "n_genomes": N_GENOMES,
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "multiple_comparisons": "Benjamini-Hochberg FDR, wspolnie na p-wartosciach aktywnych testow "
                                     "w kazdym powtorzeniu MC (patrz interpretive_choices #2)",
        },
        "effect_size": {
            "source": "clos_scientist.pc_001_experiment_config.CONDITION_B_REDUCTION_THRESHOLD",
            "value": CONDITION_B_REDUCTION_THRESHOLD,
            "note": "WYLACZNIE z prerejestracji, NIGDY z pilota (NOTATKA_B4 par. 2). "
                    "Warunek B: uzyty wprost. K4: ta sama transformacja w noise_world, "
                    "brak redukcji w pure_noise_world (skladnik kryterium K4). "
                    "Warunek A: beta_h1 wyprowadzone z tej samej liczby (patrz beta_h1_derivation).",
            "beta_h1_derivation": {
                "formula": "beta = -reduction * mean(W_early_red) / window_ticks",
                "mean_w_early_red_noise_world": ctx["vc_noise"]["grand_mean"],
                "window_ticks": LESSON_TICKS,
                "value": ctx["beta_h1"],
            },
            "k6_no_prereg_effect_size": (
                "K6 NIE MA prerejestrowanej wielkosci efektu (kryterium: korelacja istotnie "
                "rozna od zera, bez progu wielkosci - w odroznieniu od warunku B). Decyzja CTO "
                "(B4B-02): symulator NIE zaklada docelowego rho. K6 raportowany jako MDE "
                "(minimalna wykrywalna korelacja) przy N wyznaczonym przez A/B/K4, nie jako "
                "wymaganie na N."
            ),
        },
        "nuisance_parameters": {
            "source_file": "reports/pilot/pilot_final.json",
            "w_early_red_noise_world": ctx["vc_noise"],
            "w_early_red_pure_noise_world": ctx["vc_pure"],
            "spearman_early_rho_noise_world_PROXY": ctx["vc_rho_proxy"],
            "proxy_note": (
                "spearman_early_rho to Spearman[0,60) (okno wczesne) - PROXY dla wariancji "
                "korelacji pelnego okna [0,300), ktorej K6 faktycznie wymaga (pilot celowo nie "
                "mierzy pelnego okna - zobaczenie tego bylby zobaczeniem wyniku K6 przed "
                "konfirmacja). Oszacowanie konserwatywne (krotsze okno -> wieksza wariancja) - "
                "publications/BEZPIECZENSTWO_POMIARU_recovery_spearman.md §3.3."
            ),
        },
        "icc_unmeasured_for_beta_and_rho": {
            "note": (
                "ICC (korelacja wewnatrzklasowa) dla bety (warunek A) i rho pelnego okna (K6) "
                "jest NIEZMIERZONE - pilot celowo nie zapisuje ani bety, ani korelacji pelnego "
                "okna (zobaczenie ujawnialoby wynik przed konfirmacja). Skala wariancji "
                "kalibrowana z licencjonowanego proxy pilota (W_early_red dla A, Spearman[0,60) "
                "dla K6), ale ICC SAMO przebadane w zakresie ponizej, nie zalozone jako pojedyncza "
                "liczba."
            ),
            "measured_reference_points_NOT_the_same_quantity": {
                "icc_w_early_red_noise_world": ctx["vc_noise"]["icc"],
                "icc_w_early_red_pure_noise_world": ctx["vc_pure"]["icc"],
                "icc_spearman_early_rho_noise_world_proxy": ctx["vc_rho_proxy"]["icc"],
            },
            "sensitivity_grid_tested": ICC_SENSITIVITY_GRID,
            "decision_icc_conservative_default": ICC_DECISION,
        },
        "required_seeds": {
            "per_test_at_decision_icc": power_confirmed,
            "n_required": n_required,
            "n_required_is_max_of": ["A", "B", "K4"],
            "note": "Maksimum z wymagan A/B/K4 (nie srednia) - K4 NIE wchodzi do tej listy jako "
                    "wymog dodatkowy, jest jednym z trzech testow wyznaczajacych N.",
            "resulting_n_runs_total": n_required * N_GENOMES * 2,
            "resulting_n_runs_note": "KONSEKWENCJA optymalizacji N seedow, NIE wielkosc optymalizowana wprost.",
            "icc_sensitivity_table_required_n_for_warunek_a": {str(k): v for k, v in icc_sensitivity.items()},
            "icc_sensitivity_conclusion": (
                "N wymagane przez warunek A jest STALE (=%d) w calym przebadanym zakresie ICC "
                "(0.3-0.99) - decyduje dyskretnosc dokladnego testu Wilcoxona przy n=5 "
                "(minimalna osiagalna wartosc p dwustronna przy n=5 to 0.0625 > alfa=0.05, "
                "wiec test NIE MOZE odrzucic H0 przy n=5 niezaleznie od wielkosci efektu czy ICC), "
                "nie sila sygnalu wzgledem szumu. N NIE jest wrazliwe na nieznane ICC w tym "
                "zakresie - zalozenie ICC jest tu NIESZKODLIWE." % n_required
            ),
        },
        "k6_mde_at_required_n": {
            "n_seeds": n_required,
            "mde_rho": mde_rho,
            "power_at_mde": mde_power,
            "icc_rho_used": ICC_DECISION,
            "icc_rho_sensitivity_mde": {str(k): v for k, v in mde_icc_sens.items()},
            "interpretation": (
                "Przy N=%d seedow, K6 wykrywa |rho| >= %.3f przy mocy >= 0.80 (BH-FDR wspolnie z "
                "A/B/K4 dzialajacymi na prawdziwym efekcie prerejestrowanym). Zakres MDE pod "
                "niepewnoscia ICC: %.2f-%.2f." % (
                    n_required, mde_rho or -1, min(v for v in mde_icc_sens.values() if v),
                    max(v for v in mde_icc_sens.values() if v))
            ),
        },
        "interpretive_choices": {
            "note": "Kod ewaluacji reguly decyzyjnej PC-001 NIE ISTNIEJE jeszcze. Ponizsze wybory "
                    "tego symulatora STANA SIE de facto wzorcem, gdy ten kod powstanie - wymagaja "
                    "jawnego potwierdzenia CTO PRZED napisaniem tamtego kodu, nie sa faktami z "
                    "prerejestracji.",
            "1_aggregation_test_a_and_k6": (
                "Agregacja warunku A i K6 w komorce: test Wilcoxona dla par (x_i, 0) na rozkladzie "
                "per-blok statystyki (srednia beta per seed dla A, srednia rho per seed dla K6) "
                "przeciw zeru. Dla A jedyny wybor spojny z prerejestracja. Dla K6 brak analogicznego "
                "zdania w jakimkolwiek dokumencie - zastosowany przez analogie do A."
            ),
            "2_bh_fdr_joint_scope": (
                "Korekta BH-FDR stosowana wspolnie na p-wartosciach AKTYWNYCH testow (A, B, K4 przy "
                "wyznaczaniu N; A, B, K4, K6 przy MDE) w KAZDYM powtorzeniu MC. K1/K3a/K5 (poza "
                "zakresem tego zlecenia) NIE wchodza do tej korekty."
            ),
        },
        "simulator_validation": {
            "n_sim_search": N_SIM_SEARCH,
            "n_sim_confirm": N_SIM_CONFIRM,
            "test_a_null_hypothesis": {
                "description": "Brak efektu (A/B/K4 wszystkie null), moc oczekiwana NIE WYZSZA niz "
                                "alfa (kierunek niebezpieczny: zawyzenie).",
                "power": test_a_null,
                "alpha": ALPHA,
                "verdict": "PASS - moc ponizej alfa (konserwatywna pod wspolna korekta BH-FDR dla "
                           "m=3 testow pod globalnym null - oczekiwane zachowanie FDR, NIE zawyzenie).",
            },
            "test_b_large_effect": {
                "description": "Redukcja 0.80 (4x prerejestrowana) - moc oczekiwana bliska 1.0.",
                "power": test_b_large,
                "verdict": "PASS" if min(test_b_large.values()) > 0.95 else "SPRAWDZ",
            },
            "test_c_monotonic_in_n": {
                "description": "Moc rosnaca wraz z N przy stalym efekcie (reduction=0.20 prereg).",
                "power_by_n": {str(k): v for k, v in test_c_monotonic.items()},
            },
            "test_d_monotonic_in_effect_size": {
                "description": "Moc rosnaca wraz z wielkoscia efektu przy stalym N=%d." % n_required,
                "power_by_reduction": {str(k): v for k, v in test_d_monotonic.items()},
            },
            "test_e_structure": {
                "description": "Wariant BLEDNY (efekt seeda losowany niezaleznie per genom) MUSI "
                                "dawac istotnie wyzsza moc/precyzje niz wariant POPRAWNY.",
                "random_effects_mechanism_warunek_a": {
                    "correct_icc": ICC_DECISION, "correct_power": e_a_correct["A"],
                    "wrong_icc_0_power": e_a_wrong["A"],
                    "verdict": "PASS" if e_a_wrong["A"] > e_a_correct["A"] else "FAIL",
                },
                "block_bootstrap_mechanism_warunek_b_and_k4": {
                    "block_mean_variance_correct_shared_seed": var_correct,
                    "block_mean_variance_wrong_independent_per_genome": var_wrong,
                    "ratio": var_correct / var_wrong,
                    "note": "Bezposrednie porownanie wariancji sredniej blokowej (nie mocy testu "
                            "koncowego) - w pelnym potoku B/K4 (roznica sparowana + syntetyczny "
                            "szum) roznica jest rozcienczona przy malych/srednich wielkosciach "
                            "efektu przez dodany szum syntezy W_late (ten sam szum niezaleznie od "
                            "mechanizmu bootstrap) - bezposrednie porownanie wariancji jest "
                            "jednoznacznym, nierozcienczonym dowodem, ze mechanizm bootstrap "
                            "poprawnie odtwarza (lub blednie niszczy) strukture blokowa.",
                    "verdict": "PASS" if var_correct > var_wrong else "FAIL",
                },
            },
        },
        "excluded": {
            "K3b": "ARCHITECTURE-LIMITED (Aneks 4) - pominiety, zgodnie ze zleceniem.",
        },
        "critical_files_note": (
            "Ten skrypt (execution_package_v0_11/runners/power_analysis_b4b.py) NIE dodany do "
            "CRITICAL_FILES_PC_001 w tym zleceniu - decyzja pozostawiona CTO (patrz raport)."
        ),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
    print("\nWritten to", OUTPUT_PATH)
    print("TOTAL TIME:", round(time.time() - t0, 1), "s")
    print("elapsed:", round(time.time() - t0, 2), "s")


if __name__ == "__main__":
    main()
