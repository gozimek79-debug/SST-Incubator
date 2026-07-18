"""SPRINT_v0.11.0.md P0: analiza mocy statystycznej (BRAMKA).

Weryfikuje wlasna implementacje mocy dwuprobkowego testu t (bez scipy)
wprost przeciwko klasycznym, podrecznikowym tablicom mocy Cohena (1988) -
trzy niezalezne punkty odniesienia, szeroko cytowane, latwe do zweryfikowania
w dowolnym podreczniku statystyki:
  - n=64/grupe, d=0.5 (efekt sredni), alpha=.05 dwustronne -> moc ~ 0.80
  - n=26/grupe, d=0.8 (efekt duzy), alpha=.05 dwustronne -> moc ~ 0.80
  - n=393/grupe, d=0.2 (efekt maly), alpha=.05 dwustronne -> moc ~ 0.80
"""

import pytest

from clos_curriculum.laboratory.statistics import (
    power_two_sample_t_test,
    minimum_detectable_effect,
    power_anova,
    cohens_f_anova,
)


class TestPowerMatchesCohenTables:
    def test_medium_effect_n64(self):
        power = power_two_sample_t_test(d=0.5, n=64, alpha=0.05)
        assert abs(power - 0.80) < 0.01

    def test_large_effect_n26(self):
        power = power_two_sample_t_test(d=0.8, n=26, alpha=0.05)
        assert abs(power - 0.80) < 0.01

    def test_small_effect_n393(self):
        power = power_two_sample_t_test(d=0.2, n=393, alpha=0.05)
        assert abs(power - 0.80) < 0.01


class TestPowerMonotonicity:
    def test_power_increases_with_effect_size(self):
        n = 30
        powers = [power_two_sample_t_test(d, n, alpha=0.05) for d in (0.1, 0.3, 0.5, 0.8, 1.2)]
        assert powers == sorted(powers)

    def test_power_increases_with_sample_size(self):
        d = 0.5
        powers = [power_two_sample_t_test(d, n, alpha=0.05) for n in (5, 10, 20, 50, 100)]
        assert powers == sorted(powers)

    def test_power_decreases_with_stricter_alpha(self):
        d, n = 0.8, 30
        power_loose = power_two_sample_t_test(d, n, alpha=0.05)
        power_strict = power_two_sample_t_test(d, n, alpha=0.05 / 253)
        assert power_strict < power_loose

    def test_zero_effect_gives_power_equal_alpha(self):
        """Przy d=0 moc = prawdopodobienstwo falszywego odrzucenia = alpha."""
        power = power_two_sample_t_test(d=0.0, n=30, alpha=0.05)
        assert abs(power - 0.05) < 0.01


class TestMinimumDetectableEffect:
    def test_round_trip_matches_power_function(self):
        """d wyznaczone przez minimum_detectable_effect(n, alpha) MUSI dawac
        moc ~0.8 gdy wstawione z powrotem do power_two_sample_t_test."""
        for n, alpha in [(10, 0.05), (30, 0.05), (10, 0.05 / 253), (30, 0.05 / 253)]:
            d = minimum_detectable_effect(n, alpha, target_power=0.8)
            power = power_two_sample_t_test(d, n, alpha)
            assert abs(power - 0.8) < 0.005

    def test_current_design_n10_is_severely_underpowered(self):
        """SPRINT_v0.11.0.md P0, odkrycie: przy n=10/genom (projekt v0.10.1) i
        korekcie rownowaznej Bonferroniemu na 253 pary, wykrywalny jest tylko
        OGROMNY efekt (d>2) - znacznie powyzej konwencjonalnego 'duzego'
        efektu Cohena (d=0.8)."""
        d_uncorrected = minimum_detectable_effect(n=10, alpha=0.05)
        d_bonferroni = minimum_detectable_effect(n=10, alpha=0.05 / 253)
        assert d_uncorrected > 1.0
        assert d_bonferroni > 2.0

    def test_proposed_n30_still_requires_large_effect_after_correction(self):
        """Nawet przy n=30 (proponowany re-run), korekta na 253 pary wymaga
        d>1 (duzy-do-bardzo-duzego efekt) - re-run poprawia moc, ale nie
        rozwiazuje problemu w pelni; to fakt do zaraportowania, nie do ukrycia."""
        d_bonferroni_n30 = minimum_detectable_effect(n=30, alpha=0.05 / 253)
        assert 1.0 < d_bonferroni_n30 < 2.0

    def test_larger_n_needs_smaller_detectable_effect(self):
        d_n10 = minimum_detectable_effect(n=10, alpha=0.05)
        d_n30 = minimum_detectable_effect(n=30, alpha=0.05)
        assert d_n30 < d_n10


class TestAnovaPowerMatchesTwoSampleTTest:
    """Dla k=2 grup, ANOVA F-test == t-test^2 (f=d/2) - relacja podrecznikowa.
    To jest niezalezna weryfikacja _noncentral_f_cdf/power_anova wobec juz
    zwalidowanego (przeciwko tablicom Cohena) power_two_sample_t_test."""

    @pytest.mark.parametrize("d,n", [(0.5, 64), (0.8, 26), (0.2, 393), (0.985, 10), (0.985, 46)])
    def test_k2_matches_t_test(self, d, n):
        power_t = power_two_sample_t_test(d, n, alpha=0.05)
        power_f = power_anova(d / 2, k=2, n=n, alpha=0.05)
        assert abs(power_t - power_f) < 1e-3


