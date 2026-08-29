"""Walidator SPECYFIKACJI KANONICZNEJ PC-001 (SPECYFIKACJA_KANONICZNA_PC_001.md).

Niezalezna implementacja wzgledem prototypu audytora (validate_canonical_spec.py,
root repo, material referencyjny - nie do wklejenia). Uruchamiany przeciw swiezemu
klonowi; ma byc wpiety do CI jako brama zielonej galezi (patrz specyfikacja §8.1).

Sprawdzenia (numeracja zgodna ze specyfikacja §9, gdzie to mozliwe):
  1. kazdy adres pliku (skrot z SHORTCUTS + sciezka w odwrotnym apostrofie) istnieje w repo
  2. kazdy adres `plik §N` i `plik -> "fragment"` rozwiazuje sie do sekcji/fragmentu
  3. kazdy adres `plik::SYMBOL` rozwiazuje sie do symbolu zdefiniowanego w module (AST, bez importu)
  4. C-001: dokument nie zawiera liczby w kontekscie wartosci (progu/podlogi/licznosci/odsetka)
  5. kazda pozycja CRITICAL_FILES_PC_001 jest opisana (wprost, przez prefiks katalogu w §2.12,
     albo przez blizniacze .md/.json) gdziekolwiek w §2 (rejestr normatywny)
  6. JSON zgadza sie z markdownem - NIE przez hash, przez regeneracje w pamieci i porownanie
     strukturalne (patrz decyzja w scripts/spec_md_to_json.py, docstring modulu)

ZNANE OGRANICZENIE, CELOWO NIE "NAPRAWIANE" (spec §8.1): kompletnosc mapy §4 (tresci
nieobowiazujacych w zamrozonych zrodlach) nie jest tu sprawdzana. Usuniecie wiersza z §4
nie zepsuje zadnego z powyzszych testow - zadne z nich nie liczy wierszy §4 ani nie ma
zrodla, z ktorym by je porownac. To jest udokumentowana luka, nie przeoczenie: nie da sie
mechanicznie stwierdzic, ze mapa "nieobowiazujacych fragmentow" jest kompletna, bo nie ma
niezaleznego zrodla prawdy o tym, co POWINNO tam byc.

Filtr C-001 (test 4) jest jedynym miejscem w tym pliku, gdzie kazdy dodany wyjatek
przyblizamy do "przepuszczania wszystkiego" (patrz spec §9). Wyjatki sa scisle wymienione
i uzasadnione w komentarzach przy find_c001_violations_in_text(); kazdy ma test negatywny
w tests/test_validate_canonical_spec.py, ktory dowodzi, ze mimo wyjatku prawdziwa wartosc
(prog, podloga, licznosc, odsetek) nadal zostaje zlapana.
"""

import ast
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

try:
    from scripts.spec_md_to_json import convert
except ImportError:
    # Uruchomienie jako `python scripts/validate_canonical_spec.py` (zamiast
    # `python -m scripts.validate_canonical_spec`, tak jak robi CI) nie dodaje
    # katalogu repo do sys.path, wiec pakiet `scripts` jest niewidoczny. Nie jest
    # to defekt CI (dziala poprawnie), ale narzedzie majace bronic dokumentu przed
    # rozjazdem nie powinno konczyc sie surowym tracebackiem przy najbardziej
    # naturalnym wywolaniu (audyt commita 661b92a, punkt 4, opcjonalny).
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.spec_md_to_json import convert
SPEC_MD = REPO_ROOT / "SPECYFIKACJA_KANONICZNA_PC_001.md"
SPEC_JSON = REPO_ROOT / "SPECYFIKACJA_KANONICZNA_PC_001.json"
HALT_PATH = REPO_ROOT / "execution_package_v0_11" / "validators" / "hard_halt.py"

