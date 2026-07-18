"""Testy Capability Analyzer (SPRINT_v0.8.4.md, Priorytet 4.2).

Sprawdzaja uczciwosc mapowania pojec z cognitive_ontology.md na endpointy
lekcji: pojecie bez lekcji nie moze dostac wartosci liczbowej, a pojecie
z lekcja (Working Memory <- L1.1) musi dostac realna, zweryfikowana wartosc.
"""

from clos_scientist.capability_analyzer import (
    CONCEPT_METRIC_MAP,
    build_capability_profile,
)


class TestInsufficientData:
    """Pojecia bez lekcji musza byc oznaczone insufficient_data, bez wartosci."""

    def test_concept_without_lesson_has_insufficient_data_status(self):
        profile = build_capability_profile()
        by_concept = {c["concept"]: c for c in profile}

        for concept, mapping in CONCEPT_METRIC_MAP.items():
            if mapping is None:
                record = by_concept[concept]
                assert record["status"] == "insufficient_data", concept
                assert record["genomes"] == {}, f"{concept}: nie moze miec wartosci liczbowych"
                assert record["genome_comparison"] is None, concept

    def test_exploration_has_no_numeric_value(self):
        profile = build_capability_profile()
        exploration = next(c for c in profile if c["concept"] == "Exploration")
        assert exploration["status"] == "insufficient_data"
        assert exploration["source_lesson"] is None
        assert exploration["genomes"] == {}

    def test_all_concepts_present_and_match_ontology_names(self):
        profile = build_capability_profile()
        concepts = {c["concept"] for c in profile}
        expected = {
            "Perception", "Attention", "Pattern Recognition", "Pattern Retention",
            "Working Memory", "Long-term Memory", "Prediction", "Adaptation",
            "Exploration", "Generalization", "Planning", "Stability",
            "Final Energy Level", "Homeostatic Resilience",  # SPRINT_v0.11.0.md P1: bylo "Energy Efficiency"
        }
        assert concepts == expected


class TestWorkingMemoryFromL11:
    """Working Memory musi dostac wartosc z L1.1 (primary endpoint)."""

    def test_working_memory_measured_from_l1_1(self):
        profile = build_capability_profile()
        wm = next(c for c in profile if c["concept"] == "Working Memory")

        assert wm["status"] == "measured"
        assert wm["source_lesson"] == "L1.1"
        assert "default" in wm["genomes"]
        assert "highly_plastic" in wm["genomes"]

        for genome_stats in wm["genomes"].values():
            assert isinstance(genome_stats["value"], float)
            assert genome_stats["n_effective"] >= 2
            assert genome_stats["ci95_valid"] is True

    def test_working_memory_value_matches_report(self):
        import json
        from pathlib import Path

        with open("reports/academy/L1_1_pattern_echo.json", encoding="utf-8") as f:
            report = json.load(f)

        profile = build_capability_profile()
        wm = next(c for c in profile if c["concept"] == "Working Memory")

        for genome in ("default", "highly_plastic"):
            expected_mean = report["per_genome"][genome]["experimental_stats"]["mean"]
            assert wm["genomes"][genome]["value"] == expected_mean

    def test_working_memory_genome_comparison_uses_cohens_d(self):
        profile = build_capability_profile()
        wm = next(c for c in profile if c["concept"] == "Working Memory")

        comparison = wm["genome_comparison"]
        assert comparison is not None
        assert comparison["computable"] is True
        assert isinstance(comparison["cohens_d"], float)
        assert isinstance(comparison["mean_diff"], float)


class TestHomeostaticResilienceFromL12:
    """Homeostatic Resilience (SPRINT_v0.9.md P6) - N:M refaktor, zasilane z L1.2."""

    def test_default_measured_highly_plastic_absent(self):
        profile = build_capability_profile()
        hr = next(c for c in profile if c["concept"] == "Homeostatic Resilience")

        assert hr["status"] == "measured"
        assert hr["source_lesson"] == "L1.2"
        assert hr["source_lessons"] == ["L1.2"]
        assert "default" in hr["genomes"]
        assert hr["genomes"]["default"]["ci95_valid"] is True
        assert "highly_plastic" not in hr["genomes"], (
            "highly_plastic w L1.2 jest w 100% ocenzurowany - bez wartosci"
        )

    def test_genome_comparison_not_computable_when_one_genome_censored(self):
        profile = build_capability_profile()
        hr = next(c for c in profile if c["concept"] == "Homeostatic Resilience")
        assert hr["genome_comparison"] is None, (
            "Cohen's d nieobliczalny (highly_plastic bez danych) - jawny None, nie 0.0"
        )


