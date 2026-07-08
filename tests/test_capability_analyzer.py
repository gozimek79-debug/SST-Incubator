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
            "Energy Efficiency",
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


class TestNoProseInOutput:
    """Zero interpretacji/ocen slownych - tylko liczby i status."""

    def test_no_interpretation_field_in_output(self):
        profile = build_capability_profile()
        for record in profile:
            assert "interpretation" not in record
            for genome_stats in record["genomes"].values():
                assert "interpretation" not in genome_stats
