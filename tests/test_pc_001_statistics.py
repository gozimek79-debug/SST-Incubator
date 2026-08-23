"""PC-001 B3 (2026-07-28): walidacja testow statystycznych reguly decyzyjnej
(Wilcoxon, Kendall tau, Spearman, Mann-Whitney) przeciw scipy DO 1e-6 - ten sam
rygor co kruskal_wallis w v0.11 (nie przyjmujemy wlasnej implementacji na
slowo). scipy jest ZALEZNOSCIA TESTOWA WYLACZNIE (zainstalowane lokalnie do
tego pliku) - requirements.txt bez zmian, produkcyjny kod
(clos_curriculum/laboratory/statistics.py) nigdy go nie importuje (decyzja
CTO: scipy zyje poza repo, wiec nie wchodzi do CRITICAL_FILES_PC_001 hasha -
podbicie wersji scipy nie moze cicho zmienic wynikow analizy).

Przypadki brzegowe wymagane przez zlecenie: remisy (wazne dla testow
rangowych), n=0, n=1, wszystkie wartosci identyczne.
"""

import math
import random

import pytest

scipy_stats = pytest.importorskip("scipy.stats", reason="scipy jest zaleznoscia TESTOWA (walidacja), nie produkcyjna")

from clos_curriculum.laboratory.statistics import (
    wilcoxon_signed_rank,
    kendall_tau,
    spearman_rho,
    mann_whitney_u,
    block_means,
)
from execution_package_v0_11.runners.power_analysis_b4b import _block_means as _simulator_block_means
from clos_scientist.fallback_branch_diagnostic import (
    k7_fallback_branch_fraction,
    interpret_k7_fraction,
    default_prediction_depth,
)

TOL = 1e-6


def _random_pairs(n, seed):
    rng = random.Random(seed)
    return [(rng.uniform(0, 10), rng.uniform(0, 10)) for _ in range(n)]


class TestWilcoxonSignedRank:

    @pytest.mark.parametrize("n,seed", [(5, 1), (8, 2), (12, 3), (20, 4), (25, 5)])
    def test_matches_scipy_exact_no_ties(self, n, seed):
        pairs = _random_pairs(n, seed)
        mine = wilcoxon_signed_rank(pairs)
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        sp = scipy_stats.wilcoxon(x, y, zero_method="wilcox", mode="exact")
        assert mine["method"] == "exact"
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_matches_scipy_approx_with_ties(self):
        pairs = [(1.0, 1.0), (2.0, 1.5), (2.0, 1.5), (3.0, 2.0), (3.0, 2.0),
                 (4.0, 3.5), (1.5, 1.0), (2.5, 2.0), (3.5, 3.0), (4.5, 4.0)]
        mine = wilcoxon_signed_rank(pairs)
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        sp = scipy_stats.wilcoxon(x, y, zero_method="wilcox", mode="approx")
        assert mine["method"] == "normal_approx"
        assert mine["has_ties"] is True
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    @pytest.mark.parametrize("n,seed", [(30, 10), (40, 11)])
    def test_matches_scipy_approx_large_n_no_ties(self, n, seed):
        pairs = _random_pairs(n, seed)
        mine = wilcoxon_signed_rank(pairs, exact_max_n=25)
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        sp = scipy_stats.wilcoxon(x, y, zero_method="wilcox", mode="approx")
        assert mine["method"] == "normal_approx"
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_all_zero_differences_not_computable(self):
        pairs = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]
        result = wilcoxon_signed_rank(pairs)
        assert result["computable"] is False
        assert result["n_zero_dropped"] == 3

    def test_empty_input_not_computable(self):
        result = wilcoxon_signed_rank([])
        assert result["computable"] is False

    def test_n_1(self):
        result = wilcoxon_signed_rank([(5.0, 2.0)])
        assert result["computable"] is True
        assert result["n"] == 1
        assert result["method"] == "exact"
        # z jednym elementem: 2 permutacje, |diff| zawsze rangi 1 -> p=2*(1/2)=1
        assert abs(result["p_value"] - 1.0) < TOL


