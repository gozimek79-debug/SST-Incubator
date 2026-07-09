"""Validate Panel - skanuje clos_studio/panel/panel.js pod katem wklejonych
metryk (SPRINT_v0.8.5.md, Priorytet 3).

Panel Badacza ma czytac dane, nie zawierac ich. Ten skrypt FAILUJE (exit 1),
jesli w KODZIE panelu (poza string-literalami ktore wygladaja na URL/sciezke
repo) znajdzie:
  - float z >=4 miejscami po przecinku (np. 0.156712) - wyglada jak wklejona
    metryka (MSE, CI95, effect size...), ktora powinna pochodzic z fetch().
  - dlugi ciag hex (>=16 znakow) - wyglada jak wklejony hash
    (git_commit / config_hash / manifest_hash). CSS-owe kolory (#4FC8E0,
    6-8 znakow) sa ponizej progu i nie sa flagowane.
  - dokladnie "263" jako osobna liczba - znana liczba testow z poprzedniego
    sprintu; jesli kiedykolwiek trafi do kodu panelu na sztywno, to dowod
    driftu kod<->dane, ktoremu ten sprint ma zapobiegac.

Nazwy pol/identyfikatory (np. "config_hash", "n_effective") nie sa liczbami
ani ciagami hex, wiec i tak nie pasuja do powyzszych wzorcow - nie wymagaja
osobnego wykluczania.

Uzycie:
    python scripts/validate_panel.py
Kod wyjscia: 0 = czysto, 1 = znaleziono podejrzana wklejona metryke.
"""

import re
import sys
from pathlib import Path

PANEL_JS = Path("clos_studio/panel/panel.js")

STRING_LITERAL_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
URL_OR_PATH_RE = re.compile(r'^https?://|^[\w.\-]+/[\w./\-]+$')

FLOAT_RE = re.compile(r'\b\d+\.\d{4,}\b')
HEX_RE = re.compile(r'\b[0-9a-fA-F]{16,}\b')
KNOWN_COUNT_RE = re.compile(r'(?<!\d)263(?!\d)')


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


def find_violations(source: str):
    scanned = _strip_url_and_path_strings(source)
    violations = []
    for m in FLOAT_RE.finditer(scanned):
        violations.append(("float >=4 miejsca po przecinku", m.group(0), _line_of(scanned, m.start())))
    for m in HEX_RE.finditer(scanned):
        violations.append(("dlugi ciag hex (mozliwy wklejony hash)", m.group(0), _line_of(scanned, m.start())))
    for m in KNOWN_COUNT_RE.finditer(scanned):
        violations.append(('znana liczba testow "263" wpisana na sztywno', m.group(0), _line_of(scanned, m.start())))
    return violations


def main() -> int:
    if not PANEL_JS.exists():
        print(f"VALIDATE_PANEL: brak pliku {PANEL_JS}")
        return 1

    source = PANEL_JS.read_text(encoding="utf-8")
    violations = find_violations(source)

    if violations:
        print(f"VALIDATE_PANEL: {len(violations)} podejrzanych wklejonych metryk w {PANEL_JS}")
        for kind, value, line in violations:
            print(f"  FAIL: linia {line}: {kind}: '{value}'")
        return 1

    print(f"VALIDATE_PANEL: OK ({PANEL_JS} - brak wklejonych metryk)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