SHORTCUTS = {
    "PC-001": "publications/preregistration_PC_001.md",
    "A1": "publications/preregistration_PC_001_ANEKS_1_2026-07-28.md",
    "A2": "publications/preregistration_PC_001_ANEKS_2_2026-07-28.md",
    "A3": "publications/preregistration_PC_001_ANEKS_3_2026-07-28.md",
    "A4": "publications/preregistration_PC_001_ANEKS_4_2026-07-28.md",
    "A5": "publications/preregistration_PC_001_ANEKS_5_2026-07-28.md",
    # A6 ma inna date w nazwie niz A1-A5, wiec {1..5} (SHORTCUTS-tabela §1) go nie
    # obejmuje - osobny wpis, wzorem A1-A5.
    "A6": "publications/preregistration_PC_001_ANEKS_6_2026-08-03.md",
    # E1 (B4C-2 (09)): ERRATUM, nie ANEKS - poprawka do zamrozonego A1 (K4-separacja,
    # sciezka shock_world/noise_world), nie doprecyzowanie. A1 pozostaje NIETKNIETY;
    # E1 nadpisuje go normatywnie (adresy w §2 kieruja tu jako brzmienie obowiazujace).
    "E1": "publications/preregistration_PC_001_ERRATUM_1_2026-08-27.md",
    # E2 (B4C-2 (12)): ERRATUM do power_analysis_PC_001.json (N_OPERATIONAL_SEEDS
    # 8 -> 9). power_analysis_PC_001.json samo NIE ma skrotu - POZA rejestrem,
    # nie jest adresowane z §2 poza tym erratum.
    "E2": "publications/preregistration_PC_001_ERRATUM_2_2026-08-29.md",
    # E3 (B4C-2 (15)): ERRATUM do reguly decyzyjnej - szesc komorek (K1/K4/K5,
    # obie czesci) przechodzi z "brak odrzucenia H0" (ANEKS 1 warunki 4/7/8,
    # PC-001 §5 K1/K4/K5) na wnioskowanie o rownowaznosci (TOST, c=0.10).
    # ANEKS 1 i PC-001 pozostaja NIETKNIETE; E3 nadpisuje je normatywnie.
    "E3": "publications/preregistration_PC_001_ERRATUM_3_2026-08-29.md",
    "W2-SPEC": "publications/specyfikacja_W2_2026-07-28.md",
    "FLOOR": "publications/analiza_floor_model_2026-07-28.md",
    "B4": "publications/NOTATKA_B4_ANALIZA_MOCY_2026-07-28.md",
    "W2-REPORT": "publications/W2_completion_report_2026-07-28.md",
    "GOV": "docs/GOVERNANCE_RULES.md",
    "CONFIG": "clos_scientist/pc_001_experiment_config.py",
    "ENDPOINT": "clos_scientist/w2_endpoint.py",
    "FLOOR-MOD": "clos_world/floor_model.py",
    "HALT": "execution_package_v0_11/validators/hard_halt.py",
    "K7-MOD": "clos_scientist/fallback_branch_diagnostic.py",
    "STATS": "clos_curriculum/laboratory/statistics.py",
    # v1.2 (D-031, §1): dokumenty uzasadniajace objete rejestrem CRITICAL_FILES_PC_001.
    "SPRINT": "SPRINT_v0.11.0.md",
    "BEZP": "publications/BEZPIECZENSTWO_POMIARU_recovery_spearman.md",
}
_SHORTCUT_ALT = "|".join(re.escape(k) for k in sorted(SHORTCUTS, key=len, reverse=True))

SECTION_ADDR_RE = re.compile(rf"\b({_SHORTCUT_ALT})\s*§\s*(\d+(?:\.\d+)*[a-z]?)")
FRAGMENT_ADDR_RE = re.compile(rf"\b({_SHORTCUT_ALT})\s*→\s*[„\"]([^\"”]+)[\"”]")
SYMBOL_ADDR_RE = re.compile(rf"\b({_SHORTCUT_ALT})::([A-Za-z_][A-Za-z0-9_]*)")
BACKTICK_RE = re.compile(r"`([^`]+)`")
PATH_EXT_RE = re.compile(r"\.(?:py|md|json|txt|ya?ml|jsx|bat)\b")