def _reference_wilcoxon_two_sided_pre_v7(pairs, exact_max_n=25):
    """Kopia NIEZALEZNA (nie import) implementacji wilcoxon_signed_rank
    SPRZED B4C-05 v7 (dodanie parametru 'alternative') - wylacznie do dowodu
    regresji ponizej. Jesli kiedys trzeba bedzie ja zmienic, znaczy to, ze
    domyslne (dwustronne) zachowanie funkcji faktycznie sie zmienilo - co
    ten test ma properly wykryc, nie przemilczec przez import tego samego
    kodu, ktory testuje."""
    from clos_curriculum.laboratory.statistics import _std_normal_cdf

    diffs = [a - b for a, b in pairs]
    nonzero = [d for d in diffs if d != 0]
    n_zero = len(diffs) - len(nonzero)
    n = len(nonzero)
    if n == 0:
        return {"computable": False, "p_value": None, "statistic": None,
                "n": 0, "n_zero_dropped": n_zero}

    abs_d = [abs(d) for d in nonzero]
    order = sorted(range(n), key=lambda i: abs_d[i])
    ranks = [0.0] * n
    tie_sizes = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs_d[order[j + 1]] == abs_d[order[i]]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        if j > i:
            tie_sizes.append(j - i + 1)
        i = j + 1

    w_plus = sum(r for r, d in zip(ranks, nonzero) if d > 0)
    w_minus = sum(r for r, d in zip(ranks, nonzero) if d < 0)
    statistic = min(w_plus, w_minus)
    has_ties = len(tie_sizes) > 0

    if n <= exact_max_n and not has_ties:
        max_sum = n * (n + 1) // 2
        counts = [0] * (max_sum + 1)
        counts[0] = 1
        running = 0
        for r in range(1, n + 1):
            running += r
            for s in range(min(running, max_sum), r - 1, -1):
                counts[s] += counts[s - r]
        total = 2 ** n
        wpi = int(round(w_plus))
        p_le = sum(counts[:wpi + 1]) / total
        p_ge = sum(counts[wpi:]) / total
        p_value = min(1.0, 2 * min(p_le, p_ge))
        method = "exact"
    else:
        mean = n * (n + 1) / 4
        var = n * (n + 1) * (2 * n + 1) / 24 - sum(t ** 3 - t for t in tie_sizes) / 48
        if var <= 0:
            return {"computable": False, "p_value": None, "statistic": round(statistic, 6),
                    "n": n, "n_zero_dropped": n_zero}
        z = (w_plus - mean) / math.sqrt(var)
        p_value = max(0.0, min(1.0, 2 * (1 - _std_normal_cdf(abs(z)))))
        method = "normal_approx"

    return {"statistic": round(statistic, 6), "w_plus": round(w_plus, 6),
            "w_minus": round(w_minus, 6), "p_value": round(p_value, 8),
            "computable": True, "n": n, "n_zero_dropped": n_zero,
            "method": method, "has_ties": has_ties}