class TestAnovaPowerTables:
    def test_medium_large_effect_k3(self):
        """Cohen (1988), przyblizony punkt: k=3, f=0.4, n=20/grupe -> moc ~ 0.78-0.83."""
        power = power_anova(0.4, k=3, n=20, alpha=0.05)
        assert 0.75 < power < 0.85

    def test_medium_large_effect_k4(self):
        power = power_anova(0.4, k=4, n=18, alpha=0.05)
        assert 0.75 < power < 0.85


class TestCohensFFromGroupStats:
    def test_matches_manual_calculation(self):
        """3 grupy latwe do przeliczenia recznie."""
        means = [1.0, 2.0, 3.0]
        stds = [0.5, 0.5, 0.5]
        ns = [10, 10, 10]
        result = cohens_f_anova(means, stds, ns)
        assert result["computable"] is True
        grand_mean = 2.0
        sd_between = ((1.0 - grand_mean) ** 2 + (2.0 - grand_mean) ** 2 + (3.0 - grand_mean) ** 2) / 3
        import math
        assert abs(result["sd_between"] - math.sqrt(sd_between)) < 1e-6
        assert abs(result["sd_within"] - 0.5) < 1e-6

    def test_working_memory_matches_auditor_f(self):
        """SPRINT_v0.11.0.md P0 (audyt): Working Memory (L1.1/noise_world, 23
        genomow) ma f_obs~0.265 wg niezaleznego przeliczenia audytora."""
        import json
        with open("reports/population/population_validation_v0_10_1.json", encoding="utf-8") as f:
            r = json.load(f)
        pg = r["lessons"]["L1.1"]["noise_world"]["Working Memory (MSE@50)"]["per_genome"]
        means = [g["mean"] for g in pg.values()]
        stds = [g["std"] for g in pg.values()]
        ns = [g["n_available"] for g in pg.values()]
        result = cohens_f_anova(means, stds, ns)
        assert result["computable"] is True
        assert abs(result["f"] - 0.265) < 0.01

    def test_zero_within_variance_not_computable(self):
        result = cohens_f_anova([1.0, 2.0, 3.0], [0.0, 0.0, 0.0], [10, 10, 10])
        assert result["computable"] is False


class TestAnovaMultipleComparisonsCorrectionRequired:
    """SPRINT_v0.11.0.md P0, druga runda audytu: pierwsza wersja tej tabeli
    uzywala alpha=0.05 BEZ korekty na 21 rownoczesnych testow omnibusu (7
    metryk x 3 srodowiska) - dokladnie ten sam blad (raportowanie mocy bez
    korekty), ktory Design C mial pomoc uniknac. Ten test pilnuje, zeby ta
    konkretna pomylka nie wrocila cicho - zlote wartosci z rozstrzygnietej
    rozbieznosci (audytor, alpha=0.05/21)."""

    ALPHA_21 = 0.05 / 21

    def test_working_memory_power_matches_resolved_discrepancy(self):
        p10 = power_anova(0.265, k=23, n=10, alpha=self.ALPHA_21)
        p30 = power_anova(0.265, k=23, n=30, alpha=self.ALPHA_21)
        assert abs(p10 - 0.185) < 0.005
        assert abs(p30 - 0.952) < 0.005

    def test_working_memory_conservative_power_is_near_coin_flip(self):
        """Winner's curse: przy f_obs*0.7, moc@n=30 spada do ~0.457 - musi
        pozostac jawnie ponizej 0.8, inaczej ktos cicho zignorowal ostrzezenie."""
        p30_cons = power_anova(0.265 * 0.7, k=23, n=30, alpha=self.ALPHA_21)
        assert abs(p30_cons - 0.457) < 0.01
        assert p30_cons < 0.6

    def test_pattern_recognition_remains_underpowered_at_n30(self):
        """Pattern Recognition (f=0.130) NIE zostaje rozstrzygnieta przez
        re-run n=30 pod korekta na 21 testow - moc musi pozostac < 0.2."""
        p30 = power_anova(0.130, k=23, n=30, alpha=self.ALPHA_21)
        assert p30 < 0.2

    def test_uncorrected_alpha_would_overstate_power(self):
        """Regresja przeciwko dokladnie temu bledowi: alpha=0.05 (bez korekty)
        daje MOC WIEKSZA niz alpha=0.05/21 dla tego samego f/n/k - jesli te
        dwie wartosci kiedykolwiek wyjda rowne, korekta przestala dzialac."""
        p_uncorrected = power_anova(0.265, k=23, n=10, alpha=0.05)
        p_corrected = power_anova(0.265, k=23, n=10, alpha=self.ALPHA_21)
        assert p_uncorrected > p_corrected
        assert abs(p_uncorrected - 0.586) < 0.01
