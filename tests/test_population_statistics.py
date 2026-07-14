"""SPRINT_v0.10.1.md P1/P3: Welch's t-test + BH-FDR (clos_curriculum/laboratory/
statistics.py) i generator populacji LHS (clos_curriculum/laboratory/population.py).

Weryfikuje: (1) wlasna implementacja funkcji beta niezupelnej daje wyniki
zgodne ze znanymi wartosciami krytycznymi rozkladu t-Studenta (brak scipy w
requirements.txt - to NIE jest przyblizenie, patrz statistics.py docstring);
(2) generator populacji jest deterministyczny, w granicach z prerejestracji,
i NIGDY nie probkuje prediction_depth/attention_threshold/meta_cognition_sensitivity
(SPRINT_v0.10.1.md P3, wymog #2)."""

import pytest

from clos_curriculum.laboratory.statistics import welch_t_test, benjamini_hochberg
from clos_curriculum.laboratory.population import (
    generate_population, DIMENSIONS, POPULATION_SAMPLING_SEED, N_NEW_GENOMES,
)

HELD_FIXED_FIELDS = {"prediction_depth", "attention_threshold", "meta_cognition_sensitivity"}
SAMPLED_FIELDS = {"plasticity", "learning_rate", "decay_rate", "homeostasis_target", "memory_capacity"}


class TestWelchTTest:
    def test_matches_known_critical_t_value(self):
        """t=2.228, df=10 jest tablicowa wartoscia krytyczna dla alpha=0.05
        dwustronne (standardowe tablice t-Studenta) - nasza implementacja
        (funkcja beta niezupelna, bez scipy) musi dac p bliskie 0.05."""
        from clos_curriculum.laboratory.statistics import _student_t_two_tailed_p
        p = _student_t_two_tailed_p(2.228, 10)
        assert abs(p - 0.05) < 0.001

    def test_large_df_matches_normal_approximation(self):
        from clos_curriculum.laboratory.statistics import _student_t_two_tailed_p
        p = _student_t_two_tailed_p(1.96, 1_000_000)
        assert abs(p - 0.05) < 0.001

    def test_identical_groups_give_p_close_to_1(self):
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = welch_t_test(a, list(a))
        assert result["computable"] is True
        assert result["t"] == 0.0
        assert result["p_value"] == 1.0

    def test_clearly_different_groups_give_tiny_p(self):
        a = [1, 2, 3, 4, 5]
        b = [100, 101, 102, 103, 104]
        result = welch_t_test(a, b)
        assert result["computable"] is True
        assert result["p_value"] < 0.001

    def test_insufficient_n_not_computable(self):
        result = welch_t_test([1.0], [1.0, 2.0, 3.0])
        assert result["computable"] is False

    def test_both_zero_variance_not_computable(self):
        result = welch_t_test([5.0, 5.0, 5.0], [5.0, 5.0, 5.0])
        assert result["computable"] is False


class TestBenjaminiHochberg:
    def test_empty_input(self):
        assert benjamini_hochberg([]) == []

    def test_all_large_p_values_none_significant(self):
        result = benjamini_hochberg([0.3, 0.4, 0.5, 0.6, 0.7], q=0.05)
        assert result == [False] * 5

    def test_mix_of_real_and_noise_signals(self):
        """3 genuinely male p-values (sygnal) + 7 duzych (szum) - FDR musi
        wylapac dokladnie sygnal, nie wiecej, nie mniej, w tym syntetycznym
        przypadku bez dwuznacznosci."""
        pvals = [0.001, 0.002, 0.003, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        result = benjamini_hochberg(pvals, q=0.05)
        assert result == [True, True, True] + [False] * 7

    def test_more_conservative_than_uncorrected_alpha(self):
        """Korekta MUSI byc co najmniej tak konserwatywna jak brak korekty -
        zbior istotnych PO BH nie moze byc wiekszy niz zbior z surowym p<q."""
        pvals = [0.001, 0.01, 0.03, 0.04, 0.045, 0.049, 0.06, 0.1]
        raw_significant = [p < 0.05 for p in pvals]
        corrected = benjamini_hochberg(pvals, q=0.05)
        for raw, corr in zip(raw_significant, corrected):
            if corr:
                assert raw, "BH nie moze oznaczyc jako istotne czegos, co nie bylo istotne nawet bez korekty"


class TestPopulationGenerator:
    def test_returns_23_genomes(self):
        population = generate_population()
        assert len(population) == 23
        assert sum(1 for g in population if g["kind"] == "lhs") == N_NEW_GENOMES
        assert sum(1 for g in population if g["kind"] == "anchor") == 3

    def test_deterministic_given_seed(self):
        pop_a = generate_population(seed=POPULATION_SAMPLING_SEED)
        pop_b = generate_population(seed=POPULATION_SAMPLING_SEED)
        assert pop_a == pop_b

    def test_different_seed_gives_different_sample(self):
        pop_a = generate_population(seed=POPULATION_SAMPLING_SEED)
        pop_b = generate_population(seed=POPULATION_SAMPLING_SEED + 1)
        lhs_a = [g["genome_params"] for g in pop_a if g["kind"] == "lhs"]
        lhs_b = [g["genome_params"] for g in pop_b if g["kind"] == "lhs"]
        assert lhs_a != lhs_b

    def test_lhs_genomes_within_declared_bounds(self):
        population = generate_population()
        bounds = {name: (lo, hi) for name, lo, hi, _ in DIMENSIONS}
        for g in population:
            if g["kind"] != "lhs":
                continue
            for field, (lo, hi) in bounds.items():
                value = g["genome_params"][field]
                assert lo <= value <= hi, f"{g['genome_id']}.{field}={value} poza [{lo},{hi}]"

    def test_memory_capacity_is_integer(self):
        population = generate_population()
        for g in population:
            if g["kind"] == "lhs":
                assert isinstance(g["genome_params"]["memory_capacity"], int)

    def test_anchor_genomes_have_no_params_override(self):
        """Anchor (default/minimal/highly_plastic) uzywaja WYLACZNIE istniejacego
        mechanizmu presetow - genome_params=None, zero nowego kodu na tej sciezce."""
        population = generate_population()
        anchors = [g for g in population if g["kind"] == "anchor"]
        assert {g["genome_id"] for g in anchors} == {"default", "minimal", "highly_plastic"}
        for g in anchors:
            assert g["genome_params"] is None
            assert g["genome_preset"] == g["genome_id"]

    def test_lhs_genome_params_never_include_held_fixed_fields(self):
        """SPRINT_v0.10.1.md P3 wymog #2: prediction_depth/attention_threshold/
        meta_cognition_sensitivity NIGDY nie sa czescia genome_params - musza
        pozostac na wartosci domyslnej BrainTissue (3, 0.3, 0.5) dla KAZDEGO
        z 23 genomow, nie tylko "nie losowane losowo"."""
        population = generate_population()
        for g in population:
            if g["genome_params"] is None:
                continue
            assert set(g["genome_params"].keys()) == SAMPLED_FIELDS
            assert not (set(g["genome_params"].keys()) & HELD_FIXED_FIELDS)

    def test_lhs_genome_ids_are_unique(self):
        population = generate_population()
        ids = [g["genome_id"] for g in population]
        assert len(ids) == len(set(ids))