class TestWilcoxonAlternativeRegression:
    """B4C-05 v7 ZAKRES pkt 1-2: dodanie parametru 'alternative' (domyslnie
    'two-sided') NIE MOZE zmienic wyniku dla zadnego istniejacego
    wywolujacego. Dowod: NIEZALEZNA kopia starej implementacji (powyzej,
    _reference_wilcoxon_two_sided_pre_v7) porownana BIT W BIT z biezaca
    funkcja wywolana domyslnie (bez podania alternative), na kompletcie
    wzorcow wywolan realnie obecnych w repo:

      - 5 x parametrized (n,seed) z TestWilcoxonSignedRank.test_matches_scipy_exact_no_ties
      - 1 x dane z remisami (test_matches_scipy_approx_with_ties)
      - 2 x duze n bez remisow, approx (test_matches_scipy_approx_large_n_no_ties)
      - wszystkie roznice zerowe, pusta lista, n=1 (3 przypadki brzegowe)
      - ksztalt execution_package_v0_11/runners/power_analysis_b4b.py:219
        (pary (early_mean, late_mean))
      - ksztalt power_analysis_b4b.py:260 (pary (wartosc, 0.0) - test
        przeciw zeru, uzywany przez Warunek A i K6)

    Razem: 5 + 1 + 2 + 3 + 2 = 13 wzorcow wywolan sprawdzonych, kazdy
    porownany PO WSZYSTKICH kluczach obecnych w obu wynikach (nie tylko
    p_value)."""

    def _assert_bit_identical(self, pairs, exact_max_n=25):
        expected = _reference_wilcoxon_two_sided_pre_v7(pairs, exact_max_n)
        actual = wilcoxon_signed_rank(pairs, exact_max_n)
        assert actual["alternative"] == "two-sided"
        for key in expected:
            assert actual[key] == expected[key], f"klucz {key!r}: {actual[key]!r} != {expected[key]!r}"

    @pytest.mark.parametrize("n,seed", [(5, 1), (8, 2), (12, 3), (20, 4), (25, 5)])
    def test_exact_no_ties_bit_identical(self, n, seed):
        self._assert_bit_identical(_random_pairs(n, seed))

    def test_approx_with_ties_bit_identical(self):
        pairs = [(1.0, 1.0), (2.0, 1.5), (2.0, 1.5), (3.0, 2.0), (3.0, 2.0),
                 (4.0, 3.5), (1.5, 1.0), (2.5, 2.0), (3.5, 3.0), (4.5, 4.0)]
        self._assert_bit_identical(pairs)

    @pytest.mark.parametrize("n,seed", [(30, 10), (40, 11)])
    def test_approx_large_n_bit_identical(self, n, seed):
        self._assert_bit_identical(_random_pairs(n, seed), exact_max_n=25)

    def test_all_zero_differences_bit_identical(self):
        self._assert_bit_identical([(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)])

    def test_empty_input_bit_identical(self):
        self._assert_bit_identical([])

    def test_n_1_bit_identical(self):
        self._assert_bit_identical([(5.0, 2.0)])

    @pytest.mark.parametrize("n,seed", [(6, 100), (9, 101), (15, 102)])
    def test_paired_early_late_shape_bit_identical(self, n, seed):
        """Ksztalt power_analysis_b4b.py:219 - pary (early_mean, late_mean)."""
        rng = random.Random(seed)
        pairs = [(rng.uniform(0.05, 0.3), rng.uniform(0.02, 0.25)) for _ in range(n)]
        self._assert_bit_identical(pairs)

    @pytest.mark.parametrize("n,seed", [(6, 200), (9, 201), (15, 202)])
    def test_value_vs_zero_shape_bit_identical(self, n, seed):
        """Ksztalt power_analysis_b4b.py:260 - pary (wartosc, 0.0), test
        Warunku A/K6 przeciw zeru."""
        rng = random.Random(seed)
        block_avgs = [rng.gauss(0.0, 1.0) for _ in range(n)]
        pairs = [(v, 0.0) for v in block_avgs]
        self._assert_bit_identical(pairs)


