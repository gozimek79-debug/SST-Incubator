"""Generator CANONICAL PARAMETERS REPORT - PC-001.

Niezalezna implementacja wzgledem prototypu audytora
(generate_canonical_parameters_report.py, root repo, material referencyjny - nie do
wklejenia). Odpowiada SPECYFIKACJA_KANONICZNA_PC_001.md §0.4: artefakt POCHODNY,
NIEKANONICZNY, nieobjety hashem, wazny WYLACZNIE dla commitu, ktory deklaruje.

ZASADY (wiazace, patrz zadanie audytora §2.3):
  - ZERO wartosci literalnie w kodzie generatora. Kazda liczba w raporcie pochodzi
    z odczytu repozytorium w danym commicie. Niedostepne dane -> MISSING (staly string
    statusu, NIGDY liczbowy fallback/domyslna - to uczyniloby raport drugim zrodlem
    prawdy dla wartosci, ktora go nie ma).
  - Odczyt STATYCZNY (AST), zero importow modulow raportowanych - ten sam wzorzec co
    scripts/validate_canonical_spec.py::resolve_symbol_in_file.
  - Historia (--diff/--history) czytana WYLACZNIE z obiektow gita (`git show <rev>:<sciezka>`),
    NIGDY z wczesniej wygenerowanego raportu - raport nie moze byc zrodlem prawdy o przeszlosci,
    takze dla samego siebie.
  - Hashe artefaktow liczone z TRESCI BLOBU w commicie, nie z pliku na dysku.
  - Brak znacznika czasu generacji w tresci raportu (odstepstwo od prototypu, celowe):
    jedyna tozsamosc raportu to dwa hashe commitow w naglowku ("Commit", "Porownanie z").
    Dzieki temu build(rev, compare_rev) jest CZYSTA FUNKCJA obiektow gita - --verify
    dziala przez regeneracje-i-porownanie (ten sam wzorzec co test 6 walidatora
    specyfikacji), bez potrzeby ignorowania pol "niereprodukowalnych".
  - WYJATEK od powyzszego: CC-01 (czystosc drzewa roboczego) NIE jest funkcja commitu -
    jest funkcja BIEZACEGO stanu roboczego. Retrospektywna regeneracja (np. --verify
    starego raportu) oznacza CC-01 jako "NIE_DOTYCZY", zamiast udawac, ze da sie to
    sprawdzic dla przeszlosci. To jest jawnie nazwane ograniczenie, nie luka.

CC-xx (consistency checks) - trzy wiazace zasady (zadanie audytora §2.3):
  1. Identyfikator opisuje ZNACZENIE kontroli, nie pozycje w tabeli - dodanie kontroli
     nigdy nie przenumerowuje innych (patrz CC_RESERVED, CC_RETIRED ponizej).
  2. Numer raz uzyty NIGDY nie wraca do puli, nawet po wycofaniu kontroli (CC_RETIRED
     pamieta wycofane numery na zawsze, zeby nikt ich przypadkiem nie odzyskal).
  3. Kontrola NIGDY nie znika warunkowo. Jesli warunku nie da sie dzis sprawdzic
     (np. CC-11, patrz nizej), zwraca status "RESERVED" z opisem - nigdy PASS, nigdy
     nie znika z listy.

CZEGO GENERATOR CELOWO NIE ROBI: nie liczy i nie wyswietla wartosci posredniej
PC_001_BASELINE. Baseline jest TBD (decyzja CTO/audytora, zmiana kolejnosci KROK B) -
liczba, ktora WYGLADA jak baseline, zaczelaby byc traktowana jak baseline. CC-11
(zgodnosc hasha z PC_001_BASELINE) jest zarezerwowana i nieaktywna do B5.

PULAPKA CC-10 (udokumentowana w zadaniu audytora, "ten sam blad dwukrotnie" w
prototypie): sprawdzenie "czy PC_001_BASELINE jest literalem w hard_halt.py" NIE MOZE
szukac (a) samej nazwy 'PC_001_BASELINE' jako tekstu - nazwa legalnie wystepuje w
docstringach i komunikatach bledu; (b) dowolnego 64-znakowego literalu hex - HALT
legalnie zawiera AUD_001_BASELINE, inny, juz policzony baseline. Jedyne poprawne
sprawdzenie: czy istnieje PRZYPISANIE (AST Assign/AnnAssign) o nazwie DOKLADNIE
'PC_001_BASELINE'. Patrz pc_001_baseline_literal_present_in_text() i test negatywny
w tests/test_generate_canonical_parameters_report.py.

Uzycie:
    python scripts/generate_canonical_parameters_report.py [--rev REV] [--compare REV] [-o PLIK]
    python scripts/generate_canonical_parameters_report.py --verify RAPORT.md
    python scripts/generate_canonical_parameters_report.py --history SYMBOL [REV ...]
        (bez REV: pelna historia pliku z `git log`, nigdy z wczesniejszego raportu)
"""

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

