"""B4C-2 (12), znalezisko CTO: straznik luster (test_erratum_1_mirror.py)
dowodzi, ze DWIE KOPIE (.md i .json erratum) ZGADZAJA SIE ZE SOBA. Nie
dowodzi, ze OBIE ZGADZAJA SIE ZE ZRODLEM (ANEKS 1 / power_analysis_PC_001.json).
Ten sam blad co lista 51 wobec 52, tylko o jeden poziom wyzej - normalizacja
(usuniecie markdown/bialych znakow) uzyta do porownania dwoch kopii miedzy
soba zjada ROWNIEZ roznice, ktore odrozniaja obie kopie od PRAWDZIWEGO
zrodla (np. 'p<0.05' vs 'p < 0.05', 'OPROCZ' vs 'oprocz' - oba warianty
normalizuja sie identycznie, wiec lustro miedzy kopiami przechodzilo, mimo
ze zadna kopia nie byla doslowna wobec zrodla).

Kazdy cytat oznaczony jako DOSLOWNY musi wystapic w PLIKU ZRODLOWYM, do
ktorego sie odwoluje - sprawdzone WYKONANIEM, nie deklaracja."""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PUB = REPO_ROOT / "publications"


def normalize_for_source_check(text: str) -> str:
    """Usuwa WYLACZNIE znaczniki markdown (backtick, gwiazdka, cytat blokowy
    '> ', cudzyslowy dekoracyjne „ " ") i zwija biale znaki (w tym zlamania
    linii) do pojedynczej spacji. CELOWO BEZ zmiany wielkosci liter i BEZ
    usuwania pojedynczych spacji wewnatrz tekstu (B4C-2 (12), wymog CTO) -
    to jest DOKLADNIE ta para wlasciwosci, ktorych brak pozwolil 'p<0.05'
    przejsc jako rownowazne 'p < 0.05'."""
    text = re.sub(r"(?m)^>\s?", "", text)
    text = text.replace("**", "").replace("`", "")
    text = text.replace("„", "").replace('"', "").replace('"', "").replace('"', "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def assert_literal_quote_in_source(quote: str, source_path: Path) -> None:
    """Sprawdza, ze `quote` (po normalizacji ograniczonej do markdown/
    bialych znakow - patrz normalize_for_source_check) wystepuje jako
    PODCIAG w tresci `source_path` (po tej samej normalizacji). AssertionError
    (nie cichy False) na niezgodnosc - test wywolujacy ma pokazac oba
    fragmenty w komunikacie."""
    source_text = source_path.read_text(encoding="utf-8")
    normalized_quote = normalize_for_source_check(quote)
    normalized_source = normalize_for_source_check(source_text)
    assert normalized_quote in normalized_source, (
        f"cytat NIE wystepuje doslownie w zrodle {source_path.name}:\n"
        f"  cytat (znormalizowany):  {normalized_quote!r}\n"
        f"  zrodlo nie zawiera tego podciagu"
    )


ANEKS_1_MD = PUB / "preregistration_PC_001_ANEKS_1_2026-07-28.md"
ERRATUM_1_JSON = json.loads((PUB / "preregistration_PC_001_ERRATUM_1_2026-08-27.json").read_text(encoding="utf-8"))


class TestErratum1QuotesMatchAneks1Source:
    """Oba cytaty w ERRATUM 1 sprawdzone WPROST wobec ANEKS 1 -> Zmiana 3
    (publications/preregistration_PC_001_ANEKS_1_2026-07-28.md), nie wobec
    drugiej kopii erratum."""

    def test_sentence_1_matches_aneks_1_md(self):
        quote = ERRATUM_1_JSON["conflicting_sentences"]["sentence_1_problem_justification"]
        assert_literal_quote_in_source(quote, ANEKS_1_MD)

    def test_sentence_2_matches_aneks_1_md(self):
        """To jest DOKLADNIE ten cytat, ktory byl bledny (p<0.05/OPROCZ
        zamiast p < 0.05/oprocz) - dowod, ze po poprawce faktycznie zgadza
        sie ze zrodlem, nie tylko z .md erratum."""
        quote = ERRATUM_1_JSON["conflicting_sentences"]["sentence_2_new_wording"]
        assert_literal_quote_in_source(quote, ANEKS_1_MD)

    def test_negative_one_changed_letter_is_caught(self):
        """Test negatywny (wymog CTO): zmien jedna litere w cytacie -> FAIL."""
        quote = ERRATUM_1_JSON["conflicting_sentences"]["sentence_2_new_wording"]
        tampered = quote.replace("oprócz", "oprucz", 1)
        assert tampered != quote, "podmiana nie zaszla - dopasuj literalny tekst"
        try:
            assert_literal_quote_in_source(tampered, ANEKS_1_MD)
            assert False, "test negatywny nie wykryl podmienionej litery - oczekiwano AssertionError"
        except AssertionError as e:
            assert "NIE wystepuje" in str(e) or "nie wykryl" not in str(e)

    def test_negative_spacing_regression_is_caught(self):
        """Odtwarza DOKLADNIE znaleziony blad ('p<0.05' zamiast 'p < 0.05')
        - dowod, ze test faktycznie lapie TEN konkretny rodzaj rozjazdu,
        nie tylko dowolna literowke."""
        regressed = ERRATUM_1_JSON["conflicting_sentences"]["sentence_2_new_wording"].replace(
            "p < 0.05", "p<0.05"
        )
        assert regressed != ERRATUM_1_JSON["conflicting_sentences"]["sentence_2_new_wording"]
        raised = False
        try:
            assert_literal_quote_in_source(regressed, ANEKS_1_MD)
        except AssertionError:
            raised = True
        assert raised, "regresja 'p<0.05' powinna byc wykryta jako niezgodna ze zrodlem"

    def test_negative_of_negative_unmodified_quote_does_not_raise(self):
        """Sanity: sam mechanizm sprawdzajacy nie jest zawsze-czerwony."""
        quote = ERRATUM_1_JSON["conflicting_sentences"]["sentence_2_new_wording"]
        assert_literal_quote_in_source(quote, ANEKS_1_MD)  # nie podnosi


POWER_ANALYSIS_JSON_PATH = PUB / "power_analysis_PC_001.json"
ERRATUM_2_JSON = json.loads((PUB / "preregistration_PC_001_ERRATUM_2_2026-08-29.json").read_text(encoding="utf-8"))


class TestErratum2QuotesMatchPowerAnalysisSource:
    """B4C-2 (12), zadanie 4 objete rowniez na ERRATUM 2: trzy cytaty
    (source/definition/crossing pola required_seeds.n_operational) sprawdzone
    wobec publications/power_analysis_PC_001.json - jedynego zrodla (brak
    pary .md, plik czysto danowy)."""

    @pytest.mark.parametrize("key", ["source_field", "definition_field", "crossing_field"])
    def test_quote_matches_power_analysis_json(self, key):
        quote = ERRATUM_2_JSON["source_quotes"][key]["text"]
        assert_literal_quote_in_source(quote, POWER_ANALYSIS_JSON_PATH)

    def test_negative_one_changed_letter_is_caught(self):
        quote = ERRATUM_2_JSON["source_quotes"]["definition_field"]["text"]
        tampered = quote.replace("PONIZEJ", "PONIZEJU", 1)
        assert tampered != quote
        raised = False
        try:
            assert_literal_quote_in_source(tampered, POWER_ANALYSIS_JSON_PATH)
        except AssertionError:
            raised = True
        assert raised

    def test_value_8_is_historically_correct_in_untouched_source(self):
        """ZADANIE CTO pkt 4 (07): power_analysis_PC_001.json NIE jest
        edytowany - value=8 tam MUSI nadal stac, historycznie prawdziwe."""
        import json as _json
        power_analysis = _json.loads(POWER_ANALYSIS_JSON_PATH.read_text(encoding="utf-8"))
        assert power_analysis["required_seeds"]["n_operational"]["value"] == 8

    def test_erratum_declares_the_replacement_values(self):
        assert ERRATUM_2_JSON["correction"]["value_replaced"] == 8
        assert ERRATUM_2_JSON["correction"]["value_replacing"] == 9


ANEKS_1_MD_PATH = ANEKS_1_MD
PC001_MD_PATH = PUB / "preregistration_PC_001.md"
ERRATUM_3_JSON = json.loads((PUB / "preregistration_PC_001_ERRATUM_3_2026-08-29.json").read_text(encoding="utf-8"))
ERRATUM_3_SOURCE_FILE = {
    "aneks1_warunek4_K1": ANEKS_1_MD_PATH,
    "aneks1_warunek7_K4": ANEKS_1_MD_PATH,
    "aneks1_warunek8_K5": ANEKS_1_MD_PATH,
    "pc001_K1_kryterium": PC001_MD_PATH,
    "pc001_K4_kryterium": PC001_MD_PATH,
    "pc001_K5_kryterium": PC001_MD_PATH,
}


class TestErratum3QuotesMatchSources:
    """B4C-2 (15): szesc cytatow (warunki 4/7/8 ANEKS 1, kryteria K1/K4/K5
    PC-001 §5) sprawdzonych wobec DWOCH roznych plikow zrodlowych."""

    @pytest.mark.parametrize("key", list(ERRATUM_3_SOURCE_FILE.keys()))
    def test_quote_matches_source(self, key):
        quote = ERRATUM_3_JSON["source_quotes"][key]["text"]
        assert_literal_quote_in_source(quote, ERRATUM_3_SOURCE_FILE[key])

    def test_negative_one_changed_letter_is_caught(self):
        quote = ERRATUM_3_JSON["source_quotes"]["pc001_K5_kryterium"]["text"]
        tampered = quote.replace("zniknąć", "zniknoć", 1)
        assert tampered != quote
        raised = False
        try:
            assert_literal_quote_in_source(tampered, PC001_MD_PATH)
        except AssertionError:
            raised = True
        assert raised

    def test_six_cells_affected_declared(self):
        assert set(ERRATUM_3_JSON["correction"]["cells_affected"]) == {
            "K1-A", "K1-B", "K4-A", "K4-B", "K5-A", "K5-B",
        }

    def test_direction_replacement_declared(self):
        assert ERRATUM_3_JSON["correction"]["direction_replaced"] == "BRAK_ODRZUCENIA_H0"
        assert ERRATUM_3_JSON["correction"]["direction_replacing"] == "ROWNOWAZNOSC"
