"""Testy scripts/validate_canonical_spec.py.

Konwencja projektu: kazdy test pozytywny ma test negatywny obok (patrz
tests/test_validate_artifact_freshness.py) - inaczej nie wiadomo, czy walidator
cokolwiek chroni ("walidator bez testu negatywnego jest dekoracja",
SPECYFIKACJA_KANONICZNA_PC_001.md §9).

Najwazniejsza klasa testow tutaj to TestC001FilterCatchesInjectedValues: dowodzi,
ze mimo wszystkich wyjatkow w find_c001_violations_in_text (kolumna '#', cudzyslowy
fragmentow, sciezki plikow, zakresy sekcji, sklejone identyfikatory, slowa-wyzwalacze
pkt/nr/pozycja/warunek/test/sekcja, marker listy numerowanej, literalne "0"), realny
prog/podloga/licznosc/odsetek NADAL zostaje zlapany - w tym w NAJGORSZYM przypadku,
gdy wstrzykniety fragment sasiaduje ze slowem-wyzwalaczem.
"""

import copy
import json

import pytest

from scripts.spec_md_to_json import convert
from scripts.validate_canonical_spec import (
    REPO_ROOT,
    SPEC_JSON,
    SPEC_MD,
    check_c001,
    check_critical_files_registry_coverage,
    check_file_addresses,
    check_fragment_addresses,
    check_json_matches_markdown,
    check_section_addresses,
    check_symbol_addresses,
    find_c001_violations_in_text,
    load_critical_files,
    resolve_fragment_in_file,
    resolve_section_in_file,
    resolve_symbol_in_file,
)

REAL_MD = SPEC_MD.read_text(encoding="utf-8")
REAL_SPEC_DATA = convert(REAL_MD, SPEC_MD.name)


def _spec_data_copy():
    return copy.deepcopy(REAL_SPEC_DATA)


class TestRealDocumentIsClean:
    """Kotwica: caly realny dokument musi przechodzic wszystkie sprawdzenia -
    jesli nie przechodzi, albo dokument, albo walidator ma problem."""

    def test_all_checks_pass_on_real_document(self):
        assert check_file_addresses(REAL_SPEC_DATA) == []
        assert check_section_addresses(REAL_SPEC_DATA) == []
        assert check_fragment_addresses(REAL_SPEC_DATA) == []
        assert check_symbol_addresses(REAL_SPEC_DATA) == []
        assert check_c001(REAL_SPEC_DATA) == []
        assert check_critical_files_registry_coverage(REAL_SPEC_DATA) == []
        assert check_json_matches_markdown() == []


class TestFileAddressResolution:
    def test_known_shortcut_resolves(self):
        assert resolve_section_in_file(REPO_ROOT / "docs/GOVERNANCE_RULES.md", "5")

    def test_unknown_backtick_path_is_caught(self):
        data = _spec_data_copy()
        data["sections"][0]["blocks"].append(
            {"type": "paragraph", "text": "patrz `tests/test_this_file_does_not_exist.py`"}
        )
        problems = check_file_addresses(data)
        assert any("test_this_file_does_not_exist.py" in p for p in problems)

    def test_formula_with_slash_is_not_mistaken_for_a_path(self):
        """Regresja: '`a / b`' zawiera '/' ale nie jest adresem pliku (brak rozszerzenia)."""
        data = _spec_data_copy()
        data["sections"][0]["blocks"].append(
            {"type": "paragraph", "text": "wzor: `redukcja = (a - b) / c`"}
        )
        assert check_file_addresses(data) == []

    def test_brace_range_shortcut_expands_and_resolves(self):
        data = _spec_data_copy()
        data["sections"][0]["blocks"].append(
            {
                "type": "paragraph",
                "text": "`publications/preregistration_PC_001_ANEKS_{1..5}_2026-07-28.md`",
            }
        )
        assert check_file_addresses(data) == []

    def test_brace_range_with_missing_member_is_caught(self):
        data = _spec_data_copy()
        data["sections"][0]["blocks"].append(
            {
                "type": "paragraph",
                "text": "`publications/preregistration_PC_001_ANEKS_{1..9}_2026-07-28.md`",
            }
        )
        problems = check_file_addresses(data)
        assert any("ANEKS_6_2026-07-28.md" in p for p in problems)


