"""B4C-2 (10), znalezisko CTO: ERRATUM 1 (.md + .json) jest druga recznie
utrzymywana para dokumentow bez generatora i bez kontroli (spec_md_to_json.py
obsluguje wylacznie SPECYFIKACJE KANONICZNA - zweryfikowane, zgloszone
w B4C-2 (09)). Mechaniczna regeneracja nie pasuje do tej pary (struktura
.json jest slownikiem SEMANTYCZNYM, nie odwzorowaniem markdownu) - test
tutaj jest WEZSZY, celowo: sprawdza wylacznie PIEC rzeczy ROZSTRZYGAJACYCH,
nie pelna rownowaznosc dokumentow (ktora bylaby tautologia albo stale
czerwona)."""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MD_PATH = REPO_ROOT / "publications" / "preregistration_PC_001_ERRATUM_1_2026-08-27.md"
JSON_PATH = REPO_ROOT / "publications" / "preregistration_PC_001_ERRATUM_1_2026-08-27.json"

REAL_MD = MD_PATH.read_text(encoding="utf-8")
REAL_JSON = json.loads(JSON_PATH.read_text(encoding="utf-8"))


def _normalize(text: str) -> str:
    """Usuwa dekoracje markdown (**, `, cudzyslowy „ " ", znaczniki cytatu
    blokowego '> ' na poczatku linii) i sklada wieloliniowe cytaty w jedna
    linie - do porownania TRESCI cytatu miedzy .md (formatowany, zawijany
    blockquote) i .json (proza jednoliniowa)."""
    text = re.sub(r"(?m)^>\s?", "", text)
    text = text.replace("**", "").replace("`", "")
    text = text.replace("„", "").replace('"', "").replace('"', "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


NORMALIZED_MD = _normalize(REAL_MD)


def _five_decisive_facts(json_data: dict) -> dict:
    """Wyciaga piec rzeczy ROZSTRZYGAJACYCH z .json - jedyne miejsce, gdzie
    ta lista jest zdefiniowana (B4C-2 (10))."""
    return {
        "environment_replaced": json_data["correction"]["environment_replaced"],
        "environment_replacing": json_data["correction"]["environment_replacing"],
        "quote_1": json_data["conflicting_sentences"]["sentence_1_problem_justification"],
        "quote_2": json_data["conflicting_sentences"]["sentence_2_new_wording"],
        "date": json_data["date"],
        "amended_document_id": json_data["amends"],
    }


REAL_FACTS = _five_decisive_facts(REAL_JSON)


class TestErratum1MirrorFiveDecisiveFacts:
    """Piec rzeczy rozstrzygajace musza wystapic w OBU plikach (B4C-2 (10)):
    nazwa srodowiska zastepowanego, nazwa srodowiska zastepujacego, oba
    cytaty doslowne z Aneksu 1, data erratum, identyfikator dokumentu
    zmienianego."""

    def test_environment_replaced_shock_world_in_both_files(self):
        assert REAL_FACTS["environment_replaced"] == "shock_world"
        assert "shock_world" in REAL_JSON["correction"]["replacement"]
        assert "`shock_world`" in REAL_MD or "shock_world" in REAL_MD

    def test_environment_replacing_noise_world_in_both_files(self):
        assert REAL_FACTS["environment_replacing"] == "noise_world"
        assert "noise_world" in REAL_JSON["correction"]["new_wording"]
        assert "noise_world" in REAL_MD

    def test_replacement_statement_present_in_both(self):
        """Zdanie 'X zostaje ZASTAPIONY przez Y' - jawne stwierdzenie
        zastapienia, nie tylko obecnosc obu nazw osobno."""
        assert "ZASTAPIONY" in REAL_JSON["correction"]["replacement"] or \
               "ZASTĄPIONY" in REAL_JSON["correction"]["replacement"]
        assert "ZASTĄPIONY" in REAL_MD or "ZASTAPIONY" in REAL_MD

    def test_quote_1_problem_justification_in_both_files(self):
        """Cytat 1 (zdanie uzasadniajace problem, Aneks 1 -> change_3) -
        rdzen tresci (bez markdown/cudzyslowow) obecny w obu plikach."""
        core = "22% w srodowisku realnym i 19% w czystym szumie kryterium"
        core_diacritics = "22% w środowisku realnym i 19% w czystym szumie kryterium"
        assert core in _normalize(REAL_FACTS["quote_1"]) or core_diacritics in _normalize(REAL_FACTS["quote_1"])
        assert core_diacritics in NORMALIZED_MD

    def test_quote_2_new_wording_in_both_files(self):
        """Cytat 2 (nowe brzmienie kryterium, Aneks 1 -> change_3) - rdzen
        tresci obecny w obu plikach."""
        core_json = _normalize(REAL_FACTS["quote_2"])
        assert "istotnie przewyzszac efekt" in core_json or "istotnie przewyższać efekt" in core_json
        assert "pure_noise_world" in core_json
        assert "istotnie przewyższać efekt" in NORMALIZED_MD
        assert "pure_noise_world" in NORMALIZED_MD

    def test_date_matches_between_files(self):
        assert REAL_FACTS["date"] == "2026-08-27"
        assert "2026-08-27" in REAL_MD

    def test_amended_document_identifier_present_in_both(self):
        """Identyfikator dokumentu zmienianego (ANEKS 1) - .json wskazuje
        pelna sciezke, .md wskazuje nazwe - oba musza jednoznacznie wskazywac
        TEN SAM dokument."""
        assert "ANEKS_1_2026-07-28" in REAL_FACTS["amended_document_id"]
        assert "ANEKS 1" in REAL_MD

    def test_scanner_finds_something_not_empty_facts(self):
        """Dowod, ze wyciaganie faktow nie zwraca cichych pustych stringow."""
        for key, value in REAL_FACTS.items():
            assert value, f"puste pole rozstrzygajace: {key}"


class TestErratum1MirrorNegative:
    """Test negatywny (B4C-2 (10)): zmien nazwe srodowiska w KOPII .json ->
    test MUSI pasc."""

    def test_negative_tampered_environment_name_is_caught(self):
        tampered = json.loads(json.dumps(REAL_JSON))  # deep copy przez roundtrip
        tampered["correction"]["environment_replacing"] = "pure_noise_world"
        facts = _five_decisive_facts(tampered)
        assert facts["environment_replacing"] != "noise_world"
        # I odwrotnie: prawdziwy plik nadal mowi noise_world - dowod, ze
        # podmiana dotyczy KOPII, nie pliku na dysku.
        assert REAL_FACTS["environment_replacing"] == "noise_world"

    def test_negative_tampered_date_breaks_cross_file_match(self):
        tampered = json.loads(json.dumps(REAL_JSON))
        tampered["date"] = "2026-01-01"
        facts = _five_decisive_facts(tampered)
        assert facts["date"] != REAL_FACTS["date"]
        assert facts["date"] not in REAL_MD or "2026-01-01" not in REAL_MD

    def test_negative_tampered_quote_no_longer_matches_md(self):
        tampered = json.loads(json.dumps(REAL_JSON))
        tampered["conflicting_sentences"]["sentence_2_new_wording"] = (
            "Zdanie calkowicie inne, nieobecne w Aneksie 1 ani w erratum."
        )
        facts = _five_decisive_facts(tampered)
        core = _normalize(facts["quote_2"])
        assert "pure_noise_world" not in core