def _looks_like_file_path(candidate):
    """Odroznienie adresu pliku od formuly zawierajacej '/' (np. dzielenie)."""
    return "/" in candidate and PATH_EXT_RE.search(candidate) is not None
HEADER_LINE_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
BRACE_RANGE_RE = re.compile(r"\{(\d+)\.\.(\d+)\}")


def _expand_brace_range(candidate):
    """'ANEKS_{1..5}_x.md' -> ['ANEKS_1_x.md', ..., 'ANEKS_5_x.md']. Bez zakresu: [candidate]."""
    m = BRACE_RANGE_RE.search(candidate)
    if not m:
        return [candidate]
    lo, hi = int(m.group(1)), int(m.group(2))
    return [candidate[: m.start()] + str(i) + candidate[m.end() :] for i in range(lo, hi + 1)]

# --- test 4 (C-001): wzorce uzywane do wykluczenia adresow z detekcji "liczby w wartosci" ---
QUOTED_FRAGMENT_RE = re.compile(r"[„\"][^\"”]*[\"”]")  # nazwy fragmentow (notacja §1) - adresy, nie wartosci
PATH_LIKE_RE = re.compile(r"[\w./{}*~-]*/[\w./{}*~-]*\.(?:py|md|json|txt|ya?ml|jsx|bat)\b")
# zakres sekcji/pozycji: "§2.2-2.3", "Sekcje 2.1-2.11", "pozycji 7-10" - maskowany W CALOSCI,
# obie liczby zakresu naraz (druga liczba nie jest bezposrednio poprzedzona wyzwalaczem)
RANGE_REF_RE = re.compile(
    r"(?:§\s*|\b(?:Sekcj|pozycj)\w*\s+)\d+(?:\.\d+)*\s*[-–]\s*\d+(?:\.\d+)*",
    re.IGNORECASE,
)
# maksymalny "sklejony" token: litery+cyfry+kropki+podkreslenia+myslniki razem.
# Jesli token zawiera choc jedna litere - to identyfikator (L1.1, K3a, D-017, v0.11,
# PC-001), nigdy kandydat na wartosc. To odrozina to od poprzedniej wersji filtra opartej
# o "sasiedztwo znaku": ta wersja poprawnie odrzuca CALY sklejony token, nie tylko jego
# czesc bezposrednio przy literze (bug zlapany na realnym dokumencie: "L1.1" zostawialo
# drugie "1" jako pozorny kandydat, bo tylko pierwsza cyfra byla sklejona z litera).
TOKEN_RE = re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9_.\-]+")
PURE_NUMBER_RE = re.compile(r"\d+(?:\.\d+)*")
# slowa-wyzwalacze odwolan do wlasnej numeracji dokumentu (nie wartosci eksperymentu):
# punkt/pkt (punkty wyliczenia), nr (numer testu), pozycja (wiersz mapy/rejestru),
# warunek (warunek K3a 1/2), test (numeracja testow w §9), Sekcja (odwolanie do zakresu sekcji)
REFERENCE_WORD_RE = re.compile(r"\b(?:pkt\.?|punkt\w*|nr\.?|pozycj\w*|warun\w*|test\w*|Sekcj\w*)\b", re.IGNORECASE)
PRECEDED_BY_ADDRESS_MARKER_RE = re.compile(r"(?:§\s*|\b(?:pkt|nr)\.?\s*)$", re.IGNORECASE)


def _file_for_token(token):
    if token in SHORTCUTS:
        return REPO_ROOT / SHORTCUTS[token]
    return REPO_ROOT / token


