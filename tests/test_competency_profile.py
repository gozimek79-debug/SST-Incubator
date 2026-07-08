"""Testy Competency Profile (SPRINT_v0.8.4.md, Priorytet 4.3).

Sprawdzaja, ze profil zawiera wszystkie 13 pojec z cognitive_ontology.md
i ze pojecia insufficient_data nie przeciekaja zadna wartoscia liczbowa.
"""

from clos_scientist.competency_profile import (
    build_competency_profile,
    render_markdown,
    write_competency_profile,
)


class TestCompetencyProfileContents:
    def test_profile_has_all_13_concepts(self):
        profile = build_competency_profile()
        assert profile["summary"]["total_concepts"] == 13
        assert len(profile["concepts"]) == 13

    def test_insufficient_data_concepts_have_no_numeric_value(self):
        profile = build_competency_profile()
        for c in profile["concepts"]:
            if c["status"] == "insufficient_data":
                assert c["genomes"] == {}
                assert c["genome_comparison"] is None

    def test_summary_counts_match_concepts(self):
        profile = build_competency_profile()
        measured = sum(1 for c in profile["concepts"] if c["status"] == "measured")
        insufficient = sum(1 for c in profile["concepts"] if c["status"] == "insufficient_data")
        assert profile["summary"]["measured"] == measured
        assert profile["summary"]["insufficient_data"] == insufficient
        assert measured + insufficient == 13


class TestGenomeCards:
    def test_genome_cards_have_all_13_concepts_per_genome(self):
        profile = build_competency_profile()
        for genome, card in profile["genome_cards"].items():
            assert len(card) == 13
            assert {entry["concept"] for entry in card} == {
                c["concept"] for c in profile["concepts"]
            }

    def test_insufficient_data_genome_card_entry_has_no_value_key(self):
        profile = build_competency_profile()
        for card in profile["genome_cards"].values():
            for entry in card:
                if entry["status"] == "insufficient_data":
                    assert "value" not in entry
                    assert "ci95_low" not in entry


class TestMarkdownRendering:
    def test_markdown_contains_measured_summary_line(self):
        profile = build_competency_profile()
        md = render_markdown(profile)
        expected = f"Measured: {profile['summary']['measured']}/{profile['summary']['total_concepts']}"
        assert expected in md

    def test_markdown_contains_all_concept_names(self):
        profile = build_competency_profile()
        md = render_markdown(profile)
        for c in profile["concepts"]:
            assert c["concept"] in md


class TestWriteArtifacts:
    def test_write_competency_profile_creates_json_and_md(self, tmp_path):
        paths = write_competency_profile(output_dir=tmp_path)
        assert paths["json"].exists()
        assert paths["md"].exists()