class TestSectionAndFragmentResolution:
    def test_numbered_section_resolves_pc001_style(self):
        assert resolve_section_in_file(REPO_ROOT / "publications/preregistration_PC_001.md", "2.1")

    def test_section_symbol_notation_resolves_gov_style(self):
        """GOV numeruje jako '## §5 ...', nie '## 5. ...' - inna konwencja niz PC-001."""
        assert resolve_section_in_file(REPO_ROOT / "docs/GOVERNANCE_RULES.md", "6")

    def test_nonexistent_section_number_is_caught(self):
        assert not resolve_section_in_file(REPO_ROOT / "publications/preregistration_PC_001.md", "999")

    def test_fragment_resolves_via_header_prefix(self):
        assert resolve_fragment_in_file(
            REPO_ROOT / "publications/preregistration_PC_001_ANEKS_1_2026-07-28.md", "Zmiana 4"
        )

    def test_nonexistent_fragment_is_caught(self):
        assert not resolve_fragment_in_file(
            REPO_ROOT / "publications/preregistration_PC_001_ANEKS_1_2026-07-28.md",
            "Fragment Ktory Nie Istnieje",
        )

    def test_bad_section_address_injected_into_spec_is_caught(self):
        data = _spec_data_copy()
        data["sections"][0]["blocks"].append({"type": "paragraph", "text": "patrz PC-001 §999"})
        problems = check_section_addresses(data)
        assert any("PC-001 §999" in p for p in problems)

    def test_bad_fragment_address_injected_into_spec_is_caught(self):
        data = _spec_data_copy()
        data["sections"][0]["blocks"].append(
            {"type": "paragraph", "text": 'patrz A1 → „Fragment Ktorego Nie Ma"'}
        )
        problems = check_fragment_addresses(data)
        assert any("Fragment Ktorego Nie Ma" in p for p in problems)


class TestSymbolResolution:
    def test_known_symbol_resolves(self):
        assert resolve_symbol_in_file(
            REPO_ROOT / "clos_scientist/pc_001_experiment_config.py", "FLOOR_BIAS_TOLERANCE"
        )

    def test_renamed_or_removed_symbol_is_caught(self):
        assert not resolve_symbol_in_file(
            REPO_ROOT / "clos_scientist/pc_001_experiment_config.py", "SYMBOL_KTOREGO_NIE_MA"
        )

    def test_bad_symbol_address_injected_into_spec_is_caught(self):
        data = _spec_data_copy()
        data["sections"][0]["blocks"].append(
            {"type": "paragraph", "text": "patrz CONFIG::SYMBOL_KTOREGO_NIE_MA"}
        )
        problems = check_symbol_addresses(data)
        assert any("SYMBOL_KTOREGO_NIE_MA" in p for p in problems)


