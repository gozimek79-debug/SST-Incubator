"""SPRINT_v0.11.0.md P0 (druga runda): matematyka sekwencyjna dla Wariantu B
(interim n=30 -> ewentualne rozszerzenie n=185).

Weryfikuje wlasna implementacje dwuwymiarowego rozkladu normalnego (bez
scipy) na przypadkach brzegowych ORAZ przeciwko niezaleznemu przeliczeniu
audytora: rho=sqrt(30/185)=0.4027, inflacja bledu I rodzaju bez korekty na
sekwencyjnosc = 1.9675x (alpha 0.05/21=0.00238 -> 0.004685 faktycznie).
"""

import math

import pytest

from clos_curriculum.laboratory.statistics import (
    _bivariate_normal_cdf,
    sequential_correlation,
    naive_two_look_type1_error,
    pocock_boundary,
)


class TestBivariateNormalCdfEdgeCases:
    def test_independence_rho_zero_factorizes(self):
        """rho=0: P(Z1<=h,Z2<=k) = P(Z1<=h)*P(Z2<=k)."""
        from clos_curriculum.laboratory.statistics import _std_normal_cdf
        h, k = 1.5, 0.8
        joint = _bivariate_normal_cdf(h, k, rho=0.0)
        product = _std_normal_cdf(h) * _std_normal_cdf(k)
        assert abs(joint - product) < 1e-3

    def test_perfect_correlation_collapses_to_minimum(self):
        """rho~1: P(Z1<=h,Z2<=k) = P(Z<=min(h,k)) (Z1=Z2 niemal na pewno)."""
        from clos_curriculum.laboratory.statistics import _std_normal_cdf
        h, k = 1.5, 0.8
        joint = _bivariate_normal_cdf(h, k, rho=0.999999)
        expected = _std_normal_cdf(min(h, k))
        assert abs(joint - expected) < 1e-3


class TestSequentialCorrelation:
    def test_matches_sqrt_information_fraction(self):
        rho = sequential_correlation(n_interim=30, n_final=185)
        assert abs(rho - 0.4027) < 0.001

    def test_equal_looks_give_rho_one(self):
        assert abs(sequential_correlation(100, 100) - 1.0) < 1e-9


class TestNaiveTwoLookInflation:
    """SPRINT_v0.11.0.md P0: dwa spojrzenia na skorelowane dane BEZ korekty
    INFLATUJA blad I rodzaju - zwalidowane przeciwko przeliczeniu audytora."""

    def test_matches_auditor_inflation_factor(self):
        rho = sequential_correlation(30, 185)
        result = naive_two_look_type1_error(alpha_per_look=0.05 / 21, rho=rho)
        assert abs(result["alpha_actual"] - 0.00466) < 0.0001
        assert abs(result["inflation_factor"] - 1.9675) < 0.01

    def test_zero_correlation_gives_near_double_alpha(self):
        """Testy niezalezne (rho=0): inflacja zbliza sie do ~2x (1-(1-a)^2/a),
        gorny teoretyczny limit inflacji dla dwoch testow."""
        result = naive_two_look_type1_error(alpha_per_look=0.05, rho=0.0)
        assert 1.9 < result["inflation_factor"] < 2.0

    def test_perfect_correlation_gives_no_inflation(self):
        """rho~1: oba spojrzenia daja (niemal) ten sam wynik - brak inflacji."""
        result = naive_two_look_type1_error(alpha_per_look=0.05, rho=0.999999)
        assert abs(result["inflation_factor"] - 1.0) < 0.01


class TestPocockBoundary:
    def test_boundary_stricter_than_single_look_critical_value(self):
        """Granica Pococka MUSI byc surowsza (wieksza) niz pojedynczy test na
        tym samym alpha - to jest cena za dwa spojrzenia."""
        from clos_curriculum.laboratory.statistics import _t_critical_value_normal_approx
        rho = sequential_correlation(30, 185)
        target_alpha = 0.05 / 21
        c_single = _t_critical_value_normal_approx(target_alpha)
        c_pocock = pocock_boundary(target_alpha, rho)
        assert c_pocock > c_single

    def test_boundary_achieves_target_alpha(self):
        rho = sequential_correlation(30, 185)
        target_alpha = 0.05 / 21
        c = pocock_boundary(target_alpha, rho)
        p_both_within = (_bivariate_normal_cdf(c, c, rho) - _bivariate_normal_cdf(-c, c, rho)
                         - _bivariate_normal_cdf(c, -c, rho) + _bivariate_normal_cdf(-c, -c, rho))
        alpha_achieved = 1 - p_both_within
        assert abs(alpha_achieved - target_alpha) < 0.0002
