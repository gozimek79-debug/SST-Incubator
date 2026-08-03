"""Testy scripts/spec_md_to_json.py.

Konwencja projektu: kazdy test pozytywny ma test negatywny obok (inaczej nie
wiadomo, czy sprawdzenie cokolwiek chroni). Tu najwazniejszy negatyw to brak
hasha w wyjsciu - regresja do osadzania `source_document_sha256` bylaby cichym
powrotem do wyjatku od C-001, ktory ta implementacja swiadomie omija (patrz
docstring modulu).
"""

from pathlib import Path

from scripts.spec_md_to_json import convert, parse_content_blocks

SPEC_MD_PATH = Path(__file__).resolve().parents[1] / "SPECYFIKACJA_KANONICZNA_PC_001_v1.0.md"


class TestPreamble:
    def test_title_extracted_from_h1(self):
        data = convert("# TYTUL DOKUMENTU\n\n**Od:** X\n\n---\n\n## 1. Sekcja\ntresc\n", "x.md")
        assert data["title"] == "TYTUL DOKUMENTU"

    def test_meta_pairs_extracted_from_bold_lead(self):
        data = convert("# T\n\n**Od:** audytor · **Dla:** CTO\n\n---\n\n## 1. S\nx\n", "x.md")
        assert data["meta"]["od"] == "audytor"
        assert data["meta"]["dla"] == "CTO"

    def test_h1_is_not_duplicated_as_a_section(self):
        """Regresja: HEADER_RE musi wykluczac poziom 1 (tytul), inaczej dokument
        dostaje fantomowa sekcje 'id: <slug tytulu>' obok pola title."""
        data = convert("# TYTUL\n\n---\n\n## 1. Jedyna sekcja\ntresc\n", "x.md")
        assert len(data["sections"]) == 1
        assert data["sections"][0]["id"] == "1"


class TestSectionIdentification:
    def test_numbered_header_gets_numeric_id(self):
        data = convert("# T\n\n---\n\n### 2.9 Parametr\ntresc\n", "x.md")
        s = data["sections"][0]
        assert s["id"] == "2.9"
        assert s["numbered"] is True
        assert s["level"] == 3

    def test_unnumbered_header_gets_slug_id(self):
        data = convert("# T\n\n---\n\n## Notacja adresow\ntresc\n", "x.md")
        s = data["sections"][0]
        assert s["id"] == "notacja-adresow"
        assert s["numbered"] is False

    def test_lettered_subsection_id_preserved(self):
        data = convert("# T\n\n---\n\n### 6.1a Wariant\ntresc\n", "x.md")
        assert data["sections"][0]["id"] == "6.1a"

    def test_start_line_recorded(self):
        md = "# T\n\n---\n\nline3\n\n## 5. Sekcja\ntresc\n"
        data = convert(md, "x.md")
        assert data["sections"][0]["start_line"] == 7


class TestTableParsing:
    def test_table_rows_are_dicts_keyed_by_column(self):
        md = (
            "# T\n\n---\n\n## 1. S\n"
            "| Parametr | Adres |\n"
            "|---|---|\n"
            "| Tolerancja | CONFIG::X |\n"
        )
        data = convert(md, "x.md")
        table = data["sections"][0]["blocks"][0]
        assert table["type"] == "table"
        assert table["columns"] == ["Parametr", "Adres"]
        assert table["rows"] == [{"Parametr": "Tolerancja", "Adres": "CONFIG::X"}]

    def test_table_cell_values_stay_as_raw_strings_not_coerced(self):
        """Konwerter nie interpretuje tresci: liczba w komorce zostaje stringiem,
        nie jest rzutowana na int/float - to byloby juz wyciaganie wartosci."""
        md = (
            "# T\n\n---\n\n## 1. S\n"
            "| Parametr | Wartosc |\n"
            "|---|---|\n"
            "| Prog | 0.20 |\n"
        )
        data = convert(md, "x.md")
        cell = data["sections"][0]["blocks"][0]["rows"][0]["Wartosc"]
        assert cell == "0.20"
        assert isinstance(cell, str)

    def test_two_line_separator_without_table_header_is_not_a_table(self):
        blocks = parse_content_blocks(["| not a table start without separator next"])
        assert blocks == [{"type": "paragraph", "text": "| not a table start without separator next"}]


class TestListAndQuoteAndCode:
    def test_list_items_collected(self):
        blocks = parse_content_blocks(["- a", "- b", "1. c"])
        assert blocks == [{"type": "list", "items": ["a", "b", "c"]}]

    def test_blockquote_becomes_note(self):
        blocks = parse_content_blocks(["> linia jeden", "> linia dwa"])
        assert blocks == [{"type": "note", "text": "linia jeden linia dwa"}]

    def test_code_block_with_language_tag(self):
        blocks = parse_content_blocks(["```json", '{"a": 1}', "```"])
        assert blocks == [{"type": "code", "language": "json", "text": '{"a": 1}'}]

    def test_orphan_continuation_line_before_any_list_item_does_not_crash(self):
        blocks = parse_content_blocks(["  continuation with no list yet", "- real item"])
        assert blocks[-1] == {"type": "list", "items": ["real item"]}


class TestNoEmbeddedHash:
    def test_output_never_contains_a_hash_field(self):
        """Negatyw: ta implementacja swiadomie NIE osadza source_document_sha256
        (patrz docstring modulu - regeneracja+porownanie w walidatorze zastepuje
        hash i nie wymaga wyjatku od C-001). Regresja byloby cichym powrotem do
        tego wyjatku."""
        data = convert("# T\n\n---\n\n## 1. S\ntresc\n", "x.md")
        serialized_keys = set(data.keys())
        assert "source_document_sha256" not in serialized_keys
        assert not any("hash" in k.lower() for k in serialized_keys)


class TestDeterminism:
    def test_convert_is_idempotent_on_identical_input(self):
        md = SPEC_MD_PATH.read_text(encoding="utf-8")
        first = convert(md, "SPECYFIKACJA_KANONICZNA_PC_001_v1.0.md")
        second = convert(md, "SPECYFIKACJA_KANONICZNA_PC_001_v1.0.md")
        assert first == second


class TestRealDocument:
    """Kotwice na prawdziwym dokumencie - jesli te sekcje znikna, spec sie zmienila
    strukturalnie i JSON wymaga regeneracji (informacyjne, nie substytut walidatora)."""

    def test_known_section_ids_present(self):
        md = SPEC_MD_PATH.read_text(encoding="utf-8")
        data = convert(md, SPEC_MD_PATH.name)
        ids = {s["id"] for s in data["sections"]}
        for expected in ("0.2", "2.9", "6.1", "6.3", "8.1", "9"):
            assert expected in ids

    def test_section_count_matches_known_structure(self):
        md = SPEC_MD_PATH.read_text(encoding="utf-8")
        data = convert(md, SPEC_MD_PATH.name)
        assert len(data["sections"]) == 31
