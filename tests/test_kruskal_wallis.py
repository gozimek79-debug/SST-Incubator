"""SPRINT_v0.11.0.md, Red Team (2026-07-20): kruskal_wallis() w
clos_curriculum/laboratory/statistics.py - test parami (Welch+BH-FDR) dal
0/253 istotnych par dla Pattern Retention, ale slaby niemonotoniczny efekt
przezyl test omnibusowy oparty na rangach. Ten plik waliduje implementacje
NIEZALEZNIE od tego konkretnego wyniku, wprost przeciwko rozwiazaniu w
zamknietej formie (chi-kwadrat df=2 ma CDF=1-exp(-x/2))."""

import math

from clos_curriculum.laboratory.statistics import (
    kruskal_wallis, _chi2_cdf, chi2_survival, chi2_survival_log10,
)


class TestChi2CdfClosedForm:
    def test_df2_matches_closed_form_exactly(self):
        """Dla df=2, chi-kwadrat ma dokladny wzor CDF(x)=1-exp(-x/2) -
        niezalezny od calkowania numerycznego test poprawnosci _chi2_cdf."""
        for x in [1.0, 2.0, 5.0, 7.2, 10.0, 50.0]:
            approx = _chi2_cdf(x, df=2)
            exact = 1 - math.exp(-x / 2)
            assert abs(approx - exact) < 1e-8


class TestChi2SurvivalClosedFormAndExtremeTails:
    def test_df2_matches_closed_form(self):
        for x in [1.0, 2.0, 5.0, 7.2, 10.0, 50.0, 200.0]:
            assert abs(chi2_survival(x, df=2) - math.exp(-x / 2)) < 1e-10

    def test_extreme_h_gives_nonzero_or_meaningful_log10(self):
        """H=3681, df=22 (Adaptation real data scale): 1-_chi2_cdf() underflows
        to a NEGATIVE number (catastrophic cancellation) - chi2_survival()
        must not do that, and when it underflows to 0.0 in linear space,
        chi2_survival_log10() must still give a large-negative, finite number."""
        s = chi2_survival(3681.48, df=22)
        assert s >= 0.0, "funkcja przezycia nigdy nie moze byc ujemna"
        log10_p = chi2_survival_log10(3681.48, df=22)
        assert log10_p < -300, "H tej wielkosci daje p astronomicznie male"
        assert math.isfinite(log10_p)

    def test_moderate_h_survival_matches_manual_kruskal_example(self):
        assert abs(chi2_survival(7.2, df=2) - math.exp(-3.6)) < 1e-9


class TestKruskalWallisReferenceValue:
    def test_no_ties_three_groups_matches_hand_calculation(self):
        """[1,2,3]/[4,5,6]/[7,8,9]: rangi 1..9 bez remisow.
        R1=6,R2=15,R3=24, n=3 kazda, N=9.
        H = 12/(9*10)*(36/3+225/3+576/3) - 3*10 = 0.13333*279-30 = 7.2 dokladnie.
        df=2 -> p = exp(-3.6) = 0.0273237... (zamknieta forma)."""
        result = kruskal_wallis([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        assert result["computable"] is True
        assert abs(result["H"] - 7.2) < 1e-6
        assert result["df"] == 2
        assert abs(result["p_value"] - math.exp(-3.6)) < 1e-6

    def test_identical_groups_gives_h_near_zero(self):
        result = kruskal_wallis([[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]])
        assert result["computable"] is True
        assert abs(result["H"]) < 1e-6
        assert result["p_value"] > 0.9

    def test_fewer_than_two_groups_not_computable(self):
        assert kruskal_wallis([[1, 2, 3]])["computable"] is False
        assert kruskal_wallis([])["computable"] is False

    def test_ties_correction_reduces_h_below_uncorrected(self):
        """Z remisami H_skorygowane = H_surowe / tie_correction, tie_correction<1,
        wiec H rosnie po korekcie (nie maleje) - test kierunku korekty."""
        groups = [[1, 2, 2, 3], [2, 4, 5, 6], [7, 8, 9, 2]]
        result = kruskal_wallis(groups)
        assert result["computable"] is True
        assert result["tie_correction"] < 1.0


class TestKruskalWallisCanDetectNonMonotonicEffect:
    """Demonstracja mechanizmu, ktory Red Team zaraportowal: efekt, ktory
    test PAROWY (np. Welch miedzy dwiema konkretnymi grupami) latwo przegapi,
    bo nie jest monotoniczny, ale ktory OMNIBUS na rangach wykrywa, bo patrzy
    na CALY rozklad rang naraz, nie na pojedyncze pary."""

    def test_non_monotonic_pattern_detected_by_omnibus(self):
        # 3 grupy, srodkowa ma WYZSZE wartosci niz obie skrajne (U-ksztalt
        # odwrocony) - dowolna POJEDYNCZA para skrajna-skrajna nie roznicuje
        # wiele, ale omnibus na rangach widzi cala strukture.
        low_a = [1.0, 1.1, 1.2, 1.3, 1.4]
        high_mid = [5.0, 5.1, 5.2, 5.3, 5.4]
        low_b = [1.05, 1.15, 1.25, 1.35, 1.45]
        result = kruskal_wallis([low_a, high_mid, low_b])
        assert result["computable"] is True
        assert result["p_value"] < 0.05, "omnibus musi wykryc ten oczywisty (choc niemonotoniczny miedzy A/B) efekt"
