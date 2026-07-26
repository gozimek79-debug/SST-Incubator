"""Testy Competency Profile (SPRINT_v0.8.4.md P4.3; profil minimalny:
SPRINT_v0.9.md P6, Kroki 4-5; re-run konfirmacyjny: SPRINT v0.11.0 P0,
CTO 2026-07-22).

Sprawdzaja, ze profil zawiera wszystkie 14 pojec z cognitive_ontology.md,
ze pojecia insufficient_data nie przeciekaja zadna wartoscia liczbowa, ze
profil minimalny (WYLACZNIE confirmatory_status=VALIDATED od SPRINT v0.11.0
P0) i profil pelny (wszystko, w tym zdegenerowane/insufficient_data jako
osobne kategorie) sa spojne, oraz ze dane pochodza z 23-genomowej populacji
konfirmacyjnej (population_validation_v0_11_0.json), nie z 2-genomowego demo.
"""

from clos_scientist.competency_profile import (
    ARCHIVE_JSON_NAME,
    ARCHIVE_MD_NAME,
    archive_exploratory_profile,
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
    """SPRINT v0.11.0 P0 (CTO 2026-07-22): profil zrodlem jest RE-RUN
    KONFIRMACYJNY (population_validation_v0_11_0.json, 23 genomy, n=185),
    nie demo Academy (2 genomy, n=10, SPRINT_v0.9.md P6). To zmienilo
    DEFINICJE, ktore ten test sprawdzal - 4 testy ponizej zaktualizowane z
    jawnym uzasadnieniem (nie tylko zeby "przeszly"):

    - full_profile.valid/degenerate to teraz odczyt pola JUZ POLICZONEGO w
      danych ("classification": GENOME-ROBUST/GENOME-FRAGILE, prog
      ci95_valid ORAZ n_effective>=5 - patrz docs/VALIDITY_REPORT.md), NIE
      rekonstrukcja z surowego ci95_valid per genom. Odkryte przy budowie:
      Adaptation ma ci95_valid=True dla WSZYSTKICH 23 genomow, ale
      classification=GENOME-FRAGILE (n_genomes_valid=13/23) - stary test
      zakladal "degenerate <=> co najmniej jeden ci95_valid=False", co jest
      FALSZYWE dla tych danych (prog jest n_effective, nie ci95_valid).
    - minimal_profile jest teraz na statusie KONFIRMACYJNYM (VALIDATED z
      docs/METRIC_STATUS_TABLE.md po Red Teamie), nie na ci95_valid/
      classification. "ROBUST" (pomiar wiarygodny) i "VALIDATED"
      (dyskryminuje genomy, przetrwalo Kruskal-Wallis+Red Team) to DWA
      ROZNE pytania (docs/VALIDITY_REPORT.md "Kluczowe odkrycie") - Pattern
      Retention i Final Energy Level sa ROBUST (w full_profile.valid) ale
      tylko EXPERIMENTAL, wiec minimal jest teraz WLASCIWY PODZBIOR
      full_profile.valid, nie rowny mu."""

    def _expected_robust_concepts(self, profile):
        """GENOME-ROBUST wg pola 'classification' juz policzonego w
        population_validation_v0_11_0.json - NIE rekonstruowane z surowego
        ci95_valid (patrz docstring klasy, blad zlapany 2026-07-22)."""
        return {
            c["concept"] for c in profile["concepts"]
            if c["status"] == "measured" and c.get("classification") == "GENOME-ROBUST"
        }

    def _expected_validated_concepts(self, profile):
        return {
            c["concept"] for c in profile["concepts"]
            if c.get("confirmatory_status") == "VALIDATED"
        }

    def test_full_profile_valid_matches_genome_robust_classification(self):
        profile = build_competency_profile()
        expected = self._expected_robust_concepts(profile)
        actual = {c["concept"] for c in profile["full_profile"]["valid"]}
        assert actual == expected
        assert profile["summary"]["valid_ci95"] == len(expected)

    def test_minimal_profile_axes_match_concepts_with_validated_confirmatory_status(self):
        profile = build_competency_profile()
        expected = self._expected_validated_concepts(profile)
        assert set(profile["minimal_profile"]["axes"]) == expected
        assert profile["summary"]["validated"] == len(expected)
        assert len(profile["minimal_profile"]["axes"]) == len(expected)

    def test_working_memory_pattern_recognition_stability_are_validated(self):
        """docs/METRIC_STATUS_TABLE.md po Red Teamie (2026-07-20): dokladnie
        te trzy osie (L1.1/noise_world) sa VALIDATED - potwierdzone
        niezaleznie Welch-pary+FDR ORAZ Kruskal-Wallis, leave-one-out
        odporny. Zastepuje dawny test_adaptation_and_stability_are_no_longer_degenerate
        (ktory sprawdzal INNE, juz nieaktualne pytanie - patrz nizej)."""
        profile = build_competency_profile()
        validated_names = set(profile["minimal_profile"]["axes"])
        assert {"Working Memory", "Pattern Recognition", "Stability"} == validated_names

    def test_adaptation_is_genome_fragile_not_a_regression(self):
        """SPRINT v0.11.0 P0: Adaptation ma classification=GENOME-FRAGILE
        na 23-genomowej populacji konfirmacyjnej (valid_rate~56.5%,
        n_genomes_valid=13/23) - TO NIE jest regresja naprawy Read-Only
        Observer z SPRINT_v0.10.md P3/P4 (snapshoty nadal SA realne,
        niepuste - to zupelnie inne pytanie). To jest legalne, nowe
        odkrycie NA POZIOMIE POPULACJI: przy n=10/2 genomy oba dostepne
        genomy akurat mialy ci95_valid=True; przy 23 genomach czesc ma za
        niskie n_effective, wiec Adaptation jest FRAGILE, nie ROBUST.
        Status konfirmacyjny (EXPERIMENTAL, przez Kruskal-Wallis, patrz
        docs/METRIC_STATUS_TABLE.md footnote 12) jest niezalezny od tego i
        NIE degraduje przez klasyfikacje FRAGILE."""
        profile = build_competency_profile()
        by_concept = {c["concept"]: c for c in profile["concepts"]}
        assert by_concept["Adaptation"]["classification"] == "GENOME-FRAGILE"
        assert by_concept["Adaptation"]["confirmatory_status"] == "EXPERIMENTAL"
        degenerate_names = {c["concept"] for c in profile["full_profile"]["degenerate"]}
        assert "Adaptation" in degenerate_names

    def test_stability_remains_genome_robust_and_validated(self):
        """Stability, w odroznieniu od Adaptation, pozostaje ROBUST (100%
        valid_rate na 23 genomach) I VALIDATED - SPRINT_v0.10.md P3/P4 nadal
        obowiazuje dla tej konkretnej osi."""
        profile = build_competency_profile()
        by_concept = {c["concept"]: c for c in profile["concepts"]}
        assert by_concept["Stability"]["classification"] == "GENOME-ROBUST"
        assert by_concept["Stability"]["confirmatory_status"] == "VALIDATED"
        valid_names = {c["concept"] for c in profile["full_profile"]["valid"]}
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

    def test_degenerate_concepts_are_genome_fragile(self):
        """Niezmiennik definicyjny stanu 'degenerate' PO PRZEJSCIU NA DANE
        POPULACYJNE (SPRINT v0.11.0 P0): classification=GENOME-FRAGILE, NIE
        "co najmniej jeden genom ci95_valid=False" (stary niezmiennik z
        SPRINT_v0.9.md - falszywy na tych danych, patrz docstring klasy:
        Adaptation ma ci95_valid=True wszedzie, a mimo to jest FRAGILE
        przez n_effective<5 dla wielu genomow)."""
        profile = build_competency_profile()
        for c in profile["full_profile"]["degenerate"]:
            assert c.get("classification") == "GENOME-FRAGILE", c["concept"]

    def test_minimal_profile_axes_subset_of_full_profile_valid(self):
        """VALIDATED implikuje ROBUST (musi byc wiarygodnie mierzalne, zeby
        w ogole moc dyskryminowac genomy) - ale NIE odwrotnie: Pattern
        Retention i Final Energy Level sa ROBUST (w full_profile.valid) a
        tylko EXPERIMENTAL, wiec minimal jest teraz WLASCIWYM podzbiorem,
        nie rownym mu (przed SPRINT v0.11.0 P0 byly rowne, bo minimal byl
        definiowany WPROST jako ci95_valid, czyli to samo co full_profile.valid)."""
        profile = build_competency_profile()
        minimal_names = set(profile["minimal_profile"]["axes"])
        full_valid_names = {c["concept"] for c in profile["full_profile"]["valid"]}
        assert minimal_names <= full_valid_names
        assert minimal_names < full_valid_names, (
            "oczekiwano WLASCIWEGO podzbioru na tych danych - Pattern Retention "
            "i Final Energy Level sa ROBUST ale nie VALIDATED"
        )


class TestPopulationSourceOfTruth:
    """SPRINT v0.11.0 P0: profil czyta re-run konfirmacyjny (23 genomy),
    nie demo Academy (2 genomy) - to jest architektoniczna roznica warta
    wlasnego testu, nie tylko efekt uboczny innych asercji."""

    def test_dataset_status_is_confirmatory_not_exploratory(self):
        profile = build_competency_profile()
        assert profile["dataset_status"].startswith("CONFIRMATORY")

    def test_genome_cards_have_23_genomes(self):
        profile = build_competency_profile()
        assert len(profile["genome_cards"]) == 23
        assert {"default", "highly_plastic", "minimal"} <= set(profile["genome_cards"].keys())

    def test_measured_concepts_have_confirmatory_status(self):
        profile = build_competency_profile()
        for c in profile["concepts"]:
            if c["status"] == "measured":
                assert c.get("confirmatory_status") in ("VALIDATED", "EXPERIMENTAL"), c["concept"]
            else:
                assert c.get("confirmatory_status") is None, c["concept"]


class TestExploratoryArchive:
    """SPRINT v0.11.0 P0: profil eksploracyjny v0.10.1 (n=10) NIE jest
    kasowany/nadpisywany w miejscu - archive_exploratory_profile() go
    zachowuje pod osobna sciezka, dokladnie raz (idempotentnie)."""

    def _write_exploratory_fixture(self, output_dir):
        import json
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "competency_profile.json").write_text(
            json.dumps({"dataset_status": "Exploratory Dataset v0.10 (test fixture)", "marker": "old"}),
            encoding="utf-8",
        )
        (output_dir / "competency_profile.md").write_text("# old exploratory md", encoding="utf-8")

    def test_archives_exploratory_profile_once(self, tmp_path):
        self._write_exploratory_fixture(tmp_path)
        result = archive_exploratory_profile(output_dir=tmp_path)
        assert result is not None
        assert (tmp_path / ARCHIVE_JSON_NAME).exists()
        assert (tmp_path / ARCHIVE_MD_NAME).exists()

    def test_does_not_rearchive_if_archive_already_exists(self, tmp_path):
        self._write_exploratory_fixture(tmp_path)
        archive_exploratory_profile(output_dir=tmp_path)
        # Nadpisz zywy plik czyms innym (symuluje kolejne uruchomienie
        # generatora po pierwszym przejsciu na dane konfirmacyjne) -
        # ponowne wywolanie NIE powinno nadpisac juz zrobionego archiwum.
        import json
        (tmp_path / "competency_profile.json").write_text(
            json.dumps({"dataset_status": "CONFIRMATORY - powinno zostac nietkniete w archiwum"}),
            encoding="utf-8",
        )
        result = archive_exploratory_profile(output_dir=tmp_path)
        assert result is None
        archived = json.loads((tmp_path / ARCHIVE_JSON_NAME).read_text(encoding="utf-8"))
        assert archived["marker"] == "old"

    def test_does_not_archive_when_live_file_already_confirmatory(self, tmp_path):
        import json
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "competency_profile.json").write_text(
            json.dumps({"dataset_status": "CONFIRMATORY - juz po przejsciu"}),
            encoding="utf-8",
        )
        result = archive_exploratory_profile(output_dir=tmp_path)
        assert result is None
        assert not (tmp_path / ARCHIVE_JSON_NAME).exists()


class TestWriteArtifacts:
    def test_write_competency_profile_creates_json_and_md(self, tmp_path):
        paths = write_competency_profile(output_dir=tmp_path)
        assert paths["json"].exists()
        assert paths["md"].exists()
