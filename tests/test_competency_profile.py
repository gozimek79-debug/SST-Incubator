"""Testy Competency Profile (SPRINT_v0.8.4.md P4.3; profil minimalny:
SPRINT_v0.9.md P6, Kroki 4-5).

Sprawdzaja, ze profil zawiera wszystkie 14 pojec z cognitive_ontology.md,
ze pojecia insufficient_data nie przeciekaja zadna wartoscia liczbowa, oraz
ze profil minimalny (WYLACZNIE ci95_valid=True) i profil pelny (wszystko,
w tym zdegenerowane/insufficient_data jako osobne kategorie) sa spojne.
"""

from clos_scientist.competency_profile import (
    build_competency_profile,
    render_markdown,
    write_competency_profile,
)


class TestCompetencyProfileContents:
    def test_profile_has_all_14_concepts(self):
        profile = build_competency_profile()
        assert profile["summary"]["total_concepts"] == 14
        assert len(profile["concepts"]) == 14

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
        assert measured + insufficient == 14


class TestGenomeCards:
    def test_genome_cards_have_all_14_concepts_per_genome(self):
        profile = build_competency_profile()
        for genome, card in profile["genome_cards"].items():
            assert len(card) == 14
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


class TestMinimalProfile:
    """SPRINT_v0.9.md P6 Kroki 4-5: profil minimalny = wylacznie ci95_valid=True."""

    def test_minimal_profile_has_exactly_5_axes(self):
        profile = build_competency_profile()
        assert profile["summary"]["valid_ci95"] == 5
        assert len(profile["minimal_profile"]["axes"]) == 5
        assert set(profile["minimal_profile"]["axes"]) == {
            "Working Memory", "Pattern Recognition", "Pattern Retention",
            "Energy Efficiency", "Homeostatic Resilience",
        }

    def test_minimal_profile_concepts_all_have_valid_ci95_for_every_present_genome(self):
        profile = build_competency_profile()
        for c in profile["minimal_profile"]["concepts"]:
            assert c["genomes"], c["concept"]
            for genome, stats in c["genomes"].items():
                assert stats["ci95_valid"] is True, f"{c['concept']}/{genome}"

    def test_full_profile_partitions_all_concepts_into_valid_degenerate_insufficient(self):
        profile = build_competency_profile()
        full = profile["full_profile"]
        all_names = (
            {c["concept"] for c in full["valid"]}
            | {c["concept"] for c in full["degenerate"]}
            | {c["concept"] for c in full["insufficient_data"]}
        )
        assert all_names == {c["concept"] for c in profile["concepts"]}
        assert (
            len(full["valid"]) + len(full["degenerate"]) + len(full["insufficient_data"])
            == len(profile["concepts"])
        ), "kategorie musza byc rozlaczne i wyczerpujace (partycja)"

    def test_degenerate_concepts_are_adaptation_and_stability(self):
        profile = build_competency_profile()
        degenerate_names = {c["concept"] for c in profile["full_profile"]["degenerate"]}
        assert degenerate_names == {"Adaptation", "Stability"}

    def test_minimal_profile_axes_subset_of_full_profile_valid(self):
        profile = build_competency_profile()
        minimal_names = set(profile["minimal_profile"]["axes"])
        full_valid_names = {c["concept"] for c in profile["full_profile"]["valid"]}
        assert minimal_names == full_valid_names


class TestWriteArtifacts:
    def test_write_competency_profile_creates_json_and_md(self, tmp_path):
        paths = write_competency_profile(output_dir=tmp_path)
        assert paths["json"].exists()
        assert paths["md"].exists()
