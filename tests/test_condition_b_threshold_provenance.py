"""CONDITION_B_REDUCTION_THRESHOLD zgadza sie z prerejestracja (Z9/Z9B/Z9C).

Zrodlem referencyjnym jest MARKDOWN, nie JSON: markdown jest kanoniczny (Aneks 2,
"Zamrozenie"), JSON jest jego odwzorowaniem - parsowanie prozy zapisanej wewnatrz
pola JSON-a byloby parsowaniem prozy dwa kroki od zrodla (sprawdzone: prereg.json
nie niesie progu w postaci nadajacej sie do maszynowego odczytu - tylko wewnatrz
opisowego pola tekstowego, patrz Z9). Oba pliki zrodlowe (prereg, Aneks 1) sa
CZLONKAMI CRITICAL_FILES_PC_001 - zamrozone, chronione hashem. Wzorce oparte
na tekscie stalym sa stabilne Z KONSTRUKCJI, nie z czujnosci: tekst nie moze sie
zmienic bez zlamania hasha i zadzialania Hard Halt (ta sama logika co przy
zamrozonej podlodze srodowiska Primary).

DWA WZORCE (Z9C - wersja z jednym wzorcem i przypieta liczba wystapien byla
bledna: kazda proba dostrojenia liczby dopasowan do oczekiwanego wyniku jest
dokladnie tym bledem metodologicznym, ktoremu ten test ma zapobiegac gdzie
indziej w projekcie):

  WZORZEC A (definicyjny) - prog jako KRYTERIUM na redukcji
    ("Warunek B - mediana redukcji >= 20%"). Kotwica PRZED liczba:
    'redukcj' / 'Warunek B' / '**B**'.

  WZORZEC B (pochodzenie) - prog jako KONWENCJA PROJEKTU
    ("Prog 20% jest konwencja projektu, przyjeta w AIA v4"). Kotwica PO
    liczbie, w tym samym zdaniu: 'konwencja projektu'.

Oba wzorce sa NIEZALEZNE: zdanie definiujace i zdanie o pochodzeniu istnieja
w dokumentach z roznych powodow i mogłyby sie rozjechac niezaleznie. Kazdy
wzorzec MUSI znalezc co najmniej jedno dopasowanie - zero dopasowan jest FAIL,
nie ciche zawezenie do drugiego wzorca. Wszystkie znalezione wartosci (z obu
wzorcow, z obu plikow) musza byc identyczne miedzy soba i rowne stalej w CONFIG.

Zadna liczba dopasowan nie jest przypieta jako kryterium - tylko obecnosc
(>=1) i wzajemna zgodnosc wartosci.

WYKLUCZONE SWIADOMIE (zweryfikowane, ze zaden wzorzec ich nie lapie):
  - `0.2` (nie "20%") - sygnal bazowy `shock_world` w opisie srodowiska K3
    (prereg.md), forma dziesietna wyklucza go z PCT_RE bez dodatkowej logiki.
  - "pierwsze/ostatnie 20% okna" - rozmiar okna W_early/W_late (przypadkowo ta
    sama liczba co prog redukcji), brak kotwicy A ani B w poblizu.
  - cytowania pochodzenia w linii "Podstawa:" prerejestracji
    ("AIA v4 (prog 20%)") i w blockquocie "Relacja do rewizji 1"
    ("nachylenie regresji + prog 20%") - przelotne wzmianki bez slowa
    'redukcj'/'Warunek B' w poblizu (wzorzec A) i bez 'konwencja projektu'
    PO liczbie (wzorzec B - te zdania nie zawieraja tej frazy wcale).
"""

import re
from pathlib import Path

from clos_scientist.pc_001_experiment_config import CONDITION_B_REDUCTION_THRESHOLD

REPO_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = REPO_ROOT / "publications" / "preregistration_PC_001.md"
ANEKS1_PATH = REPO_ROOT / "publications" / "preregistration_PC_001_ANEKS_1_2026-07-28.md"