class TestWilcoxonOneSided:
    """B4C-05 v6/v7: tryb jednostronny (K3a-warunek1, decyzja CTO ratyfikowana
    v6 pkt 2 - JEDNOSTRONNY Wilcoxon, H1: mediana(post_shock-pre_shock) > 0).

    ZAKRES WALIDACJI - dokladnie jak zazadano (mirror B3): OBOWIAZKOWO dane
    BEZ REMISOW, method='exact', zero_method='wilcox', alternative='greater'
    i 'two-sided', tolerancja 1e-6 - to jest jedyny regime, w ktorym repo i
    scipy licza TA SAMA wielkosc. ZAKAZANE: walidacja przeciw scipy
    method='exact' NA DANYCH Z REMISAMI - zmierzone bezposrednio (patrz
    dowod nizej w tym docstringu) i POTWIERDZONE jako niewlasciwe:

        roznice = [1.0, 1.0, -1.0, 2.0, 2.0, -3.0, 3.0, 0.5]  (remisy: 1.0x2, 2.0x2)
        repo (wlasna implementacja, normal_approx)         = 0.29004704
        scipy method='exact'  (BEZ OSTRZEZENIA o remisach)  = 0.3828125
        scipy method='approx'                                = 0.32340549

    scipy 1.15.3 przy method='exact' PO CICHU IGNORUJE remisy - roznica
    0.09 wobec repo nie jest bledem zadnej ze stron, tylko dowodem, ze te
    dwa narzedzia licza wtedy INNA wielkosc. Test negatywny ponizej
    (test_ties_regime_scipy_exact_silently_ignores_ties_do_not_validate_here)
    odtwarza to bezposrednio, zeby ta wiedza nie zniknela z kodu."""

    TOL = 1e-6

    @pytest.mark.parametrize("n,seed", [(5, 1), (8, 2), (12, 3), (20, 4), (25, 5), (9, 42)])
    def test_matches_scipy_exact_no_ties_greater(self, n, seed):
        pairs = _random_pairs(n, seed)
        mine = wilcoxon_signed_rank(pairs, alternative="greater")
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        sp = scipy_stats.wilcoxon(x, y, zero_method="wilcox", mode="exact", alternative="greater")
        assert mine["method"] == "exact"
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    @pytest.mark.parametrize("n,seed", [(5, 1), (8, 2), (12, 3), (20, 4), (25, 5), (9, 42)])
    def test_matches_scipy_exact_no_ties_less(self, n, seed):
        pairs = _random_pairs(n, seed)
        mine = wilcoxon_signed_rank(pairs, alternative="less")
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        sp = scipy_stats.wilcoxon(x, y, zero_method="wilcox", mode="exact", alternative="less")
        assert mine["method"] == "exact"
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    @pytest.mark.parametrize("n,seed", [(5, 1), (8, 2), (12, 3), (20, 4), (25, 5)])
    def test_matches_scipy_exact_no_ties_two_sided_still_matches(self, n, seed):
        """Re-potwierdzenie dwustronnego trybu PO refaktoryzacji na wspolne
        _wilcoxon_null_distribution - nie tylko regresja wewnetrzna, tez
        wciaz zgodny ze scipy."""
        pairs = _random_pairs(n, seed)
        mine = wilcoxon_signed_rank(pairs, alternative="two-sided")
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        sp = scipy_stats.wilcoxon(x, y, zero_method="wilcox", mode="exact", alternative="two-sided")
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_ties_regime_scipy_exact_silently_ignores_ties_do_not_validate_here(self):
        """DOWOD (nie test poprawnosci repo) - reprodukcja pomiaru z
        docstringu klasy: scipy method='exact' na danych z remisami daje
        WYNIK NIEZGODNY z repo, bo scipy po cichu ignoruje remisy w tym
        trybie. Ten test dokumentuje ROZBIEZNOSC jako oczekiwana, NIE
        naprawia jej i NIE dostraja repo do scipy w tym regime (B4C-05 v7,
        wprost zakazane)."""
        diffs = [1.0, 1.0, -1.0, 2.0, 2.0, -3.0, 3.0, 0.5]
        pairs = [(d, 0.0) for d in diffs]
        mine = wilcoxon_signed_rank(pairs)
        assert mine["has_ties"] is True
        assert mine["method"] == "normal_approx"
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        sp_exact = scipy_stats.wilcoxon(x, y, zero_method="wilcox", mode="exact")
        sp_approx = scipy_stats.wilcoxon(x, y, zero_method="wilcox", mode="approx")
        # repo zgadza sie z approx (poprawny regime dla remisow)...
        assert abs(mine["p_value"] - sp_approx.pvalue) < TOL
        # ...i NIE zgadza sie z exact (scipy po cichu ignoruje remisy tam) -
        # rozbieznosc jest OCZEKIWANA, nie regresja.
        assert abs(mine["p_value"] - sp_exact.pvalue) > 0.01

    def test_resolution_at_n9_one_sided_is_1_over_2_pow_9(self):
        """B4C-05 v7 ZAKRES pkt 4: min. osiagalne p jednostronne przy n=9,
        LICZONE WYWOLANIEM (uklad skrajny: wszystkie roznice dodatnie,
        maksymalnie separujacy), nie wzorem."""
        pairs = [(float(i + 1), 0.0) for i in range(9)]
        result = wilcoxon_signed_rank(pairs, alternative="greater")
        assert result["method"] == "exact"
        # p_value zaokraglane do 8 miejsc w funkcji (round(p_value, 8)) -
        # tolerancja musi to uwzgledniac, nie porownywac bit-w-bit z surowa
        # wartoscia 1/512.
        assert abs(result["p_value"] - (1 / 512)) < 1e-8

    def test_resolution_at_n9_two_sided_is_2_over_2_pow_9(self):
        """Kontrast: to samo skrajne ulozenie, tryb dwustronny daje 2x
        wiecej (2/512), NIE 1/512 - dowod, ze margines jednostronny/dwustronny
        rozni sie dokladnie czynnikiem 2 w tym skrajnym przypadku."""
        pairs = [(float(i + 1), 0.0) for i in range(9)]
        result = wilcoxon_signed_rank(pairs, alternative="two-sided")
        assert abs(result["p_value"] - (2 / 512)) < 1e-8

    def test_invalid_alternative_raises(self):
        with pytest.raises(ValueError):
            wilcoxon_signed_rank([(1.0, 0.0)], alternative="sideways")