class TestC001AllowedReferencesNotFlagged:
    """Prawdziwe wzorce z dokumentu, ktore NIE sa wartosciami - dowod, ze filtr
    nie jest tak szeroki, ze przepuszcza tylko dlatego, ze nic nie lapie."""

    @pytest.mark.parametrize(
        "text",
        [
            "Rola L1.1 (wspierająca, poza regułą decyzyjną)",
            "**K3a** warunek 1 — wzrost PE po wstrząsie",
            "warunku 2 K3a (błąd projektu pomiaru)",
            "CLOS v0.12",
            "Core — ZAMROŻONY od v0.1",
            "Sekcje 2.1–2.11 adresują kryteria",
            "wspólny dla pozycji 7–10",
            "dokument jest pozycją 1",
            "Testy 4b i 6 istnieją",
            "Wynik testów 5 i 2 był początkowo negatywny",
            "PE_red(t) = max(0, PE(t) − floor)",
            "Warunek A (kierunek, `β < 0`)",
            "patrz PC-001 §2.1 → „Uzasadnienie”",
            "wersja mniejsza (v1.1)",
        ],
    )
    def test_allowed_reference_produces_no_violation(self, text):
        assert find_c001_violations_in_text(text) == []

    def test_numbered_list_marker_in_code_block_not_flagged(self):
        code_text = (
            "1. Specyfikacja Kanoniczna v1.0     ← ten dokument\n"
            "2. K3a Window Design Study          ← osobny artefakt\n"
            "5. B5 baseline → B6 bramka → START"
        )
        assert find_c001_violations_in_text(code_text) == []

    def test_row_index_column_not_flagged_regardless_of_value(self):
        assert find_c001_violations_in_text("47", column="#") == []

    def test_a6_recognized_as_document_identifier_like_a1_through_a5(self):
        """A6 (Aneks 6, data inna niz A1-A5, wiec poza wzorcem {1..5}) - zero
        zmian w filtrze bylo potrzebne: kazdy token sklejony z litera (A6, A1,
        K3a...) jest automatycznie wykluczony przez PURE_NUMBER_RE.fullmatch,
        niezaleznie od tego, ile takich skrotow SHORTCUTS wymienia. Test
        dokumentuje to zachowanie wprost, zamiast polegac na przypadku."""
        assert find_c001_violations_in_text("patrz A6 §3, definicja w A2") == []

    def test_a6_does_not_mask_a_real_injected_value_beside_it(self):
        violations = find_c001_violations_in_text("A6 wprowadza próg 0.20")
        assert any(tok == "0.20" for _, tok in violations)


class TestC001FilterCatchesInjectedValues:
    """Test negatywny 4b (spec §9): sondy - prog, podloga, licznosc, odsetek -
    MUSZA zostac zlapane kazda z osobna, w tym w NAJGORSZYM przypadku (obok slowa-
    wyzwalacza, ktore w innym miejscu legalnie zwalnia liczby calkowite z kontroli)."""

    def test_threshold_probe_caught(self):
        violations = find_c001_violations_in_text("próg redukcji wynosi 0.20")
        assert any(tok == "0.20" for _, tok in violations)

    def test_floor_probe_caught(self):
        """Realna wartosc podlogi z repo (CONFIG::FROZEN_FLOOR_NOISE_WORLD) jako kotwica."""
        violations = find_c001_violations_in_text("podłoga środowiska wynosi 0.09589")
        assert any(tok == "0.09589" for _, tok in violations)

    def test_count_probe_caught_without_reference_word_nearby(self):
        violations = find_c001_violations_in_text("rejestr zawiera 47 plików krytycznych")
        assert any(tok == "47" for _, tok in violations)

    def test_percentage_probe_caught(self):
        violations = find_c001_violations_in_text("różnica wynosi 12%")
        assert any(tok == "12" for _, tok in violations)

    def test_threshold_probe_caught_even_beside_warunek_and_pkt_trigger_words(self):
        """Najgorszy przypadek: dekady/prog obok DWOCH slow-wyzwalaczy naraz - filtr
        zwalnia tylko liczby CALKOWITE bez kropki, nigdy liczb z kropka."""
        violations = find_c001_violations_in_text("warunek wymaga redukcji o 0.20 (pkt 3)")
        assert any(tok == "0.20" for _, tok in violations)

    def test_percentage_probe_caught_even_beside_test_and_pozycja_trigger_words(self):
        violations = find_c001_violations_in_text("test wykazał różnicę 12% (pozycja 4)")
        assert any(tok == "12" for _, tok in violations)

    def test_count_probe_not_accidentally_masked_by_unrelated_range_reference(self):
        violations = find_c001_violations_in_text("Sekcje 2.1–2.11 opisują 47 warstw wykonawczych")
        assert any(tok == "47" for _, tok in violations)

    def test_injected_probe_into_real_spec_data_is_caught_end_to_end(self):
        """Pelna sciezka: wstrzykniecie do skopiowanego spec_data (nie realnego pliku),
        przepuszczenie przez check_c001 tak jak zrobilby to CI."""
        data = _spec_data_copy()
        data["sections"][0]["blocks"].append(
            {"type": "paragraph", "text": "próg Warunku B wynosi w tym wydaniu 0.20"}
        )
        problems = check_c001(data)
        assert any("0.20" in p for p in problems)


