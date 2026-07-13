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
    """SPRINT_v0.9.md P6 Kroki 4-5: profil minimalny = wylacznie ci95_valid=True.

    SPRINT_v0.10.md P4: liczba/skladnik osi NIE jest juz wpisana na sztywno
    tutaj - re-liczona niezaleznie od surowych c["genomes"][g]["ci95_valid"],
    zeby test rzeczywiscie sprawdzal profil, a nie powtarzal go (i zeby nie
    trzeba bylo edytowac testu za kazdym razem, gdy realne dane sie zmienia,
    tak jak sie zmienily miedzy P2 a P3 przez Read-Only Observer)."""

    def _expected_valid_concepts(self, profile):
        expected = set()
        for c in profile["concepts"]:
            if c["status"] != "measured":
                continue
            genome_keys = list(c["genomes"].keys())
            if genome_keys and all(c["genomes"][g]["ci95_valid"] is True for g in genome_keys):
                expected.add(c["concept"])
        return expected

    def test_minimal_profile_axes_match_concepts_with_valid_ci95_for_every_present_genome(self):
        profile = build_competency_profile()
        expected = self._expected_valid_concepts(profile)
        assert set(profile["minimal_profile"]["axes"]) == expected
        assert profile["summary"]["valid_ci95"] == len(expected)
        assert len(profile["minimal_profile"]["axes"]) == len(expected)

    def test_adaptation_and_stability_are_no_longer_degenerate(self):
        """SPRINT_v0.10.md P3/P4: Read-Only Observer da realne snapshoty ->
        Adaptation/Stability (zasilane z L1.1) maja teraz ci95_valid=True dla
        obu genomow i NIE MOGA zostac w koszyku degenerate (byly tam do P2,
        gdy snapshoty byly zawsze puste - patrz RAPORT_v0.9.md)."""
        profile = build_competency_profile()
        degenerate_names = {c["concept"] for c in profile["full_profile"]["degenerate"]}
        valid_names = {c["concept"] for c in profile["full_profile"]["valid"]}
        assert "Adaptation" not in degenerate_names
        assert "Stability" not in degenerate_names
        assert "Adaptation" in valid_names
        assert "Stability" in valid_names

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

    def test_degenerate_concepts_have_at_least_one_invalid_genome(self):
        """Niezmiennik definicyjny stanu 'degenerate': zmierzone, ale co
        najmniej jeden OBECNY genom ma ci95_valid=False. Nie zaklada KTORE
        pojecia tam sa (to wynika z danych, patrz docstring klasy) -
        pozwala kolekcji byc pusta, jesli aktualnie nic nie jest zdegenerowane."""
        profile = build_competency_profile()
        for c in profile["full_profile"]["degenerate"]:
            genome_keys = list(c["genomes"].keys())
            assert genome_keys, c["concept"]
            assert any(c["genomes"][g]["ci95_valid"] is False for g in genome_keys), c["concept"]

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