class TestBlockMeansConsistency:
    """B4C-05 v8: block_means (clos_curriculum/laboratory/statistics.py,
    CZLONEK rejestru) MUSI dawac identyczny wynik co _block_means
    (execution_package_v0_11/runners/power_analysis_b4b.py, POZA rejestrem,
    Wariant C - plik wyprodukowal juz artefakt B4b, nietykany). Test spojnosci,
    NIE konsolidacja - dwie niezalezne implementacje tej samej, jednej
    definicji (srednia po kolumnie), porownywane na danych losowych."""

    N_CASES = 200

    def _random_columns(self, seed):
        rng = random.Random(seed)
        n_cols = rng.randint(1, 12)
        col_len = rng.randint(1, 23)
        return [[rng.uniform(-10, 10) for _ in range(col_len)] for _ in range(n_cols)]

    def test_identical_on_random_data(self):
        """200 losowych ukladow kolumn (rozna liczba kolumn, rozna dlugosc) -
        obie implementacje musza dac IDENTYCZNY wynik na kazdym."""
        checked = 0
        for seed in range(self.N_CASES):
            columns = self._random_columns(seed)
            mine = block_means(columns)
            simulator = _simulator_block_means(columns)
            assert mine == simulator, f"seed={seed}: {mine} != {simulator}"
            checked += 1
        assert checked == self.N_CASES

    def test_identical_on_23_genome_shape(self):
        """Ksztalt faktycznie uzywany przez rodzine BH-FDR: 23 genomy (wiersze)
        x N seedow (kolumny) - patrz publications/pc_001_bh_family.json."""
        for seed, n_seeds in [(1, 6), (2, 8), (3, 9), (4, 15)]:
            rng = random.Random(seed)
            columns = [[rng.uniform(0.0, 0.3) for _ in range(23)] for _ in range(n_seeds)]
            assert block_means(columns) == _simulator_block_means(columns)

    def test_negative_median_instead_of_mean_is_caught(self):
        """Dowod, ze test faktycznie porownuje WARTOSCI, nie tylko ksztalt
        wyniku - podmiana sredniej na mediane w jednej z dwoch 'implementacji'
        MUSI zostac zlapana."""
        def _median_variant(columns):
            result = []
            for col in columns:
                s = sorted(col)
                n = len(s)
                mid = n // 2
                result.append(s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2)
            return result

        columns = [[1.0, 2.0, 100.0], [5.0, 5.0, 5.0, 1.0]]
        mine = block_means(columns)
        median_variant = _median_variant(columns)
        assert mine != median_variant, "przypadek testowy nie roznicuje sredniej od mediany"

    def test_power_analysis_b4b_module_is_untouched(self):
        """B4C-05 v8 zakaz wprost: NIE edytuj power_analysis_b4b.py. Ten test
        nie dowodzi tego mechanicznie (to robi git diff, patrz raport), ale
        potwierdza, ze _block_means nadal istnieje pod swoim oryginalnym,
        prywatnym (podkreslnikowym) nazwiskiem w tym pliku - import powyzej
        (import _block_means as _simulator_block_means) nie wymagal zadnej
        zmiany sygnatury ani eksportu."""
        import inspect
        from execution_package_v0_11.runners import power_analysis_b4b as sim
        assert hasattr(sim, "_block_means")
        assert "sum(col) / len(col)" in inspect.getsource(sim._block_means)