class TestCriticalFilesRegistryCoverage:
    def test_real_registry_fully_covered(self):
        assert check_critical_files_registry_coverage(REAL_SPEC_DATA) == []

    def test_load_critical_files_returns_52_known_entries(self):
        """D-031 (2026-08-04): +2 wzgledem 47 - SPRINT_v0.11.0.md,
        publications/BEZPIECZENSTWO_POMIARU_recovery_spearman.md, przed B5.
        Aneks 6 (2026-08-03, po weryfikacji Z1): +2 (md+json), 49 -> 51.
        B4C-01 (2026-08-17): +1 - runner Eksperymentu Konfirmacyjnego, 51 -> 52."""
        files = load_critical_files()
        assert len(files) == 52
        assert "docs/GOVERNANCE_RULES.md" in files
        assert "clos_brain/tissue.py" in files
        assert "SPRINT_v0.11.0.md" in files
        assert "publications/preregistration_PC_001_ANEKS_6_2026-08-03.md" in files
        assert "publications/BEZPIECZENSTWO_POMIARU_recovery_spearman.md" in files

    def test_removing_directory_prefix_row_breaks_coverage_for_its_files(self):
        """Negatyw (test §9 nr 6, odpowiednik): usuniecie adresu z §2 MUSI zepsuc test 5 -
        inaczej nie wiadomo, czy test 5 w ogole dziala. Usuwamy z KOPII wiersz §2.12
        opisujacy prefiks 'clos_brain/, birth/, genome/' (Core)."""
        data = _spec_data_copy()
        section_2_12 = next(s for s in data["sections"] if s["id"] == "2.12")
        for block in section_2_12["blocks"]:
            if block["type"] == "table":
                block["rows"] = [r for r in block["rows"] if "clos_brain/" not in r.get("Adres", "")]
        problems = check_critical_files_registry_coverage(data)
        assert any(p.startswith("clos_brain/") for p in problems)
        assert any(p.startswith("birth/") for p in problems)
        assert any(p.startswith("genome/") for p in problems)

    def test_removing_shortcut_reference_breaks_coverage_for_that_file(self):
        """GOV jest wspomniany w kilku podsekcjach §2 (nie tylko §2.10) - trzeba
        usunac KAZDA wzmianke, inaczej test nic by nie dowodzil (jedna ocalala
        wzmianka wystarczy, zeby plik pozostal 'opisany')."""
        data = _spec_data_copy()
        for section in data["sections"]:
            if not (section["id"] == "2" or section["id"].startswith("2.")):
                continue
            for block in section["blocks"]:
                if block["type"] == "table":
                    block["rows"] = [r for r in block["rows"] if "GOV" not in str(r.values())]
                elif block["type"] in ("paragraph", "note"):
                    block["text"] = block["text"].replace("GOV", "")
        problems = check_critical_files_registry_coverage(data)
        assert any(p.startswith("docs/GOVERNANCE_RULES.md") for p in problems)

    def test_extra_critical_file_not_in_real_registry_is_still_caught(self, monkeypatch):
        """Dowod, ze test 5 dziala nie tylko na §2.12: dokladamy fikcyjny plik do
        rejestru (poprzez monkeypatch load_critical_files) i sprawdzamy, ze
        nieopisany plik zostaje zlapany na realnym spec_data."""
        import scripts.validate_canonical_spec as mod

        real_files = load_critical_files()
        monkeypatch.setattr(mod, "load_critical_files", lambda: real_files + ["nieopisany_katalog/plik_widmo.py"])
        problems = mod.check_critical_files_registry_coverage(REAL_SPEC_DATA)
        assert any("nieopisany_katalog/plik_widmo.py" in p for p in problems)