def iter_texts(spec_data):
    """(sekcja, blok, tekst, nazwa_kolumny_lub_None) dla kazdego fragmentu tresci dokumentu."""
    for section in spec_data["sections"]:
        for block in section["blocks"]:
            btype = block["type"]
            if btype in ("paragraph", "note", "code"):
                yield section, block, block["text"], None
            elif btype == "list":
                for item in block["items"]:
                    yield section, block, item, None
            elif btype == "table":
                for row in block["rows"]:
                    for col, val in row.items():
                        yield section, block, val, col


# --- test 1: adresy plikow ---


def check_file_addresses(spec_data):
    """UWAGA (B4C-05 v5/v6, znalezisko CTO): pusta lista problemow ze skrotow
    (SHORTCUTS) NIGDY nie moze wynikac z 'nic nie sprawdzono' - SHORTCUTS jest
    stalym, niepustym slownikiem (len()>0 zawsze), wiec ta czesc kontroli jest
    ODPORNA na wektor 'zero dopasowan = ciche PASS' z definicji. Druga czesc
    (adresy plikow w odwrotnych apostrofach w PROZIE dokumentu) NIE jest
    odporna - zniszczenie notacji (albo usuniecie wszystkich adresow z prozy)
    dalyby zero kandydatow i ciche PASS. Stad jawny prog: co najmniej jeden
    adres pliku w prozie musi zostac znaleziony, inaczej FAIL (nie PASS)."""
    problems = []
    for shortcut, rel_path in SHORTCUTS.items():
        if not (REPO_ROOT / rel_path).exists():
            problems.append(f"skrot {shortcut} -> {rel_path} nie istnieje w repo")
    seen = set()
    for _sec, _blk, text, _col in iter_texts(spec_data):
        for m in BACKTICK_RE.finditer(text):
            candidate = m.group(1)
            if candidate.endswith("/"):
                pass  # prefiks katalogu - sprawdzany dalej bez wymogu rozszerzenia
            elif not _looks_like_file_path(candidate):
                continue  # np. formula '(a - b) / c' - nie jest adresem pliku
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate.endswith("/"):
                continue  # prefiks katalogu, nie pojedynczy plik - patrz test 5
            for expanded in _expand_brace_range(candidate):
                if "*" in expanded:
                    if not list(REPO_ROOT.glob(expanded)):
                        problems.append(f"wzorzec {expanded} nie pasuje do zadnego pliku")
                elif not (REPO_ROOT / expanded).exists():
                    problems.append(f"adres pliku {expanded} nie istnieje w repo")
    if not seen:
        problems.append(
            "ZERO adresow plikow w odwrotnych apostrofach znalezionych w prozie "
            "dokumentu - dokument jest albo pusty, albo notacja adresow zostala "
            "zniszczona (B4C-05 v5: pusta lista problemow z tego powodu NIE "
            "oznacza poprawnosci, tylko brak czegokolwiek do sprawdzenia)"
        )
    return problems


def count_file_address_candidates(spec_data):
    """Do raportowania resolved_count w main() - nie zmienia kontraktu
    check_file_addresses (lista problemow, bez zmian sygnatury dla
    istniejacych wywolujacych)."""
    seen = set()
    for _sec, _blk, text, _col in iter_texts(spec_data):
        for m in BACKTICK_RE.finditer(text):
            candidate = m.group(1)
            if not candidate.endswith("/") and not _looks_like_file_path(candidate):
                continue
            seen.add(candidate)
    return len(SHORTCUTS), len(seen)


# --- test 2: adresy sekcji i fragmentow ---