PCT_RE = re.compile(r"(\d+)\s*%")
PATTERN_A_ANCHOR = re.compile(r"redukcj|Warunek B|\*\*B\*\*", re.IGNORECASE)
PATTERN_B_ANCHOR = re.compile(r"konwencj\w*\s+projektu", re.IGNORECASE)
_WINDOW = 120


def find_pattern_a(text):
    """Zdania definiujace: liczba% poprzedzona w oknie wsteczym kotwica A."""
    found = []
    for m in PCT_RE.finditer(text):
        window = text[max(0, m.start() - _WINDOW) : m.start()]
        if PATTERN_A_ANCHOR.search(window):
            found.append(int(m.group(1)))
    return found


def find_pattern_b(text):
    """Zdania o pochodzeniu: liczba% nastepnie (w tym samym zdaniu) 'konwencja projektu'."""
    found = []
    for m in PCT_RE.finditer(text):
        window = text[m.end() : m.end() + _WINDOW]
        if PATTERN_B_ANCHOR.search(window):
            found.append(int(m.group(1)))
    return found


def verify_threshold_provenance(prereg_text, aneks1_text, expected_fraction):
    """Pelna kontrola: oba wzorce licza >=1 dopasowanie razem (w obu plikach),
    wszystkie znalezione wartosci sa identyczne miedzy soba i rowne
    expected_fraction. Zwraca liste problemow (pusta = OK)."""
    problems = []
    a_matches = find_pattern_a(prereg_text) + find_pattern_a(aneks1_text)
    b_matches = find_pattern_b(prereg_text) + find_pattern_b(aneks1_text)

    if not a_matches:
        problems.append("wzorzec A (definicyjny) nie znalazl zadnego dopasowania")
    if not b_matches:
        problems.append("wzorzec B (pochodzenie) nie znalazl zadnego dopasowania")

    all_values = set(a_matches) | set(b_matches)
    if len(all_values) > 1:
        problems.append(f"znalezione wartosci procentowe nie sa ze soba zgodne: {sorted(all_values)}")
    elif all_values:
        found_fraction = next(iter(all_values)) / 100.0
        if found_fraction != expected_fraction:
            problems.append(f"znaleziona wartosc {found_fraction} != stala CONFIG {expected_fraction}")

    return problems


REAL_PREREG_TEXT = PREREG_PATH.read_text(encoding="utf-8")
REAL_ANEKS1_TEXT = ANEKS1_PATH.read_text(encoding="utf-8")


class TestConstantValue:
    def test_constant_is_a_fraction_not_a_percent(self):
        assert CONDITION_B_REDUCTION_THRESHOLD == 0.20


class TestPatternsFindRealOccurrences:
    """Informacyjne: liczba dopasowan NIE jest kryterium (Z9C)."""

    def test_pattern_a_finds_at_least_one_in_each_document(self, capsys):
        prereg_hits = find_pattern_a(REAL_PREREG_TEXT)
        aneks1_hits = find_pattern_a(REAL_ANEKS1_TEXT)
        print(f"wzorzec A: prereg={len(prereg_hits)}, aneks1={len(aneks1_hits)}")
        assert len(prereg_hits) >= 1
        assert len(aneks1_hits) >= 1

    def test_pattern_b_finds_at_least_one_overall(self, capsys):
        prereg_hits = find_pattern_b(REAL_PREREG_TEXT)
        aneks1_hits = find_pattern_b(REAL_ANEKS1_TEXT)
        print(f"wzorzec B: prereg={len(prereg_hits)}, aneks1={len(aneks1_hits)}")
        assert len(prereg_hits) + len(aneks1_hits) >= 1