class TestJsonMatchesMarkdown:
    def test_real_json_matches_real_markdown(self):
        assert check_json_matches_markdown() == []

    def test_hand_edited_json_is_caught(self, tmp_path):
        md_path = tmp_path / "spec.md"
        json_path = tmp_path / "spec.json"
        md_path.write_text(REAL_MD, encoding="utf-8")
        data = convert(REAL_MD, "spec.md")
        data["sections"][0]["title"] = "RECZNIE ZMIENIONY TYTUL"  # symulacja recznej edycji
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        problems = check_json_matches_markdown(md_path=md_path, json_path=json_path)
        assert problems != []

    def test_stale_json_after_markdown_edit_is_caught(self, tmp_path):
        md_path = tmp_path / "spec.md"
        json_path = tmp_path / "spec.json"
        data = convert(REAL_MD, "spec.md")
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        edited_md = REAL_MD.replace("## 9. Weryfikowalność", "## 9. Weryfikowalność (ZMIENIONE)")
        md_path.write_text(edited_md, encoding="utf-8")
        problems = check_json_matches_markdown(md_path=md_path, json_path=json_path)
        assert problems != []

    def test_missing_json_is_caught(self, tmp_path):
        md_path = tmp_path / "spec.md"
        md_path.write_text(REAL_MD, encoding="utf-8")
        problems = check_json_matches_markdown(md_path=md_path, json_path=tmp_path / "missing.json")
        assert problems != []