def resolve_section_in_file(path, section_num):
    """N jako naglowek 'N. ...' / 'N)' (styl PC-001, W2-SPEC, ...) LUB '§N ...' (styl GOV)."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    for m in HEADER_LINE_RE.finditer(text):
        title = m.group(1).strip()
        if re.match(re.escape(section_num) + r"[.)]?\s", title):
            return True
        if re.match(r"§\s*" + re.escape(section_num) + r"\b", title):
            return True
    return False


def resolve_fragment_in_file(path, fragment):
    """Fragment jako tytul naglowka (prefiks) LUB wytluszczony lead akapitu (notacja §1)."""
    if not path.exists():
        return False
    data = convert(path.read_text(encoding="utf-8"), path.name)
    fragment_norm = fragment.strip()
    for section in data["sections"]:
        title = section["title"].strip()
        if title == fragment_norm or title.startswith(fragment_norm):
            return True
        for block in section["blocks"]:
            lead = block.get("lead")
            if lead and (lead == fragment_norm or lead.startswith(fragment_norm)):
                return True
    return False


def check_section_addresses(spec_data):
    """B4C-05 v5/v6: zniszczenie notacji '§' (np. zamiana na 'par.') daje ZERO
    dopasowan SECTION_ADDR_RE - petla nizej po prostu nie wykonuje sie ani razu,
    a pusta lista problemow wygladalaby identycznie jak 'wszystko sie rozwiazalo'.
    Prog >=1 dopasowanie (BEZ przypinania konkretnej liczby - kryterium to
    'co najmniej jeden', nie 'dokladnie N', wzorem Z9C) odroznia te dwa stany."""
    problems = []
    n_matches = 0
    for _sec, _blk, text, _col in iter_texts(spec_data):
        for m in SECTION_ADDR_RE.finditer(text):
            n_matches += 1
            token, num = m.group(1), m.group(2)
            path = _file_for_token(token)
            if not resolve_section_in_file(path, num):
                problems.append(f"{token} §{num} nie rozwiazuje sie do sekcji w {path.name}")
    if n_matches == 0:
        problems.append(
            "ZERO adresow sekcji (PLIK §N) znalezionych w dokumencie - notacja "
            "adresow jest albo zniszczona, albo dokument jest pusty (B4C-05 v5)"
        )
    return problems


def check_fragment_addresses(spec_data):
    """Ta sama podatnosc i to samo zabezpieczenie co check_section_addresses -
    dla notacji 'PLIK → "fragment"'."""
    problems = []
    n_matches = 0
    for _sec, _blk, text, _col in iter_texts(spec_data):
        for m in FRAGMENT_ADDR_RE.finditer(text):
            n_matches += 1
            token, fragment = m.group(1), m.group(2)
            path = _file_for_token(token)
            if not resolve_fragment_in_file(path, fragment):
                problems.append(f'{token} → "{fragment}" nie rozwiazuje sie w {path.name}')
    if n_matches == 0:
        problems.append(
            "ZERO adresow fragmentow (PLIK → \"fragment\") znalezionych w dokumencie "
            "- notacja adresow jest albo zniszczona, albo dokument jest pusty (B4C-05 v5)"
        )
    return problems


def count_section_matches(spec_data):
    return sum(1 for _s, _b, text, _c in iter_texts(spec_data) for _ in SECTION_ADDR_RE.finditer(text))


def count_fragment_matches(spec_data):
    return sum(1 for _s, _b, text, _c in iter_texts(spec_data) for _ in FRAGMENT_ADDR_RE.finditer(text))


# --- test 3: adresy symboli ---


def resolve_symbol_in_file(path, symbol):
    """Odczyt statyczny przez AST - bez importu modulu (ten sam wzorzec co generator raportu)."""
    if not path.exists():
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                return True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol:
                    return True
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == symbol:
                return True
    return False


def check_symbol_addresses(spec_data):
    """Ta sama podatnosc i to samo zabezpieczenie co check_section_addresses -
    dla notacji 'PLIK::SYMBOL' (B4C-05 v5/v6)."""
    problems = []
    n_matches = 0
    for _sec, _blk, text, _col in iter_texts(spec_data):
        for m in SYMBOL_ADDR_RE.finditer(text):
            n_matches += 1
            token, symbol = m.group(1), m.group(2)
            path = _file_for_token(token)
            if not resolve_symbol_in_file(path, symbol):
                problems.append(f"{token}::{symbol} nie rozwiazuje sie w {path.name}")
    if n_matches == 0:
        problems.append(
            "ZERO adresow symboli (PLIK::SYMBOL) znalezionych w dokumencie - "
            "notacja adresow jest albo zniszczona, albo dokument jest pusty (B4C-05 v5)"
        )
    return problems


def count_symbol_matches(spec_data):
    return sum(1 for _s, _b, text, _c in iter_texts(spec_data) for _ in SYMBOL_ADDR_RE.finditer(text))


# --- test 4: C-001 (zero wartosci) ---


def _mask(text, pattern):
    return pattern.sub(lambda m: " " * len(m.group(0)), text)


def _is_line_leading_ordinal(text, start, end):
    """'N. ' na poczatku fizycznej linii - marker listy numerowanej (np. blok kodu
    "Kolejnosc wykonania": '1. Specyfikacja...', '2. K3a...'), nie wartosc."""
    line_start = text.rfind("\n", 0, start) + 1
    if text[line_start:start].strip() != "":
        return False
    return text[end : end + 1] == "."


def find_c001_violations_in_text(text, column=None):
    """Zwraca liste (pozycja, token) liczb w kontekscie wartosci - naruszenie C-001.

    Wyjatki (kazdy wazony osobno, patrz docstring modulu i testy negatywne):
      - kolumna tabeli '#' (indeks wiersza, nie wartosc)
      - tresc wewnatrz cudzyslowow „..." / "..." - nazwa fragmentu (notacja §1)
      - sciezka pliku (zawiera '/', konczy sie znanym rozszerzeniem)
      - zakres sekcji/pozycji poprzedzony '§'/'Sekcj...'/'pozycj...' (np. "§2.2-2.3")
      - token sklejony z litera (L1.1, K3a, D-017, v0.11, PC-001) - to identyfikator,
        nie liczba - sprawdzane na CALYM sklejonym tokenie, nie pojedynczym znaku
      - liczba bezposrednio poprzedzona '§'/'pkt'/'nr'
      - liczba calkowita (bez kropki) w bloku zawierajacym gdziekolwiek slowo z
        REFERENCE_WORD_RE (pkt/punkt/nr/pozycja/warunek/test/sekcja) - odwolanie do
        wlasnej numeracji dokumentu, nie do wartosci eksperymentu
      - 'N.' na poczatku linii - marker listy numerowanej
      - doslowna "0" - stala formuly (`max(0, x)`, `β < 0`), nigdy nie jest sama w sobie
        progiem/podloga/licznoscia/odsetkiem w tym projekcie (te zawsze maja > 0)
    Percent ('N%') NIGDY nie jest wyjatkiem - odsetek jest jawnie zakazany przez C-001
    niezaleznie od kontekstu, nawet wewnatrz bloku z ktoryms z powyzszych slow-wyzwalaczy.
    """
    if column == "#":
        return []
    masked = _mask(text, QUOTED_FRAGMENT_RE)
    masked = _mask(masked, PATH_LIKE_RE)
    masked = _mask(masked, RANGE_REF_RE)
    block_has_reference_word = bool(REFERENCE_WORD_RE.search(masked))

    violations = []
    for m in TOKEN_RE.finditer(masked):
        token = m.group(0)
        if not PURE_NUMBER_RE.fullmatch(token):
            continue  # zawiera litere/podkreslenie - identyfikator, nie liczba
        start, end = m.start(), m.end()
        after_char = masked[end : end + 1]
        before = masked[max(0, start - 12) : start]

        if after_char == "%":
            violations.append((start, token))
            continue
        if token == "0":
            continue
        if PRECEDED_BY_ADDRESS_MARKER_RE.search(before):
            continue
        if _is_line_leading_ordinal(masked, start, end):
            continue
        if "." not in token and block_has_reference_word:
            continue
        violations.append((start, token))
    return violations


def check_c001(spec_data):
    """B4C-05 v5: ZERO naruszen jest tu ZAMIERZONYM, poprawnym wynikiem (C-001
    mowi, ze dokument nie powinien niesc wartosci) - w odroznieniu od kontroli
    2/3, gdzie zero dopasowan jest podejrzane. Ale zero PRZESKANOWANYCH
    fragmentow tekstu (n_scanned) to INNY sygnal - dokument pusty albo
    nie sparsowal sie w ogole - i TO jest sprawdzane osobno, zeby nie pomylic
    'sprawdzilem i jest czysto' z 'nie mialem czego sprawdzac'."""
    problems = []
    n_scanned = 0
    for section, _blk, text, col in iter_texts(spec_data):
        n_scanned += 1
        for start, token in find_c001_violations_in_text(text, column=col):
            snippet = text[max(0, start - 20) : start + 20].strip()
            problems.append(f"§{section['id']}: liczba '{token}' w kontekscie wartosci: ...{snippet}...")
    if n_scanned == 0:
        problems.append(
            "ZERO fragmentow tekstu przeskanowanych - dokument jest pusty albo "
            "nie sparsowal sie poprawnie (B4C-05 v5)"
        )
    return problems


def count_scanned_text_fragments(spec_data):
    return sum(1 for _ in iter_texts(spec_data))


# --- test 5: pokrycie rejestru plikow krytycznych ---


def load_critical_files():
    """Odczyt CRITICAL_FILES_PC_001 przez AST (bez importu HALT)."""
    tree = ast.parse(HALT_PATH.read_text(encoding="utf-8"), filename=str(HALT_PATH))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CRITICAL_FILES_PC_001":
                    return ast.literal_eval(node.value)
    raise RuntimeError("CRITICAL_FILES_PC_001 nie znaleziony w " + str(HALT_PATH))


def _section_in_registry_chapter(section):
    sid = section["id"]
    return sid == "2" or sid.startswith("2.")


def _collect_covered_paths_and_prefixes(spec_data):
    covered_paths = set()
    covered_prefixes = set()
    for section, _blk, text, _col in iter_texts(spec_data):
        if not _section_in_registry_chapter(section):
            continue
        for shortcut, rel_path in SHORTCUTS.items():
            if re.search(rf"(?<![\w-]){re.escape(shortcut)}(?![\w-])", text):
                covered_paths.add(rel_path)
        for m in BACKTICK_RE.finditer(text):
            candidate = m.group(1)
            if candidate.endswith("/"):
                covered_prefixes.add(candidate)
            elif "/" in candidate:
                covered_paths.add(candidate.replace("*", ""))
    twins = set()
    for p in covered_paths:
        if p.endswith(".md"):
            twins.add(p[:-3] + ".json")
        elif p.endswith(".json"):
            twins.add(p[:-5] + ".md")
    covered_paths |= twins
    return covered_paths, covered_prefixes


def check_critical_files_registry_coverage(spec_data):
    """B4C-05 v5: NIE podatna na 'zero dopasowan = ciche PASS' w tym samym
    sensie co kontrole 2/3 - ta kontrola iteruje po CRITICAL_FILES_PC_001
    (staly, niepusty rejestr - licznosc rosnie w czasie, patrz hard_halt.py),
    nie po dopasowaniach regex w prozie. Gdyby cale pokrycie (covered_paths/
    covered_prefixes) znikneło, KAZDY plik z rejestru trafilby na liste
    'missing' - kontrola FAILUJE glosno, nie PASSuje cicho. Guard na pusty
    rejestr ponizej to obrona defensywna, nie naprawa
    tej samej luki - rejestr pusty oznaczalby zepsuty HALT, inny rodzaj bledu."""
    critical_files = load_critical_files()
    if not critical_files:
        return ["CRITICAL_FILES_PC_001 jest pusta - rejestr, od ktorego zalezy ta kontrola, nie istnieje"]
    covered_paths, covered_prefixes = _collect_covered_paths_and_prefixes(spec_data)
    missing = []
    for cf in critical_files:
        if cf in covered_paths:
            continue
        if any(cf.startswith(prefix) for prefix in covered_prefixes):
            continue
        missing.append(cf)
    return [f"{cf} jest w CRITICAL_FILES_PC_001, ale nieopisany w §2 specyfikacji" for cf in missing]


# --- test 6: zgodnosc JSON z markdownem (regeneracja w pamieci, bez hasha) ---


def check_json_matches_markdown(md_path=SPEC_MD, json_path=SPEC_JSON):
    if not md_path.exists():
        return [f"{md_path} nie istnieje"]
    regenerated = convert(md_path.read_text(encoding="utf-8"), md_path.name)
    if not json_path.exists():
        return [f"{json_path} nie istnieje - uruchom: python scripts/spec_md_to_json.py {md_path.name}"]
    try:
        committed = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{json_path} nie jest poprawnym JSON-em: {exc}"]
    if regenerated != committed:
        return [
            f"{json_path.name} rozjechal sie z {md_path.name} - zregeneruj przez "
            "`python scripts/spec_md_to_json.py` (markdown zmieniono bez regeneracji "
            "JSON-a, albo JSON edytowano recznie)"
        ]
    return []


CHECKS = [
    ("1_adresy_plikow", check_file_addresses),
    ("2_adresy_sekcji_i_fragmentow", lambda d: check_section_addresses(d) + check_fragment_addresses(d)),
    ("3_adresy_symboli", check_symbol_addresses),
    ("4_C001_zero_wartosci", check_c001),
    ("5_pokrycie_rejestru_plikow_krytycznych", check_critical_files_registry_coverage),
    ("6_json_zgodny_z_markdownem", lambda d: check_json_matches_markdown()),
]


def run_all_checks(spec_data):
    """Zwraca {nazwa_testu: [problemy]} dla wszystkich testow (puste [] = PASS)."""
    return {name: fn(spec_data) for name, fn in CHECKS}


def resolved_count_label(name, spec_data):
    """B4C-05 v5/v6 pkt 3: liczba rozwiazanych/przeskanowanych elementow per
    kontrola, wypisywana NAWET przy PASS - nagly spadek (np. 25 -> 3) ma byc
    widoczny dla czlowieka, mimo ze formalnie nadal przechodzi prog >=1."""
    if name == "1_adresy_plikow":
        n_shortcuts, n_paths = count_file_address_candidates(spec_data)
        return f"resolved={n_shortcuts + n_paths} ({n_shortcuts} skrotow + {n_paths} adresow plikow w prozie)"
    if name == "2_adresy_sekcji_i_fragmentow":
        n_sec = count_section_matches(spec_data)
        n_frag = count_fragment_matches(spec_data)
        return f"resolved={n_sec + n_frag} ({n_sec} sekcji + {n_frag} fragmentow)"
    if name == "3_adresy_symboli":
        return f"resolved={count_symbol_matches(spec_data)}"
    if name == "4_C001_zero_wartosci":
        return f"przeskanowano={count_scanned_text_fragments(spec_data)} fragmentow"
    if name == "5_pokrycie_rejestru_plikow_krytycznych":
        n = len(load_critical_files())
        return f"resolved={n}/{n} plikow krytycznych"
    if name == "6_json_zgodny_z_markdownem":
        return "resolved=1 (pelne porownanie strukturalne JSON<->markdown)"
    return ""


def main():
    if not SPEC_MD.exists():
        print(f"BRAK: {SPEC_MD}")
        return 1
    spec_data = convert(SPEC_MD.read_text(encoding="utf-8"), SPEC_MD.name)
    results = run_all_checks(spec_data)
    all_ok = True
    for name, problems in results.items():
        label = resolved_count_label(name, spec_data)
        if problems:
            all_ok = False
            print(f"FAIL {name} ({len(problems)}) {label}:")
            for p in problems[:30]:
                print(f"  - {p}")
        else:
            print(f"PASS {name} - {label}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