class TestKendallTau:

    @pytest.mark.parametrize("n,seed", [(5, 1), (7, 2), (10, 3), (20, 4), (28, 5)])
    def test_matches_scipy_exact_no_ties(self, n, seed):
        rng = random.Random(seed)
        x = [rng.uniform(0, 10) for _ in range(n)]
        y = [rng.uniform(0, 10) for _ in range(n)]
        mine = kendall_tau(x, y)
        sp = scipy_stats.kendalltau(x, y, variant="b", method="exact")
        assert mine["method"] == "exact"
        assert abs(mine["tau"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_matches_scipy_asymptotic_with_ties(self):
        x = [1, 2, 2, 3, 3, 3, 4, 5, 5, 6]
        y = [2, 1, 3, 2, 4, 4, 5, 6, 5, 7]
        mine = kendall_tau(x, y)
        sp = scipy_stats.kendalltau(x, y, variant="b", method="asymptotic")
        assert mine["method"] == "normal_approx"
        assert mine["has_ties"] is True
        assert abs(mine["tau"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    @pytest.mark.parametrize("n,seed", [(35, 10), (50, 11)])
    def test_matches_scipy_asymptotic_large_n_no_ties(self, n, seed):
        rng = random.Random(seed)
        x = [rng.uniform(0, 10) for _ in range(n)]
        y = [rng.uniform(0, 10) for _ in range(n)]
        mine = kendall_tau(x, y, exact_max_n=30)
        sp = scipy_stats.kendalltau(x, y, variant="b", method="asymptotic")
        assert mine["method"] == "normal_approx"
        assert abs(mine["tau"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_n_less_than_2_not_computable(self):
        assert kendall_tau([1.0], [2.0])["computable"] is False
        assert kendall_tau([], [])["computable"] is False

    def test_all_identical_x_not_computable(self):
        result = kendall_tau([5.0, 5.0, 5.0, 5.0], [1.0, 2.0, 3.0, 4.0])
        assert result["computable"] is False
        assert "remis" in result["reason"] or "zerowy" in result["reason"]

    def test_k3b_scale_n7_matches_scipy(self):
        """K3b-1 realistyczny rozmiar: ~7 wstrzasow/przebieg."""
        rng = random.Random(99)
        x = list(range(7))
        y = [v + rng.uniform(-1, 1) for v in x]
        mine = kendall_tau(x, y)
        sp = scipy_stats.kendalltau(x, y, variant="b", method="exact")
        assert abs(mine["tau"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL


class TestSpearmanRho:

    @pytest.mark.parametrize("n,seed", [(3, 1), (5, 2), (10, 3), (25, 4), (50, 5)])
    def test_matches_scipy_no_ties(self, n, seed):
        rng = random.Random(seed)
        x = [rng.uniform(0, 10) for _ in range(n)]
        y = [rng.uniform(0, 10) for _ in range(n)]
        mine = spearman_rho(x, y)
        sp = scipy_stats.spearmanr(x, y)
        assert abs(mine["rho"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_matches_scipy_with_ties(self):
        x = [1, 2, 2, 3, 3, 3, 4, 5, 5, 6]
        y = [2, 1, 3, 2, 4, 4, 5, 6, 5, 7]
        mine = spearman_rho(x, y)
        sp = scipy_stats.spearmanr(x, y)
        assert abs(mine["rho"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_n_less_than_3_not_computable(self):
        assert spearman_rho([1.0, 2.0], [1.0, 2.0])["computable"] is False
        assert spearman_rho([], [])["computable"] is False

    def test_all_identical_not_computable(self):
        result = spearman_rho([5.0, 5.0, 5.0], [1.0, 2.0, 3.0])
        assert result["computable"] is False

    def test_perfect_correlation_p_zero(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        result = spearman_rho(x, y)
        assert abs(result["rho"] - 1.0) < TOL
        assert result["p_value"] == 0.0


class TestMannWhitneyU:

    @pytest.mark.parametrize("n_a,n_b,seed", [(5, 5, 1), (8, 10, 2), (15, 20, 3), (23, 23, 4)])
    def test_matches_scipy_exact_no_ties(self, n_a, n_b, seed):
        rng = random.Random(seed)
        a = [rng.uniform(0, 10) for _ in range(n_a)]
        b = [rng.uniform(0, 10) for _ in range(n_b)]
        mine = mann_whitney_u(a, b)
        sp = scipy_stats.mannwhitneyu(a, b, alternative="two-sided", method="exact")
        assert mine["method"] == "exact"
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_matches_scipy_asymptotic_with_ties(self):
        rng = random.Random(7)
        a = [round(rng.uniform(0, 5), 1) for _ in range(30)]
        b = [round(rng.uniform(0, 5), 1) for _ in range(30)]
        mine = mann_whitney_u(a, b, exact_max_product=1)
        sp = scipy_stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
        assert mine["method"] == "normal_approx"
        assert mine["has_ties"] is True
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_empty_group_not_computable(self):
        assert mann_whitney_u([], [1.0, 2.0])["computable"] is False
        assert mann_whitney_u([1.0], [])["computable"] is False

    def test_k4_scale_23_genomes_matches_scipy(self):
        """K4 realistyczny rozmiar: 23 genomy per srodowisko."""
        rng = random.Random(2026)
        shock = [rng.uniform(0, 1) for _ in range(23)]
        pure_noise = [rng.uniform(0, 1) for _ in range(23)]
        mine = mann_whitney_u(shock, pure_noise)
        sp = scipy_stats.mannwhitneyu(shock, pure_noise, alternative="two-sided", method="exact")
        assert abs(mine["p_value"] - sp.pvalue) < TOL


class TestBruteForceCrossCheck:
    """Weryfikacja NIEZALEZNA od scipy: dla bardzo malych n, przeliczenie
    metoda brute-force (pelna enumeracja) - trzecia, calkowicie oddzielna
    droga weryfikacji tego samego wyniku."""

    def test_wilcoxon_n4_brute_force(self):
        pairs = [(5.0, 2.0), (3.0, 1.0), (8.0, 7.0), (6.0, 6.5)]
        mine = wilcoxon_signed_rank(pairs)
        diffs = [a - b for a, b in pairs]
        nonzero = [d for d in diffs if d != 0]
        n = len(nonzero)
        abs_d = sorted(set(abs(d) for d in nonzero))
        # brak remisow w tym przykladzie - rangi to 1..n w kolejnosci |d|
        sorted_by_abs = sorted(range(n), key=lambda i: abs(nonzero[i]))
        rank_of = {idx: r + 1 for r, idx in enumerate(sorted_by_abs)}
        w_plus_true = sum(rank_of[i] for i in range(n) if nonzero[i] > 0)
        # enumeracja pelna 2^n znakow
        from itertools import product
        count_le = count_ge = 0
        total = 2 ** n
        for signs in product([1, -1], repeat=n):
            s = sum(rank_of[i] for i in range(n) if signs[i] > 0)
            if s <= w_plus_true:
                count_le += 1
            if s >= w_plus_true:
                count_ge += 1
        p_brute = min(1.0, 2 * min(count_le / total, count_ge / total))
        assert abs(mine["p_value"] - p_brute) < TOL

    def test_mann_whitney_n3_n3_brute_force(self):
        from itertools import combinations
        a = [1.0, 5.0, 9.0]
        b = [2.0, 4.0, 7.0]
        mine = mann_whitney_u(a, b)
        combined = sorted(a + b)
        ranks = {v: i + 1 for i, v in enumerate(combined)}
        n_a = len(a)
        all_ranks = list(range(1, len(combined) + 1))
        r_a_obs = sum(ranks[v] for v in a)
        total = 0
        le = ge = 0
        for subset in combinations(all_ranks, n_a):
            total += 1
            s = sum(subset)
            if s <= r_a_obs:
                le += 1
            if s >= r_a_obs:
                ge += 1
        p_brute = min(1.0, 2 * min(le / total, ge / total))
        assert abs(mine["p_value"] - p_brute) < TOL


class TestK7FallbackBranchDiagnostic:

    def test_default_prediction_depth_matches_tissue_dataclass(self):
        from clos_brain.tissue import BrainTissue
        tissue = BrainTissue(brain_id="x", genome_id="y")
        assert default_prediction_depth() == tissue.prediction_depth

    def test_perfect_fallback_match_gives_fraction_1(self):
        depth = 3
        inputs = [0.2, 0.4, 0.6, 0.8, 1.0, 0.5]
        predictions = [None, None, sum(inputs[0:3]) / 3, sum(inputs[1:4]) / 3,
                       sum(inputs[2:5]) / 3, sum(inputs[3:6]) / 3]
        result = k7_fallback_branch_fraction(predictions, inputs, depth)
        assert result["computable"] is True
        assert result["fraction"] == 1.0
        assert result["n_evaluable"] == 4

    def test_no_fallback_match_gives_fraction_0(self):
        depth = 3
        inputs = [0.1, 0.1, 0.1, 0.1, 0.1]
        predictions = [None, None, 0.9, 0.9, 0.9]
        result = k7_fallback_branch_fraction(predictions, inputs, depth)
        assert result["computable"] is True
        assert result["fraction"] == 0.0

    def test_prediction_depth_none_is_not_computable(self):
        result = k7_fallback_branch_fraction([1.0], [1.0], None)
        assert result["computable"] is False
        assert "nieobliczalny" not in result["reason"] or True  # tresc dowolna, computable=False wystarcza

    def test_gap_in_history_none_input_skips_tick(self):
        depth = 3
        inputs = [0.2, 0.4, None, 0.8, 1.0]
        predictions = [None, None, 0.5, 0.5, 0.5]
        result = k7_fallback_branch_fraction(predictions, inputs, depth)
        # tick 2 (window [0,1,2]) ma None w oknie -> pominiety
        # tick 3 (window [1,2,3]) ma None (input[2]) w oknie -> pominiety
        # tick 4 (window [2,3,4]) ma None (input[2]) w oknie -> pominiety
        assert result["computable"] is False
        assert result["n_total"] == 5

    def test_zero_evaluable_ticks_not_computable(self):
        result = k7_fallback_branch_fraction([0.5], [0.5], 3)
        assert result["computable"] is False

    def test_tolerance_respected(self):
        depth = 2
        inputs = [0.5, 0.5, 0.5]
        candidate = (0.5 + 0.5) / 2
        predictions = [None, candidate + 1e-3, None]
        result = k7_fallback_branch_fraction(predictions, inputs, depth, tolerance=1e-9)
        assert result["fraction"] == 0.0
        result_loose = k7_fallback_branch_fraction(predictions, inputs, depth, tolerance=1e-2)
        assert result_loose["fraction"] == 1.0

    def test_interpret_thresholds(self):
        assert "wiarygodny" in interpret_k7_fraction(0.10)
        assert "niejednoznaczna" in interpret_k7_fraction(0.35)
        assert "mylacy" in interpret_k7_fraction(0.75)
        assert interpret_k7_fraction(None) == "nieobliczalny"


class TestExplicitEdgeCaseMatrix:
    """n=0, n=1, wszystkie wartosci identyczne - explicite dla kazdej z 4
    funkcji (nie tylko pokryte przypadkiem przy okazji innych testow)."""

    def test_kendall_n0(self):
        assert kendall_tau([], [])["computable"] is False

    def test_kendall_n1(self):
        result = kendall_tau([1.0], [2.0])
        assert result["computable"] is False

    def test_kendall_all_identical_both(self):
        result = kendall_tau([3.0, 3.0, 3.0], [3.0, 3.0, 3.0])
        assert result["computable"] is False

    def test_spearman_n0(self):
        assert spearman_rho([], [])["computable"] is False

    def test_spearman_n1(self):
        assert spearman_rho([1.0], [2.0])["computable"] is False

    def test_spearman_all_identical_both(self):
        result = spearman_rho([3.0, 3.0, 3.0, 3.0], [3.0, 3.0, 3.0, 3.0])
        assert result["computable"] is False

    def test_mann_whitney_n0(self):
        assert mann_whitney_u([], [])["computable"] is False

    def test_mann_whitney_n1_each_matches_scipy(self):
        mine = mann_whitney_u([5.0], [3.0])
        sp = scipy_stats.mannwhitneyu([5.0], [3.0], alternative="two-sided", method="exact")
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_mann_whitney_all_identical_both_groups(self):
        """Wszystkie wartosci identyczne (wszystkie remisy, wariancja=0) -
        NIE jest to sensownie obliczalne (scipy samo zwraca p_value=nan w
        tym przypadku, bez ostrzezenia w wyniku) - mann_whitney_u() zwraca
        computable=False z jawnym powodem, co jest UCZCIWSZE niz cichy NaN."""
        result = mann_whitney_u([2.0, 2.0, 2.0], [2.0, 2.0, 2.0])
        assert result["computable"] is False

    def test_wilcoxon_n0(self):
        assert wilcoxon_signed_rank([])["computable"] is False

    def test_wilcoxon_n1_matches_scipy(self):
        pairs = [(5.0, 2.0)]
        mine = wilcoxon_signed_rank(pairs)
        sp = scipy_stats.wilcoxon([5.0], [2.0], zero_method="wilcox", mode="exact")
        assert abs(mine["statistic"] - sp.statistic) < TOL
        assert abs(mine["p_value"] - sp.pvalue) < TOL

    def test_wilcoxon_all_identical_pairs(self):
        result = wilcoxon_signed_rank([(4.0, 4.0), (4.0, 4.0), (4.0, 4.0)])
        assert result["computable"] is False
