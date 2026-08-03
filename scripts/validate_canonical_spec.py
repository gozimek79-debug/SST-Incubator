"""Walidator SPECYFIKACJI KANONICZNEJ PC-001 (SPECYFIKACJA_KANONICZNA_PC_001_v1.0.md).

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

from scripts.spec_md_to_json import convert

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_MD = REPO_ROOT / "SPECYFIKACJA_KANONICZNA_PC_001_v1.0.md"
SPEC_JSON = REPO_ROOT / "SPECYFIKACJA_KANONICZNA_PC_001_v1.0.json"
HALT_PATH = REPO_ROOT / "execution_package_v0_11" / "validators" / "hard_halt.py"

SHORTCUTS = {
    "PC-001": "publications/preregistration_PC_001.md",
    "A1": "publications/preregistration_PC_001_ANEKS_1_2026-07-28.md",
    "A2": "publications/preregistration_PC_001_ANEKS_2_2026-07-28.md",
    "A3": "publications/preregistration_PC_001_ANEKS_3_2026-07-28.md",
    "A4": "publications/preregistration_PC_001_ANEKS_4_2026-07-28.md",
    "A5": "publications/preregistration_PC_001_ANEKS_5_2026-07-28.md",
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
    return problems


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
    problems = []
    for _sec, _blk, text, _col in iter_texts(spec_data):
        for m in SECTION_ADDR_RE.finditer(text):
            token, num = m.group(1), m.group(2)
            path = _file_for_token(token)
            if not resolve_section_in_file(path, num):
                problems.append(f"{token} §{num} nie rozwiazuje sie do sekcji w {path.name}")
    return problems


def check_fragment_addresses(spec_data):
    problems = []
    for _sec, _blk, text, _col in iter_texts(spec_data):
        for m in FRAGMENT_ADDR_RE.finditer(text):
            token, fragment = m.group(1), m.group(2)
            path = _file_for_token(token)
            if not resolve_fragment_in_file(path, fragment):
                problems.append(f'{token} → "{fragment}" nie rozwiazuje sie w {path.name}')
    return problems


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
    problems = []
    for _sec, _blk, text, _col in iter_texts(spec_data):
        for m in SYMBOL_ADDR_RE.finditer(text):
            token, symbol = m.group(1), m.group(2)
            path = _file_for_token(token)
            if not resolve_symbol_in_file(path, symbol):
                problems.append(f"{token}::{symbol} nie rozwiazuje sie w {path.name}")
    return problems


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
    problems = []
    for section, _blk, text, col in iter_texts(spec_data):
        for start, token in find_c001_violations_in_text(text, column=col):
            snippet = text[max(0, start - 20) : start + 20].strip()
            problems.append(f"§{section['id']}: liczba '{token}' w kontekscie wartosci: ...{snippet}...")
    return problems


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
    critical_files = load_critical_files()
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


def main():
    if not SPEC_MD.exists():
        print(f"BRAK: {SPEC_MD}")
        return 1
    spec_data = convert(SPEC_MD.read_text(encoding="utf-8"), SPEC_MD.name)
    results = run_all_checks(spec_data)
    all_ok = True
    for name, problems in results.items():
        if problems:
            all_ok = False
            print(f"FAIL {name} ({len(problems)}):")
            for p in problems[:30]:
                print(f"  - {p}")
        else:
            print(f"PASS {name}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
