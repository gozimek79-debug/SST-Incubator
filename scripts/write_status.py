"""Write Status - generuje reports/status.json w CI, ZAWSZE (patrz CI-01C/CI-01D
nizej - nie tylko po zielonym pytest + walidatorach, jak w pierwotnej wersji).

Zrodlo prawdy dla Panelu Badacza (SPRINT_v0.8.5.md, Priorytet 3, opcja a):
liczba testow i status CI nie sa wpisywane recznie do panel.js - panel czyta
ten plik. Pierwotnie (do CI-01C) skrypt uruchamial sie w .github/workflows/ci.yml
WYLACZNIE PO tym, jak pytest i wszystkie trzy walidatory juz przeszly, wiec sama
obecnosc w tym miejscu byla dowodem sukcesu - to zalozenie JUZ NIE OBOWIAZUJE,
patrz notatki CI-01C i CI-01D nizej.

SPRINT_v0.11.0.md Zadanie 3 (decyzja CTO 2026-07-18): plik VERSION w roocie
repo jest JEDYNYM zrodlem numeru sprintu - ten skrypt go czyta i wpisuje do
status.json jako pole "sprint". Panel czyta WYLACZNIE status.json (ZERO
literalow wersji w panel.js, egzekwowane przez scripts/validate_panel.py) -
zeby zmienic wersje widoczna w panelu, edytuje sie TYLKO plik VERSION.

NAPRAWA CI-01 (zgloszenie uzytkownika 2026-08-10): "N passed / green" wygladalo
identycznie niezaleznie od tego, ile testow zostalo cicho pominietych.
tests.skipped/failed/errors dodane obok passed.

NAPRAWA CI-01B (zgloszenie audytora 2026-08-11, pomiar w srodowisku bez scipy):
importorskip stoi NA POZIOMIE MODULU - brak scipy daje "1 skipped" (caly
modul jako jedna pozycja kolekcji), NIE "60 skipped". Sam zapis liczby
pominietych nie wystarcza - "1" jest tak samo latwe do przeoczenia jak jego
brak. Dwie zmiany w odpowiedzi:
  1. tests.collected - z OSOBNEGO przebiegu `pytest --collect-only -q`
     (patrz collect_log_path ponizej) - niezalezna od pytest -q liczba
     "ile testow pytest w ogole zobaczyl", do porownania z passed+skipped+
     failed+errors. Rozjazd = czesc testow zniknela w sposob, ktorego
     rozbicie na kategorie nie tlumaczy.
  2. tests.status jest WYLICZANY (patrz compute_tests_status), nie
     literalem "green": red gdy failed>0 lub errors>0; unknown gdy
     collected nie do odczytania LUB nie zgadza sie z suma kategorii
     (BRAK ODCZYTU != ZERO - nieodczytana liczba nie ma wygladac jak
     zero pominiec); warning gdy skipped>0; green tylko gdy wszystko
     policzone i zgadza sie, i skipped==0.

NAPRAWA CI-01C (zgloszenie audytora 2026-08-11): w ci.yml ten krok teraz ma
`if: always()` - odpala sie TAKZE gdy "Run tests" lub ktorykolwiek walidator
padnie (wczesniej: pomijany, wiec galaz tests.status=="red" byla w CI
NIEOSIAGALNA - job po prostu przerywal sie wczesniej i status.json zostawal
stary). Konsekwencja: SAMA OBECNOSC w tym miejscu przestaje byc dowodem, ze
walidatory przeszly (byla nim tylko dawniej, gdy brakowalo always()). Stad
JOB_STATUS (z ${{ job.status }} w ci.yml, patrz main()): gdy != "success",
validators.* i ci.conclusion NIE moga juz zakladac powodzenia - patrz
build_validators_status()/main().

NAPRAWA CI-01D (zgloszenie audytora 2026-08-12): if: always() z CI-01C
otwiera droge do "red" TYLKO jesli skrypt faktycznie zdazy zapisac plik.
Byl tu wczesny "return 1" (PRZED zapisem), gdy w logu brakowalo wzorca
"N passed" - a brakuje go WLASNIE przy bledzie kolekcji (zly import w jednym
pliku testowym, bez importorskip: log to "1 error in 2.3s", zero testow
faktycznie ruszylo, zero wzmianki o "passed"). Skutek: w tym scenariuszu
skrypt konczyl sie PRZED zapisaniem czegokolwiek - status.json zostawal
stary mimo if: always(). Usuniety - skrypt ZAWSZE zapisuje plik (zwraca 0),
brak odczytu "passed" (jak i pliku loga w ogole) daje passed=None, ten sam
wzorzec "brak odczytu != zero" co dla collected.

Uzycie (w CI, po `python -m pytest -q | tee pytest_output.txt` oraz
`python -m pytest --collect-only -q | tee pytest_collect_output.txt`):
    python scripts/write_status.py pytest_output.txt reports/status.json pytest_collect_output.txt
Zmienna srodowiskowa JOB_STATUS (opcjonalna, ustawiana w ci.yml z ${{ job.status }}):
gdy brak/"success" - validators/ci.conclusion jak dawniej (OK/success);
w przeciwnym razie - validators "UNKNOWN", ci.conclusion = wartosc JOB_STATUS.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PASSED_RE = re.compile(r"(\d+) passed")
SKIPPED_RE = re.compile(r"(\d+) skipped")
FAILED_RE = re.compile(r"(\d+) failed")
ERRORS_RE = re.compile(r"(\d+) error")
# Format `pytest --collect-only -q`: linia koncowa "N tests collected" albo,
# gdy cos jest odfiltrowane (np. -k/--deselect), "N/M tests collected (M
# deselected)" - w obu przypadkach interesuje nas PIERWSZA liczba (faktycznie
# zebrane pozycje, nie "M" z nawiasu).
COLLECTED_RE = re.compile(r"(\d+)(?:/\d+)? tests? collected")
VERSION_FILE = Path("VERSION")


def read_sprint_version() -> str:
    if not VERSION_FILE.exists():
        return ""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def parse_passed(pytest_output: str):
    m = PASSED_RE.search(pytest_output)
    return int(m.group(1)) if m else None


def parse_count(pattern: re.Pattern, pytest_output: str) -> int:
    """0, gdy wzorzec nie wystapil - zgodnie z formatem pytest, ktory
    POMIJA kategorie o liczbie zero w linii podsumowania (nigdy nie pisze
    "0 skipped"). To NIE jest "domyslanie sie zera" w sensie ryzykownym:
    pytest gwarantuje, ze kazda niezerowa kategoria w tej linii sie pojawi.
    Wlasciwym sygnalem "czegos nie odczytano" jest rozjazd wzgledem
    niezaleznie zmierzonego tests.collected - patrz compute_tests_status."""
    m = pattern.search(pytest_output)
    return int(m.group(1)) if m else 0


def parse_collected(collect_output: str):
    m = COLLECTED_RE.search(collect_output)
    return int(m.group(1)) if m else None


def compute_tests_status(passed, skipped: int, failed: int, errors: int, collected):
    """Wyliczony, nie literal (zgloszenie audytora CI-01B). Kolejnosc
    sprawdzen ma znaczenie: failed/errors > 0 to zawsze "red", niezaleznie
    od tego, czy passed/collected sie zgadzaja - blad kolekcji (np. zly
    import w jednym pliku testowym, BEZ importorskip) daje log bez slowa
    "passed" w ogole ("1 error in 2.3s"), ale "errors" nadal sie parsuje -
    to i tak "red", nie "unknown" (znany, konkretny problem, patrz CI-01D).

    passed=None (NAPRAWA CI-01D, zgloszenie audytora): brak odczytu tak samo
    jak dla collected - "unknown", NIGDY cichy fallback do "green"."""
    if failed > 0 or errors > 0:
        return "red"
    if passed is None or collected is None:
        return "unknown"
    accounted = passed + skipped + failed + errors
    if accounted != collected:
        return "unknown"
    if skipped > 0:
        return "warning"
    return "green"


KNOWN_VALIDATORS = ["validate_publication", "validate_artifacts", "validate_panel"]


def build_validators_and_ci(job_status):
    """job_status: wartosc ${{ job.status }} przekazana przez ci.yml (patrz
    komentarz modulu), albo None przy lokalnym/recznym uruchomieniu.

    job_status None lub "success": walidatory faktycznie musialy przejsc, zeby
    dojsc do tego kroku (kazdy z siedmiu jest krokiem BEZ continue-on-error) -
    "OK"/"success" sa tu nadal strukturalnie gwarantowane, nie zgadywane.

    job_status inny (np. "failure", "cancelled"): ten krok ma teraz if: always(),
    wiec dojscie do niego JUZ NIE dowodzi, ze walidatory przeszly - mogly nie
    zdazyc sie uruchomic (job przerwal sie na "Run tests") albo jeden z nich
    faktycznie padl. Nie da sie std stad odroznic ktory z dwoch przypadkow -
    w obu "OK" bylby fabrykacja, wiec "UNKNOWN" dla wszystkich trzech."""
    if job_status is None or job_status == "success":
        return {name: "OK" for name in KNOWN_VALIDATORS}, "success"
    return {name: "UNKNOWN" for name in KNOWN_VALIDATORS}, job_status


def git_commit_sha() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return ""


def main() -> int:
    pytest_log_path = sys.argv[1] if len(sys.argv) > 1 else "pytest_output.txt"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "reports/status.json"
    collect_log_path = sys.argv[3] if len(sys.argv) > 3 else None

    # NAPRAWA CI-01D (zgloszenie audytora 2026-08-12): byl tu wczesny "return 1"
    # PRZED zapisem status.json, gdy wzorca "N passed" brakowalo w logu - a brakuje
    # go WLASNIE przy bledzie kolekcji (np. zly import w jednym pliku testowym,
    # BEZ importorskip: "1 error in 2.3s", zero wzmianki o "passed"). Skutek: w
    # dokladnie tym scenariuszu, w ktorym najbardziej zalezy na zapisaniu "red",
    # skrypt konczyl sie PRZED zapisaniem czegokolwiek - status.json zostawal
    # stary/zielony mimo if: always() w ci.yml (sierpniowa awaria, BRIEF 5.2).
    # Skrypt ma teraz ZAWSZE zapisac status.json: brak pliku loga lub brak
    # wzorca "passed" -> passed=None -> compute_tests_status() daje "unknown"
    # (chyba ze failed/errors>0 juz sklasyfikowaly to jako "red") - ten sam
    # wzorzec "brak odczytu != zero", co juz stosowany dla collected.
    try:
        with open(pytest_log_path, encoding="utf-8") as f:
            pytest_output = f.read()
    except FileNotFoundError:
        print(f"write_status: UWAGA - nie znaleziono {pytest_log_path}; tests.passed bedzie null.", file=sys.stderr)
        pytest_output = ""

    passed = parse_passed(pytest_output)
    if passed is None:
        print(
            f"write_status: UWAGA - nie znaleziono wzorca 'N passed' w {pytest_log_path} "
            "(typowe przy bledzie kolekcji - zero testow faktycznie ruszylo); "
            "tests.passed bedzie null, tests.status niezielony.",
            file=sys.stderr,
        )
    skipped = parse_count(SKIPPED_RE, pytest_output)
    failed = parse_count(FAILED_RE, pytest_output)
    errors = parse_count(ERRORS_RE, pytest_output)

    collected = None
    if collect_log_path:
        try:
            with open(collect_log_path, encoding="utf-8") as f:
                collected = parse_collected(f.read())
        except FileNotFoundError:
            collected = None
        if collected is None:
            print(
                f"write_status: UWAGA - nie znaleziono wzorca 'N tests collected' w "
                f"{collect_log_path}; tests.collected bedzie null, tests.status 'unknown' "
                "(brak odczytu != zero pominiec).",
                file=sys.stderr,
            )
    else:
        print(
            "write_status: UWAGA - collect_log_path nie podany; tests.collected bedzie "
            "null, tests.status 'unknown'.",
            file=sys.stderr,
        )

    tests_status = compute_tests_status(passed, skipped, failed, errors, collected)
    job_status = os.environ.get("JOB_STATUS") or None
    validators, ci_conclusion = build_validators_and_ci(job_status)

    status = {
        "sprint": read_sprint_version(),
        "tests": {
            "passed": passed,
            "skipped": skipped,
            "failed": failed,
            "errors": errors,
            "collected": collected,
            "status": tests_status,
        },
        "validators": validators,
        "ci": {"conclusion": ci_conclusion, "workflow": "ci.yml"},
        "commit": git_commit_sha(),
        "branch": os.environ.get("GITHUB_REF_NAME", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

    extra = []
    if skipped:
        extra.append(f"{skipped} skipped")
    if failed:
        extra.append(f"{failed} failed")
    if errors:
        extra.append(f"{errors} errors")
    extra_note = ", " + ", ".join(extra) if extra else ""
    passed_note = str(passed) if passed is not None else "?"
    collected_note = f", collected={collected}" if collected is not None else ", collected=?"
    print(f"write_status: zapisano {out_path} ({passed_note} passed{extra_note}{collected_note}, status={tests_status})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