class TestZeroMatchesIsNeverSilentPass:
    """B4C-05 v5/v6 (zgloszenie trzeciego audytora, potwierdzone eksperymentem
    CTO): pusta lista problemow z kontroli 1/2/3 wygladala identycznie
    niezaleznie od tego, czy WSZYSTKO sie rozwiazalo, czy NIC nie bylo do
    sprawdzenia (notacja zniszczona). CTO zniszczyl 187 wystapien znaku
    paragrafu (zamiana na 'par.') w calej Specyfikacji i dostal PASS na
    kontrolach 2 i 3, mimo zero dopasowan. Ponizej DOKLADNA reprodukcja tego
    eksperymentu na naprawionym kodzie - PRZED i PO widoczne w nazwach
    testow (before = na oryginalnym dokumencie, after = na zniszczonej
    kopii)."""

    def test_before_real_document_has_nonzero_matches_of_every_kind(self):
        """PRZED zniszczeniem: dowod, ze kontrole faktycznie maja co liczyc -
        bez tego 'FAIL po zniszczeniu' nie dowodziloby niczego."""
        from scripts.validate_canonical_spec import (
            count_file_address_candidates,
            count_section_matches,
            count_fragment_matches,
            count_symbol_matches,
        )
        n_shortcuts, n_paths = count_file_address_candidates(REAL_SPEC_DATA)
        assert n_shortcuts > 0 and n_paths > 0
        assert count_section_matches(REAL_SPEC_DATA) > 0
        assert count_fragment_matches(REAL_SPEC_DATA) > 0
        assert count_symbol_matches(REAL_SPEC_DATA) > 0

    def test_after_destroying_section_sign_notation_check_section_fails(self):
        """Reprodukcja eksperymentu CTO: wszystkie wystapienia '§' -> 'par.'.

        B4C-05 v5/v6 zakaz wprost: NIE przypinac konkretnej liczby dopasowan
        (nauczka z Z9C) - stad '> 0', nie '== 187' (liczba wystapien '§' w
        dokumencie rosnie z kazda kolejna rewizja Specyfikacji; test ma
        dowodzic MECHANIZMU odpornosci, nie zamrazac liczby paragrafow)."""
        assert REAL_MD.count("§") > 0
        mangled = REAL_MD.replace("§", "par.")
        data = convert(mangled, SPEC_MD.name)
        problems = check_section_addresses(data)
        assert problems != [], "check_section_addresses dal PASS mimo zniszczonej notacji - regresja"
        assert any("ZERO" in p for p in problems)

    def test_after_destroying_section_sign_combined_check_2_fails(self):
        """Dokladnie ten check, ktory jest wpiety do CI jako '2_adresy_sekcji_i_fragmentow'."""
        mangled = REAL_MD.replace("§", "par.")
        data = convert(mangled, SPEC_MD.name)
        combined = check_section_addresses(data) + check_fragment_addresses(data)
        assert combined != [], "kontrola 2 (jak wpieta w CHECKS) dala PASS mimo zniszczonej notacji sekcji"

    def test_after_destroying_double_colon_notation_check_symbol_fails(self):
        mangled = REAL_MD.replace("::", ":")
        data = convert(mangled, SPEC_MD.name)
        problems = check_symbol_addresses(data)
        assert problems != [], "check_symbol_addresses dal PASS mimo zniszczonej notacji ::"
        assert any("ZERO" in p for p in problems)

    def test_after_removing_all_backticks_check_file_addresses_fails(self):
        mangled = REAL_MD.replace("`", "")
        data = convert(mangled, SPEC_MD.name)
        problems = check_file_addresses(data)
        assert problems != [], "check_file_addresses dal PASS mimo usuniecia wszystkich adresow w prozie"
        assert any("ZERO" in p for p in problems)

    def test_c001_fails_on_completely_empty_document(self):
        problems = check_c001({"sections": []})
        assert problems != []
        assert any("ZERO" in p for p in problems)

    def test_registry_coverage_fails_on_empty_critical_files_list(self, monkeypatch):
        import scripts.validate_canonical_spec as mod
        monkeypatch.setattr(mod, "load_critical_files", lambda: [])
        problems = mod.check_critical_files_registry_coverage(REAL_SPEC_DATA)
        assert problems != []

    def test_negative_of_negative_real_document_still_passes_after_fix(self):
        """Sanity: naprawa nie zepsula prawdziwego dokumentu - wszystkie
        kontrole nadal PASS na nietknietej Specyfikacji."""
        assert check_file_addresses(REAL_SPEC_DATA) == []
        assert check_section_addresses(REAL_SPEC_DATA) == []
        assert check_fragment_addresses(REAL_SPEC_DATA) == []
        assert check_symbol_addresses(REAL_SPEC_DATA) == []
        assert check_c001(REAL_SPEC_DATA) == []
        assert check_critical_files_registry_coverage(REAL_SPEC_DATA) == []


class TestResolvedCountReporting:
    """B4C-05 v6 pkt 1: resolved_count widoczny NAWET przy PASS."""

    def test_resolved_count_label_reports_nonzero_on_real_document(self):
        import re
        from scripts.validate_canonical_spec import resolved_count_label

        for name in (
            "1_adresy_plikow", "2_adresy_sekcji_i_fragmentow", "3_adresy_symboli",
            "4_C001_zero_wartosci", "5_pokrycie_rejestru_plikow_krytycznych",
            "6_json_zgodny_z_markdownem",
        ):
            label = resolved_count_label(name, REAL_SPEC_DATA)
            assert label != ""
            m = re.search(r"(?:resolved|przeskanowano)=(\d+)", label)
            assert m is not None, f"{name}: brak liczby w etykiecie {label!r}"
            assert int(m.group(1)) > 0, f"{name}: liczba w etykiecie jest 0 ({label!r})"
