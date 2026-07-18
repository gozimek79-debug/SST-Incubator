"""Validate Panel - skanuje clos_studio/panel/panel.js pod katem wklejonych
metryk (SPRINT_v0.8.5.md, Priorytet 3) ORAZ, od SPRINT_v0.11.0.md (decyzja
CTO 2026-07-18), pod katem dwoch dodatkowych sposobow, w jakie panel moze
"rozjechac sie" z Pythonem bez cracha i bez ostrzezenia:

  (A) REIMPLEMENTACJA KLASYFIKACJI. Python (clos_scientist/competency_profile.py)
      jest JEDYNYM zrodlem klasyfikacji valid/degenerate/insufficient - panel
      MA ja czytac (comp.full_profile.valid/degenerate/insufficient_data),
      NIE liczyc samodzielnie z progow typu "wszystkie genomy ci95_valid=true".
      Historia: przed tym sprintem panel liczyl to sam
      (competencyRowState()), wiec zmiana ontologii (6 osi poznawczych + 1
      zmienna stanu fizjologicznego) w Pythonie NIE dotarla do panelu -
      "artefakt != kod" w warstwie widoku, niewykryte przez zaden test.
      Jedyny dopuszczalny wyjatek: funkcja jawnie nazwana
      "_fallbackClassifyConcepts" (uzywana WYLACZNIE gdy stary/niezgodny
      competency_profile.json nie ma pola full_profile) - poza jej cialem,
      wzorce typu ".every(...ci95_valid...)" lub "ci95_valid ===" lub
      "n_effective >=/<=/>/<" sa FAILEM.
  (B) CZYTANIE KLUCZA, KTOREGO NIE MA W competency_profile.json. Panel
      czyta ten plik przez zmienne o ustalonych, jednoznacznych nazwach
      (comp = caly profil, c = pojedynczy koncept, gd = per-genom staty
      koncepta, obs = pojedyncza secondary_observation, gs = per-genom
      staty wewnatrz secondary_observation). Kazdy sciezka comp.a.b.c /
      c.x.y / itd. znaleziona w kodzie MUSI istniec w REALNYM
      publications/competency_profile.json (sprawdzane wzgledem
      reprezentatywnego ksztaltu, bo concepts/genomes to listy/slowniki o
      zmiennych kluczach) - inaczej FAIL. To lapie DOKLADNIE ten rodzaj
      bledu: panel czyta pole, ktorego Python przestal produkowac (lub
      nigdy nie produkowal), bez zadnego ostrzezenia w CI.

Uzycie:
    python scripts/validate_panel.py
Kod wyjscia: 0 = czysto, 1 = znaleziono podejrzana wklejona metryke,
reimplementacje klasyfikacji, lub odczyt nieistniejacego klucza.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PANEL_JS = Path("clos_studio/panel/panel.js")
COMPETENCY_PROFILE = Path("publications/competency_profile.json")

STRING_LITERAL_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
URL_OR_PATH_RE = re.compile(r'^https?://|^[\w.\-]+/[\w./\-]+$')

FLOAT_RE = re.compile(r'\b\d+\.\d{4,}\b')
HEX_RE = re.compile(r'\b[0-9a-fA-F]{16,}\b')
KNOWN_COUNT_RE = re.compile(r'(?<!\d)263(?!\d)')

FALLBACK_FN_NAME = "_fallbackClassifyConcepts"
CLASSIFICATION_COMPARISON_RE = re.compile(r'ci95_valid\s*(===|!==|==|!=)|n_effective\s*(>=|<=|>|<)')
CLASSIFICATION_ITERATION_RE = re.compile(r'\.(every|some|filter)\([^;]{0,300}?ci95_valid', re.DOTALL)

# Zmienne o jednoznacznym, ustalonym znaczeniu w panel.js (patrz docstring
# modulu, punkt B) - kazda z nich MUSI zawsze wskazywac na ten sam ksztalt
# danych wszedzie w pliku, inaczej ten walidator dawalby falszywe alarmy.
CHAIN_ROOTS = ["comp", "c", "gd", "obs", "gs"]
CHAIN_RE = re.compile(r'\b(' + "|".join(CHAIN_ROOTS) + r')((?:\.[A-Za-z_]\w*)+)')

# Wlasciwosci/metody JS wbudowane w Array/Object/String - NIE sa kluczami
# JSON, ucinaja lancuch w tym miejscu (nie sprawdzane dalej).
JS_BUILTIN_STOP = {
    "length", "map", "filter", "forEach", "join", "push", "every", "some",
    "indexOf", "slice", "concat", "reduce", "sort", "includes", "find",
    "findIndex", "toString", "hasOwnProperty", "call", "apply", "bind",
    "keys", "values", "entries",
}


def _strip_url_and_path_strings(source: str) -> str:
    """Zamienia zawartosc string-literali wygladajacych na URL/sciezke na
    puste, zeby walidator nie skanowal ich wnetrza (KONTRAKT DANYCH,
    adresy GitHub API/raw.githubusercontent to legalna czesc kodu)."""
    def repl(m):
        literal = m.group(0)
        quote = literal[0]
        inner = literal[1:-1]
        if URL_OR_PATH_RE.match(inner):
            return quote + quote
        return literal
    return STRING_LITERAL_RE.sub(repl, source)


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def find_pasted_metric_violations(source: str):
    scanned = _strip_url_and_path_strings(source)
    violations = []
    for m in FLOAT_RE.finditer(scanned):
        violations.append(("float >=4 miejsca po przecinku", m.group(0), _line_of(scanned, m.start())))
    for m in HEX_RE.finditer(scanned):
        violations.append(("dlugi ciag hex (mozliwy wklejony hash)", m.group(0), _line_of(scanned, m.start())))
    for m in KNOWN_COUNT_RE.finditer(scanned):
        violations.append(('znana liczba testow "263" wpisana na sztywno', m.group(0), _line_of(scanned, m.start())))
    return violations


def _extract_function_span(source: str, fn_name: str) -> Optional[Tuple[int, int]]:
    marker = f"function {fn_name}("
    start = source.find(marker)
    if start == -1:
        return None
    brace_start = source.find("{", start)
    if brace_start == -1:
        return None
    depth = 0
    i = brace_start
    while i < len(source):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    return None


def find_classification_reimplementation_violations(source: str):
    """(A) SPRINT_v0.11.0.md: klasyfikacja valid/degenerate/insufficient
    MUSI pochodzic z comp.full_profile (Python), nie z lokalnie liczonych
    progow na ci95_valid/n_effective - poza jednym, jawnie nazwanym
    fallbackiem. Usuwa cialo fallbacku przed skanowaniem, zeby go legalnie
    wykluczyc, potem szuka wzorcow progu/iteracji w RESZCIE pliku."""
    span = _extract_function_span(source, FALLBACK_FN_NAME)
    scanned = source if span is None else source[:span[0]] + source[span[1]:]

    violations = []
    for m in CLASSIFICATION_COMPARISON_RE.finditer(scanned):
        violations.append((
            "reimplementacja progu klasyfikacji poza " + FALLBACK_FN_NAME,
            m.group(0), _line_of(scanned, m.start()),
        ))
    for m in CLASSIFICATION_ITERATION_RE.finditer(scanned):
        violations.append((
            "reimplementacja iteracji klasyfikacyjnej (.every/.some/.filter + ci95_valid) poza " + FALLBACK_FN_NAME,
            m.group(0)[:60], _line_of(scanned, m.start()),
        ))
    return violations


# "c" jest przeciazone w tym pliku: w renderConceptRow/renderCompetency/
# renderGenomes oznacza KONCEPT (competency_profile.json), ale w
# renderOverview's commits.map(function (c) {...}) oznacza commit z GitHub
# API - inny ksztalt calkowicie. Jawnie wykluczone spod sprawdzania klucza
# "c." (NIE jest to blad tego walidatora - to naprawde inny obiekt), zeby
# nie generowac falszywych alarmow o "c.sha"/"c.commit" itp.
NON_CONCEPT_C_MARKERS = ["commits.map(function (c) {"]


def _excluded_spans(source: str, markers: List[str]) -> List[Tuple[int, int]]:
    spans = []
    for marker in markers:
        start = source.find(marker)
        if start == -1:
            continue
        brace_start = source.find("{", start)
        depth, i = 0, brace_start
        while i < len(source):
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
                if depth == 0:
                    spans.append((start, i + 1))
                    break
            i += 1
    return spans


def _extract_chains(source: str, root_name: str, excluded_spans: Optional[List[Tuple[int, int]]] = None) -> List[List[str]]:
    excluded_spans = excluded_spans or []
    chains = []
    for m in CHAIN_RE.finditer(source):
        if m.group(1) != root_name:
            continue
        if any(start <= m.start() < end for start, end in excluded_spans):
            continue
        segments = m.group(2).lstrip(".").split(".")
        trimmed = []
        for seg in segments:
            if seg in JS_BUILTIN_STOP:
                break
            trimmed.append(seg)
        if trimmed:
            chains.append(trimmed)
    return chains


def _resolve_chain(shape: Any, chain: List[str]) -> Optional[str]:
    """Zwraca opis bledu (string) jesli sciezka nie istnieje w `shape`,
    None jesli sciezka rozwiazuje sie poprawnie. Listy/slowniki o
    zmiennych kluczach (np. genomes: {default: ..., highly_plastic: ...})
    sa reprezentowane przez PIERWSZY element/wartosc - to jest
    reprezentatywny KSZTALT, nie doslowna wartosc."""
    node = shape
    walked = []
    for seg in chain:
        walked.append(seg)
        if isinstance(node, dict):
            if seg not in node:
                return "brak klucza '" + ".".join(walked) + "'"
            node = node[seg]
        elif isinstance(node, list):
            if not node:
                return None  # pusta lista - nie da sie dalej zweryfikowac, nie failuj
            node = node[0]
            if isinstance(node, dict):
                if seg not in node:
                    return "brak klucza '" + ".".join(walked) + "' (w elemencie listy)"
                node = node[seg]
            # jesli element listy to skalar, zwyczajnie kontynuuj (rzadkie w tym pliku)
        else:
            return "probuje zejsc w '" + ".".join(walked) + "' ponizej wartosci skalarnej"
    return None


def _representative_shapes(profile: Dict[str, Any]) -> Dict[str, Any]:
    concepts = profile.get("concepts", [])
    # "c" (koncept) MUSI reprezentowac przypadek z jak najwiecej WYPELNIONYCH
    # pol zagniezdzonych (genome_comparison/genomes/secondary_observations
    # niepuste) - inaczej sciezki typu c.genome_comparison.cohens_d falszywie
    # "nie istnieja" tylko dlatego, ze concepts[0] akurat jest
    # insufficient_data (genome_comparison=None tam, a nie w ogole brak pola).
    c_shape = concepts[0] if concepts else {}
    for concept in concepts:
        if concept.get("genome_comparison") and concept.get("genomes") and concept.get("secondary_observations"):
            c_shape = concept
            break

    gd_shape: Dict[str, Any] = {}
    for concept in concepts:
        genomes = concept.get("genomes") or {}
        if genomes:
            gd_shape = next(iter(genomes.values()))
            break

    obs_shape: Dict[str, Any] = {}
    gs_shape: Dict[str, Any] = {}
    for concept in concepts:
        secondary = concept.get("secondary_observations") or []
        if secondary:
            obs_shape = secondary[0]
            genomes = obs_shape.get("genomes") or {}
            if genomes:
                gs_shape = next(iter(genomes.values()))
            break

    return {"comp": profile, "c": c_shape, "gd": gd_shape, "obs": obs_shape, "gs": gs_shape}


def find_unknown_key_violations(source: str, profile: Dict[str, Any]):
    """(B) SPRINT_v0.11.0.md: kazda sciezka comp./c./gd./obs./gs. w kodzie
    panelu MUSI istniec w realnym competency_profile.json."""
    shapes = _representative_shapes(profile)
    excluded_c_spans = _excluded_spans(source, NON_CONCEPT_C_MARKERS)
    violations = []
    seen = set()
    for root in CHAIN_ROOTS:
        spans = excluded_c_spans if root == "c" else []
        for chain in _extract_chains(source, root, spans):
            key = (root, tuple(chain))
            if key in seen:
                continue
            seen.add(key)
            error = _resolve_chain(shapes[root], chain)
            if error:
                path_str = root + "." + ".".join(chain)
                violations.append(("odczyt nieistniejącego pola: " + path_str, error, None))
    return violations


def main() -> int:
    if not PANEL_JS.exists():
        print(f"VALIDATE_PANEL: brak pliku {PANEL_JS}")
        return 1

    source = PANEL_JS.read_text(encoding="utf-8")
    violations = find_pasted_metric_violations(source)
    violations += find_classification_reimplementation_violations(source)

    if not COMPETENCY_PROFILE.exists():
        print(f"VALIDATE_PANEL: brak {COMPETENCY_PROFILE} - pomijam sprawdzanie kluczy (punkt B)")
    else:
        with open(COMPETENCY_PROFILE, encoding="utf-8") as f:
            profile = json.load(f)
        violations += find_unknown_key_violations(source, profile)

    if violations:
        print(f"VALIDATE_PANEL: {len(violations)} problem(ow) w {PANEL_JS}")
        for kind, value, line in violations:
            loc = f"linia {line}: " if line else ""
            print(f"  FAIL: {loc}{kind}: '{value}'")
        return 1

    print(f"VALIDATE_PANEL: OK ({PANEL_JS} - brak wklejonych metryk, brak reimplementacji klasyfikacji, wszystkie klucze istnieją)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
