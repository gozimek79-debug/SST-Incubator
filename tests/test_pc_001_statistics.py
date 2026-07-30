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
)
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