MISSING = "(niedostepne w tym commicie)"

CONFIG_PATH = "clos_scientist/pc_001_experiment_config.py"
FLOOR_MODEL_PATH = "clos_world/floor_model.py"
HALT_PATH = "execution_package_v0_11/validators/hard_halt.py"
BASELINE_HASH_FILE = "execution_package_v0_11/hashes/pc_001_baseline_hash.txt"

# Adresy parametrow (SPECYFIKACJA_KANONICZNA_PC_001.md §2.9) - to sa ADRESY, nie
# wartosci: nazwa etykiety, sciezka modulu, nazwa symbolu, adres uzasadnienia (proza).
PARAM_ADDRESSES = [
    ("Tolerancja biasu podlogi", CONFIG_PATH, "FLOOR_BIAS_TOLERANCE", "W2-SPEC §2.1a; FLOOR §3"),
    ("Minimalny mianownik", CONFIG_PATH, "MIN_DENOMINATOR", "W2-SPEC §3.1"),
    ("Prog FLOOR_LIMITED w komorce", CONFIG_PATH, "FLOOR_LIMITED_CELL_THRESHOLD", "W2-SPEC §3.3"),
    ("Okno W_early", CONFIG_PATH, "W_EARLY_TICKS", "PC-001 §2.1"),
    ("Okno W_late", CONFIG_PATH, "W_LATE_TICKS", "PC-001 §2.1"),
    ("Mierzalne okno", CONFIG_PATH, "MEASURABLE_WINDOW_TICKS", "CONFIG, komentarz nad symbolem"),
    ("Tolerancja kontroli odtwarzalnosci podlogi", CONFIG_PATH, "FLOOR_ENV_VERIFICATION_TOLERANCE", "FLOOR §6"),
    ("Liczba realizacji na tick (domyslna)", FLOOR_MODEL_PATH, "DEFAULT_N", "FLOOR §6"),
    ("Poczatek zakresu seedow podlogi (domyslny)", FLOOR_MODEL_PATH, "DEFAULT_SEED_START", "FLOOR §6"),
]
# Warunek B: CELOWO brak sciezki/symbolu - znalezisko §6.1 specyfikacji. Generator NIE
# wyszukuje tej wartosci nigdzie indziej (np. w prerejestracji proza) - to uczyniloby
# raport drugim zrodlem prawdy dla wartosci bez zrodla maszynowego.
WARUNEK_B_LABEL = "Prog wielkosci redukcji (Warunek B)"
WARUNEK_B_JUSTIFICATION = 'A1 → „Zmiana 4” · znalezisko §6.1 (brak adresu w kodzie)'

CC_RESERVED = {
    "CC-11": "Zgodnosc hasha z PC_001_BASELINE - aktywuje sie po B5, gdy istnieje wartosc odniesienia.",
}
CC_RETIRED = {}  # numer raz uzyty nigdy nie wraca do puli, nawet po wycofaniu kontroli


# --- warstwa gita: JEDYNE zrodlo historii ---


def _git(args, check=True):
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=check)


def rev_exists(rev):
    return _git(["rev-parse", "--verify", f"{rev}^{{commit}}"], check=False).returncode == 0