class TestKnownDecoysNotCaught:
    def test_shock_world_baseline_signal_not_caught(self):
        """'stala 0.2' (forma dziesietna, nie procentowa) - opis sygnalu K3."""
        text = "Srodowisko: `shock_world` (stala 0.2 -> wstrzas w ticku 20-80 -> nowy rezim)"
        assert find_pattern_a(text) == []
        assert find_pattern_b(text) == []

    def test_window_size_mentions_not_caught(self):
        text = "srednia prediction_error, ticki 0-59 (pierwsze 20% okna)"
        assert find_pattern_a(text) == []
        assert find_pattern_b(text) == []

    def test_provenance_citation_in_basis_line_not_caught_by_either_pattern(self):
        text = "Podstawa: D-005 (poprawki redakcyjne) - D-006 (zamrozenie) - AIA v4 (prog 20%)"
        assert find_pattern_a(text) == []
        assert find_pattern_b(text) == []

    def test_revision_relation_blockquote_not_caught_by_either_pattern(self):
        text = "dwuwarunkowy Primary Endpoint (nachylenie regresji + prog 20%) zamiast samych okien"
        assert find_pattern_a(text) == []
        assert find_pattern_b(text) == []


class TestEndToEndVerification:
    def test_real_documents_pass(self):
        problems = verify_threshold_provenance(
            REAL_PREREG_TEXT, REAL_ANEKS1_TEXT, CONDITION_B_REDUCTION_THRESHOLD
        )
        assert problems == []


class TestNegativeA_WrongConstantValue:
    """(a) zmieniona wartosc stalej -> FAIL."""

    def test_wrong_expected_value_is_caught(self):
        problems = verify_threshold_provenance(REAL_PREREG_TEXT, REAL_ANEKS1_TEXT, 0.25)
        assert problems != []
        assert any("!=" in p for p in problems)


class TestNegativeB_DisagreeingOccurrences:
    """(b) tekst z rozna wartoscia w dwoch miejscach -> FAIL na niezgodnosci."""

    def test_tampered_single_occurrence_triggers_disagreement(self):
        tampered_aneks1 = REAL_ANEKS1_TEXT.replace(
            "mediana redukcji **≥ 20%**", "mediana redukcji **≥ 25%**"
        )
        assert tampered_aneks1 != REAL_ANEKS1_TEXT, "podmiana nie zaszla - dopasuj literalny tekst"
        problems = verify_threshold_provenance(
            REAL_PREREG_TEXT, tampered_aneks1, CONDITION_B_REDUCTION_THRESHOLD
        )
        assert any("zgodne" in p for p in problems)


class TestNegativeC_PatternANoMatches:
    """(c) tekst bez dopasowan dla wzorca A -> FAIL, nie PASS."""

    def test_stripping_pattern_a_anchors_fails_not_passes(self):
        redacted_prereg = re.sub(r"redukcj\w*", "XXXXX", REAL_PREREG_TEXT, flags=re.IGNORECASE)
        redacted_prereg = redacted_prereg.replace("Warunek B", "XXXXX").replace("**B**", "XXXXX")
        redacted_aneks1 = re.sub(r"redukcj\w*", "XXXXX", REAL_ANEKS1_TEXT, flags=re.IGNORECASE)
        redacted_aneks1 = redacted_aneks1.replace("Warunek B", "XXXXX").replace("**B**", "XXXXX")
        assert find_pattern_a(redacted_prereg) == []
        assert find_pattern_a(redacted_aneks1) == []
        problems = verify_threshold_provenance(
            redacted_prereg, redacted_aneks1, CONDITION_B_REDUCTION_THRESHOLD
        )
        assert any("wzorzec A" in p for p in problems)


class TestNegativeD_PatternBNoMatches:
    """(d) tekst bez dopasowan dla wzorca B -> FAIL, nie PASS."""

    def test_stripping_pattern_b_anchors_fails_not_passes(self):
        redacted_aneks1 = re.sub(r"konwencj\w*", "XXXXX", REAL_ANEKS1_TEXT, flags=re.IGNORECASE)
        assert find_pattern_b(redacted_aneks1) == []
        assert find_pattern_b(REAL_PREREG_TEXT) == []  # prereg nigdy nie mial dopasowan B
        problems = verify_threshold_provenance(
            REAL_PREREG_TEXT, redacted_aneks1, CONDITION_B_REDUCTION_THRESHOLD
        )
        assert any("wzorzec B" in p for p in problems)