class TestConceptMetricMapIsNtoM:
    """Architektura N:M (SPRINT_v0.9.md P6, Odkrycie #1 opcja 2)."""

    def test_mappings_are_lists_not_single_dicts(self):
        for concept, mappings in CONCEPT_METRIC_MAP.items():
            assert mappings is None or isinstance(mappings, list), (
                f"{concept}: CONCEPT_METRIC_MAP musi mapowac na liste lekcji (N:M), nie pojedynczy dict"
            )

    def test_protected_l1_1_concepts_unchanged_by_refactor(self):
        """Regresja krytyczna: pojecia zasilane WYLACZNIE z L1.1 musza dawac
        te same wartosci co przed wprowadzeniem relacji N:M (SPRINT_v0.9.md P6)."""
        import json
        from clos_curriculum.laboratory.statistics import compute_ci95

        profile = build_capability_profile()
        by_concept = {c["concept"]: c for c in profile}

        with open("reports/academy/L1_1_pattern_echo.json", encoding="utf-8") as f:
            l11_report = json.load(f)

        checks = {
            "Pattern Recognition": "mae_stimulus_phase",  # SPRINT_v0.11.0.md P1: bylo mse_stimulus_phase
            "Pattern Retention": "memory_decay_rate",
            "Final Energy Level": "final_energy",  # SPRINT_v0.11.0.md P1: bylo "Energy Efficiency"
        }
        for concept, field in checks.items():
            record = by_concept[concept]
            assert record["source_lesson"] == "L1.1"
            for genome in ("default", "highly_plastic"):
                raw = [r[field] for r in l11_report["results"]
                       if r["genome"] == genome and r["scenario"] == l11_report["scenario"]]
                expected_mean = compute_ci95(raw)["mean"]
                assert record["genomes"][genome]["value"] == expected_mean, concept


class TestPoolFalseNonPoolingRule:
    """SPRINT_v0.10.md P4: mapping z "pool": False (Adaptation <- L1.2) nie
    moze wplynac na oficjalna wartosc pojecia, tylko trafic do
    secondary_observations, jawnie oznaczona."""

    def test_adaptation_official_value_sourced_only_from_l1_1(self):
        profile = build_capability_profile()
        adapt = next(c for c in profile if c["concept"] == "Adaptation")
        assert adapt["source_lesson"] == "L1.1"
        assert adapt["source_lessons"] == ["L1.1"]

    def test_adaptation_l1_2_appears_only_as_secondary_observation(self):
        profile = build_capability_profile()
        adapt = next(c for c in profile if c["concept"] == "Adaptation")
        assert len(adapt["secondary_observations"]) == 1
        obs = adapt["secondary_observations"][0]
        assert obs["lesson"] == "L1.2"
        assert obs["pooled"] is False
        assert obs["note"]
        for genome in ("default", "highly_plastic"):
            assert obs["genomes"][genome]["deterministic"] is True
            assert obs["genomes"][genome]["ci95_valid"] is False
            assert obs["genomes"][genome]["value"] == 10.0

    def test_adaptation_pooled_stats_match_l1_1_only_ci95(self):
        """Regresja: dodanie L1.2 jako pool=False nie zmienia ANI JEDNEJ
        liczby w oficjalnym CI95 Adaptation wzgledem liczenia z samego L1.1."""
        import json
        from clos_curriculum.laboratory.statistics import compute_ci95

        with open("reports/academy/L1_1_pattern_echo.json", encoding="utf-8") as f:
            l11_report = json.load(f)

        profile = build_capability_profile()
        adapt = next(c for c in profile if c["concept"] == "Adaptation")

        for genome in ("default", "highly_plastic"):
            raw = [r["adaptation_tick"] for r in l11_report["results"]
                   if r["genome"] == genome and r["scenario"] == l11_report["scenario"]]
            expected = compute_ci95(raw)
            assert adapt["genomes"][genome]["value"] == expected["mean"]
            assert adapt["genomes"][genome]["n_effective"] == expected["n_effective"]
            assert adapt["genomes"][genome]["ci95_valid"] == expected["ci95_valid"]

    def test_concepts_without_secondary_observations_have_empty_list(self):
        profile = build_capability_profile()
        wm = next(c for c in profile if c["concept"] == "Working Memory")
        assert wm["secondary_observations"] == []


class TestNoProseInOutput:
    """Zero interpretacji/ocen slownych - tylko liczby i status."""

    def test_no_interpretation_field_in_output(self):
        profile = build_capability_profile()
        for record in profile:
            assert "interpretation" not in record
            for genome_stats in record["genomes"].values():
                assert "interpretation" not in genome_stats