def read_bytes_at(rev, rel_path):
    result = _git(["show", f"{rev}:{rel_path}"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def read_text_at(rev, rel_path):
    raw = read_bytes_at(rev, rel_path)
    return raw.decode("utf-8") if raw is not None else None


def blob_sha256_at(rev, rel_path):
    raw = read_bytes_at(rev, rel_path)
    return hashlib.sha256(raw).hexdigest() if raw is not None else None


def list_files_at(rev, dir_path):
    result = _git(["ls-tree", "-r", "--name-only", rev, "--", dir_path], check=False)
    if result.returncode != 0:
        return []
    return sorted(line for line in result.stdout.decode("utf-8").splitlines() if line.strip())


def file_history_revs(rel_path):
    """Rewizje (najstarsza pierwsza) ktore zmienily dany plik - z `git log`, NIGDY z
    wczesniej wygenerowanego raportu. Uzywane przez --history, gdy uzytkownik nie
    poda rewizji jawnie (patrz main()) - pusta lista REV nie moze oznaczac ciszy."""
    result = _git(["log", "--follow", "--format=%H", "--reverse", "--", rel_path], check=False)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.decode("utf-8").splitlines() if line.strip()]


def commit_meta_at(rev):
    result = _git(["show", "-s", "--format=%H|%ai", rev], check=False)
    if result.returncode != 0:
        return MISSING, MISSING
    full_hash, _, date = result.stdout.decode("utf-8").strip().partition("|")
    return full_hash, date


# --- odczyt statyczny (AST), bez importu ---


def _eval_range_call(node):
    """Wasko dopasowuje 'list(range(a, b))' - jedyna forma uzywana w CONFIG dla okien
    pomiarowych. Celowo waskie: nie probuje interpretowac zadnej innej postaci wywolania."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "list"):
        return None
    if len(node.args) != 1:
        return None
    inner = node.args[0]
    if not (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == "range"):
        return None
    try:
        bounds = [ast.literal_eval(a) for a in inner.args]
    except (ValueError, SyntaxError):
        return None
    return list(range(*bounds)) if len(bounds) in (1, 2, 3) else None


def _eval_constant_value(value_node):
    try:
        return ast.literal_eval(value_node)
    except (ValueError, SyntaxError):
        pass
    ranged = _eval_range_call(value_node)
    return ranged if ranged is not None else MISSING


def module_constant_in_text(text, symbol):
    """Statyczny odczyt stalej modulu ze zrodla (bez importu). Zwraca MISSING gdy
    symbol nie istnieje, tekst sie nie parsuje, albo wartosc nie jest literalem/
    rozpoznawalnym wywolaniem list(range(...))."""
    if text is None:
        return MISSING
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return MISSING
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol:
                    return _eval_constant_value(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == symbol:
                return _eval_constant_value(node.value)
    return MISSING


def module_constant_at(rev, rel_path, symbol):
    return module_constant_in_text(read_text_at(rev, rel_path), symbol)


def registry_length_assertion_in_text(text):
    """Odczytuje N z 'assert len(CRITICAL_FILES_PC_001) == N' w zrodle HALT (statycznie)."""
    if text is None:
        return MISSING
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return MISSING
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
            left = node.test.left
            if (
                isinstance(left, ast.Call)
                and isinstance(left.func, ast.Name)
                and left.func.id == "len"
                and left.args
                and isinstance(left.args[0], ast.Name)
                and left.args[0].id == "CRITICAL_FILES_PC_001"
            ):
                for comparator in node.test.comparators:
                    try:
                        return ast.literal_eval(comparator)
                    except (ValueError, SyntaxError):
                        return MISSING
    return MISSING


def pc_001_baseline_literal_present_in_text(text):
    """Czy istnieje PRZYPISANIE 'PC_001_BASELINE = ...' - NIE samo wystapienie nazwy
    jako tekstu (docstringi/komunikaty bledu legalnie ja wspominaja) i NIE dowolny
    64-znakowy hex (AUD_001_BASELINE legalnie ma swoj wlasny). Patrz docstring modulu."""
    if text is None:
        return False
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        if "PC_001_BASELINE" in names:
            return True
    return False


def critical_files_at(rev):
    text = read_text_at(rev, HALT_PATH)
    if text is None:
        return MISSING
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return MISSING
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CRITICAL_FILES_PC_001":
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return MISSING
    return MISSING


def baseline_status_at(rev):
    """Laczy kolejne linie komentarza zaczynajace sie od '# STATUS:' az do pustej linii
    komentarza - jedna linia obcinalaby tekst w polowie zdania (naprawiony blad
    prototypu, patrz docstring modulu przy PARAM_ADDRESSES)."""
    text = read_text_at(rev, BASELINE_HASH_FILE)
    if text is None:
        return MISSING
    collected = []
    collecting = False
    for line in text.splitlines():
        stripped = line.strip()
        if not collecting:
            if stripped.startswith("# STATUS:"):
                collecting = True
                collected.append(stripped[len("# STATUS:") :].strip())
            continue
        if stripped in ("#", ""):
            break
        if stripped.startswith("#"):
            collected.append(stripped.lstrip("#").strip())
        else:
            break
    return " ".join(collected) if collected else MISSING


def power_analysis_exists_at(rev):
    return read_bytes_at(rev, "publications/power_analysis_PC_001.json") is not None


# --- formatowanie ---


def fmt(value):
    if value is MISSING:
        return MISSING
    if isinstance(value, list) and value and all(isinstance(v, int) for v in value):
        return f"[{value[0]} … {value[-1]}] (dlugosc: {len(value)})"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, bool):
        return "tak" if value else "nie"
    return str(value)


def delta(current, previous, has_baseline):
    if not has_baseline:
        return "brak odniesienia"
    if previous is MISSING and current is MISSING:
        return "brak odniesienia"
    if previous == current:
        return "bez zmian"
    return f"ZMIENIONE (bylo: {fmt(previous)})"


# --- migawka stanu jednego commitu (czysta funkcja rev) ---


def snapshot(rev):
    params = {label: module_constant_at(rev, path, symbol) for label, path, symbol, _just in PARAM_ADDRESSES}
    critical_files = critical_files_at(rev)
    pilot_files = list_files_at(rev, "reports/pilot")
    return {
        "rev": rev,
        "params": params,
        "warunek_b": MISSING,
        "frozen_floor": module_constant_at(rev, CONFIG_PATH, "FROZEN_FLOOR_NOISE_WORLD"),
        "experiment_config": module_constant_at(rev, CONFIG_PATH, "EXPERIMENT_CONFIG"),
        "critical_files": critical_files,
        "registry_len_assertion": registry_length_assertion_in_text(read_text_at(rev, HALT_PATH)),
        "baseline_status": baseline_status_at(rev),
        "power_analysis_exists": power_analysis_exists_at(rev),
        "pilot_artifacts": {p: blob_sha256_at(rev, p) for p in pilot_files},
        "baseline_literal_present": pc_001_baseline_literal_present_in_text(read_text_at(rev, HALT_PATH)),
    }


# --- consistency checks (CC-xx) ---


def working_tree_check(is_live_head):
    if not is_live_head:
        return {
            "id": "CC-01",
            "description": "Drzewo robocze czyste",
            "status": "NIE_DOTYCZY",
            "detail": "sprawdzenie ma sens tylko dla biezacego HEAD, nie retrospektywnej regeneracji",
        }
    result = _git(["status", "--porcelain"])
    dirty = result.stdout.decode("utf-8").strip()
    return {
        "id": "CC-01",
        "description": "Drzewo robocze czyste",
        "status": "PASS" if not dirty else "FAIL",
        "detail": "" if not dirty else dirty[:300],
    }


def consistency_checks(snap):
    checks = []

    def add(cc_id, description, ok, detail=""):
        checks.append({"id": cc_id, "description": description, "status": "PASS" if ok else "FAIL", "detail": detail})

    cf = snap["critical_files"]
    add("CC-02", "Rejestr plikow krytycznych odczytany", cf is not MISSING,
        "" if cf is not MISSING else "AST nie znalazl przypisania CRITICAL_FILES_PC_001")

    if cf is MISSING:
        add("CC-03", "Wszystkie pliki krytyczne obecne w commicie", False, "rejestr nieodczytany")
        add("CC-04", "Rejestr bez duplikatow", False, "rejestr nieodczytany")
    else:
        missing_files = [f for f in cf if read_bytes_at(snap["rev"], f) is None]
        add("CC-03", "Wszystkie pliki krytyczne obecne w commicie", not missing_files, ", ".join(missing_files[:10]))
        dups = sorted({f for f in cf if cf.count(f) > 1})
        add("CC-04", "Rejestr bez duplikatow", not dups, ", ".join(dups))

    asserted = snap["registry_len_assertion"]
    if cf is MISSING or asserted is MISSING:
        add("CC-05", "Asercja licznosci rejestru zgodna z lista", False, "nieodczytane")
    else:
        add("CC-05", "Asercja licznosci rejestru zgodna z lista", asserted == len(cf),
            "" if asserted == len(cf) else f"assert mowi {asserted}, lista ma {len(cf)}")

    unread_params = [label for label, val in snap["params"].items() if val is MISSING]
    add("CC-06", "Wszystkie adresowane parametry odczytane", not unread_params, ", ".join(unread_params))

    add("CC-07", "Zamrozona podloga Primary obecna", snap["frozen_floor"] is not MISSING)
    add("CC-08", "Konfiguracja eksperymentu obecna", snap["experiment_config"] is not MISSING)
    add("CC-09", "Status PC_001_BASELINE odczytany", snap["baseline_status"] is not MISSING)

    add(
        "CC-10",
        "Brak literalu hasha PC_001_BASELINE w kodzie Hard Halt",
        not snap["baseline_literal_present"],
        "" if not snap["baseline_literal_present"] else "znaleziono przypisanie PC_001_BASELINE = ... w HALT",
    )

    for cc_id, description in CC_RESERVED.items():
        checks.append({"id": cc_id, "description": description, "status": "RESERVED", "detail": ""})
    for cc_id, description in CC_RETIRED.items():
        checks.append({"id": cc_id, "description": description, "status": "RETIRED", "detail": ""})

    return checks


# --- render markdown ---


def is_live_head_rev(rev):
    head_full, _ = commit_meta_at("HEAD")
    if head_full is MISSING:
        return False
    if rev == "HEAD":
        return True
    rev_full, _ = commit_meta_at(rev)
    return rev_full == head_full


def render_report(rev, compare_rev=None, is_live_head=False):
    full_rev, rev_date = commit_meta_at(rev)
    snap = snapshot(rev)
    has_baseline = compare_rev is not None and rev_exists(compare_rev)
    prev_snap = snapshot(compare_rev) if has_baseline else None

    lines = []
    lines.append("# CANONICAL PARAMETERS REPORT — PC-001")
    lines.append("")
    lines.append("> **ARTEFAKT POCHODNY, NIEKANONICZNY.** Wygenerowany automatycznie z repozytorium.")
    lines.append("> Nie jest zrodlem prawdy dla zadnej wartosci - zrodlem jest adres w kolumnie „Adres”.")
    lines.append("> Nie wchodzi do `CRITICAL_FILES_PC_001`. Nie edytowac recznie.")
    lines.append("> **Wazny wylacznie dla commitu podanego nizej.**")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| Commit | `{full_rev}` |")
    lines.append(f"| Data commitu | {rev_date} |")
    if has_baseline:
        prev_full, prev_date = commit_meta_at(compare_rev)
        lines.append(f"| Porownanie z | `{prev_full}` ({prev_date}) |")
    lines.append("")
    lines.append(
        "> Kolumna „Zmiana” pochodzi z obiektow gita (`git show <rev>:<plik>`), nigdy z "
        "wczesniej wygenerowanego raportu."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Parametry prerejestrowane (§2.9)")
    lines.append("")
    lines.append("| Parametr | Wartosc | Zmiana | Adres uzasadnienia |")
    lines.append("|---|---|---|---|")
    for label, path, symbol, justification in PARAM_ADDRESSES:
        current = snap["params"][label]
        prev = prev_snap["params"][label] if prev_snap else None
        lines.append(f"| {label} | `{fmt(current)}` | {delta(current, prev, has_baseline)} | {justification} |")
    lines.append(f"| **{WARUNEK_B_LABEL}** | *{MISSING}* | — | {WARUNEK_B_JUSTIFICATION} |")
    lines.append("")
    lines.append(
        "> Ostatni wiersz nie jest bledem generatora. Prog Warunku B nie ma adresu maszynowego "
        "(znalezisko §6.1 specyfikacji) - generator nie podstawia go z prozy prerejestracji."
    )
    lines.append("")
    lines.append("## Zamrozona podloga Primary (§2.4)")
    lines.append("")
    lines.append(f"`{fmt(snap['frozen_floor'])}`")
    lines.append("")
    lines.append("## Konfiguracja eksperymentu (§2.1, §2.2)")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(snap["experiment_config"], indent=2, ensure_ascii=False) if snap["experiment_config"] is not MISSING else MISSING)
    lines.append("```")
    lines.append("")
    lines.append("## Rejestr plikow krytycznych (§2.11, §2.12)")
    lines.append("")
    cf = snap["critical_files"]
    if cf is MISSING:
        lines.append(MISSING)
    else:
        lines.append(f"Pozycji: **{len(cf)}**")
    lines.append("")
    lines.append("## Stan bramek i artefaktow (§5)")
    lines.append("")
    lines.append(f"**`PC_001_BASELINE`:** `{snap['baseline_status']}`")
    lines.append("")
    lines.append(f"**Artefakt analizy mocy** (`publications/power_analysis_PC_001.json`): "
                  f"{'istnieje' if snap['power_analysis_exists'] else 'nie istnieje'}")
    lines.append("")
    if snap["pilot_artifacts"]:
        lines.append("| Artefakt | sha256 (blob) |")
        lines.append("|---|---|")
        for path, sha in sorted(snap["pilot_artifacts"].items()):
            lines.append(f"| `{path}` | `{sha}` |")
        lines.append("")
    lines.append("## Consistency Check")
    lines.append("")
    lines.append("| ID | Sprawdzenie | Status | Szczegoly |")
    lines.append("|---|---|---|---|")
    checks = [working_tree_check(is_live_head)] + consistency_checks(snap)
    for c in checks:
        lines.append(f"| `{c['id']}` | {c['description']} | {c['status']} | {c['detail']} |")
    lines.append("")
    lines.append(
        "> Identyfikatory sa stabilne: opisuja ZNACZENIE kontroli, nie pozycje w tabeli. "
        "Numer raz uzyty nie zostanie przypisany innej kontroli. Kontrola nigdy nie znika "
        "warunkowo - nieaktywna kontrola ma status RESERVED z opisem, nie brak wiersza."
    )
    lines.append("")

    return "\n".join(lines) + "\n"


# --- --verify ---


COMMIT_LINE_RE = re.compile(r"^\|\s*Commit\s*\|\s*`([0-9a-f]{7,40})`\s*\|\s*$", re.MULTILINE)
COMPARE_LINE_RE = re.compile(r"^\|\s*Porownanie z\s*\|\s*`([0-9a-f]{7,40})`", re.MULTILINE)


def verify_report(report_path):
    text = Path(report_path).read_text(encoding="utf-8")
    commit_m = COMMIT_LINE_RE.search(text)
    if not commit_m:
        return {"ok": False, "reason": "nie znaleziono zadeklarowanego commitu w raporcie", "report": str(report_path)}
    declared_rev = commit_m.group(1)
    if not rev_exists(declared_rev):
        return {"ok": False, "reason": f"commit {declared_rev} nie istnieje w tym repo", "report": str(report_path)}
    compare_m = COMPARE_LINE_RE.search(text)
    compare_rev = compare_m.group(1) if compare_m else None
    regenerated = render_report(declared_rev, compare_rev=compare_rev, is_live_head=is_live_head_rev(declared_rev))
    ok = regenerated == text
    result = {"ok": ok, "report": str(report_path), "declared_commit": declared_rev, "declared_compare": compare_rev}
    if not ok:
        result["reason"] = "regenerowany raport rozjezdza sie z podanym plikiem"
    return result


# --- CLI ---


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", default="HEAD")
    parser.add_argument("--compare")
    parser.add_argument("-o", "--output")
    parser.add_argument("--verify")
    parser.add_argument("--history", nargs="+", metavar=("SYMBOL", "REV"))
    args = parser.parse_args(argv)

    if args.verify:
        result = verify_report(args.verify)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ok"] else 1

    if args.history:
        symbol = args.history[0]
        explicit_revs = args.history[1:]
        entry = next((p for p in PARAM_ADDRESSES if p[0] == symbol or p[2] == symbol), None)
        if entry is None:
            print(f"nieznany parametr: {symbol}")
            return 2
        label, path, sym, _just = entry
        # Brak REV nie moze oznaczac ciszy (audyt 661b92a, punkt 1): bez jawnych
        # rewizji przechodzimy CALA historie pliku z `git log`, nie z raportu.
        revs = explicit_revs if explicit_revs else file_history_revs(path)
        if not revs:
            print(f"brak historii dla '{symbol}' ({path}) - `git log` nie znalazl zadnej rewizji")
            return 1
        for rev in revs:
            value = module_constant_at(rev, path, sym)
            print(f"{rev}: {fmt(value)}")
        return 0

    report = render_report(args.rev, compare_rev=args.compare, is_live_head=is_live_head_rev(args.rev))
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"zapisano: {args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
