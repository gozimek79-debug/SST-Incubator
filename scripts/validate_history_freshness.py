"""Validate History Freshness (zlecenie uzytkownika, 2026-08-22: automatyzacja kroniki).

PROBLEM: reports/history.json ("Historia laboratorium CLOS" w panelu) jest
jawnie RECZNIE UTRZYMYWANA kronika (patrz jej wlasne pole "note") - swiadoma
decyzja, nie zaniedbanie: proza kazdego wpisu ma byc zrozumiala dla zwyklego
obserwatora, czego nie da sie mechanicznie wyprodukowac z gestych, technicznych
commit message tego repo (np. "CRITICAL_FILES_PC_001", "Hard-Halt", "N_power
vs N_operational" - zargon audytu, nie narracja dla czytelnika z zewnatrz).
Bez ZADNEGO automatycznego sygnalu kronika moze cicho rozjechac sie z
rzeczywistym stanem prac - i tak sie stalo: 26 dni i cztery kamienie milowe
(Pilot Final, B4b, B4C-01/03/04, audyt panelu) bez ani jednego wpisu, nikt
tego nie zauwazyl, bo nic tego nie sygnalizowalo.

ROZWIAZANIE: automatyzacja SYGNALU, nie TRESCI (proza zostaje ludzka - ten
sam wybor co GAP-DOCS/validate_artifact_freshness.py: "ochrona faktow, nie
generowanie prozy"). Ten sam wzorzec co krok "Check reports/status.json
freshness" w .github/workflows/ci.yml: continue-on-error, widoczny czerwony
krok, NIE blokujacy - naprawa (dopisanie wpisu do kroniki) i tak dzieje sie
PRZED pushem, w osobnym commicie, wiec twarde zablokowanie tego joba nie
naprawia niczego, tylko zatrzymuje kod, ktory jest juz gotowy.

TOLERANCJA "gap <= 1", NIE "gap == 0": entries[0]["commit"] wskazuje na
commit PRACY, ktory dany wpis opisuje - a sam wpis moze zostac dopisany
WYLACZNIE w NASTEPNYM, ODREBNYM commicie (nie mozna odwolac sie do wlasnego,
jeszcze nieistniejacego hasha - dokladnie ten sam powod, dla ktorego
PC_001_BASELINE nie moze byc literalem wewnatrz hard_halt.py, patrz
execution_package_v0_11/hashes/pc_001_baseline_hash.txt). Jeden commit
"spoznienia" (ten, ktory dopisuje wpis) jest wiec STRUKTURALNIE nieunikniony
i oczekiwany - identyczna tolerancja jak dla bota "ci-status(ok)...[skip ci]"
przy reports/status.json. Commity "[skip ci]" sa wykluczone z liczenia z
tego samego powodu co tam (wlasne auto-commity CI nie licza sie jako "praca
bez wpisu").

Uzycie:
    python scripts/validate_history_freshness.py
Kod wyjscia: 0 = kronika swieza (gap <= 1) lub brak historii do sprawdzenia,
1 = co najmniej jeden commit "roboczy" bez odpowiadajacego wpisu w kronice.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = REPO_ROOT / "reports" / "history.json"


def load_history(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def newest_recorded_commit(history: dict) -> str:
    entries = history.get("entries", [])
    if not entries:
        raise ValueError("reports/history.json nie ma zadnych wpisow (entries pusta)")
    commit = entries[0].get("commit")
    if not commit:
        raise ValueError("najnowszy wpis w reports/history.json nie ma pola 'commit'")
    return commit


def count_real_commits_since(repo_root: Path, recorded_commit: str) -> int:
    """Liczy commity NIE-[skip ci] od recorded_commit (wylacznie) do HEAD
    (wlacznie) - identyczny wzorzec co krok "Check reports/status.json
    freshness" w ci.yml."""
    ancestor_check = subprocess.run(
        ["git", "merge-base", "--is-ancestor", recorded_commit, "HEAD"],
        cwd=repo_root,
    )
    if ancestor_check.returncode != 0:
        raise ValueError(
            f"commit {recorded_commit} zapisany w reports/history.json nie jest "
            "przodkiem HEAD (przepisana historia?) - nie moge policzyc dystansu"
        )
    result = subprocess.run(
        ["git", "rev-list", "--count", "--invert-grep", "--fixed-strings",
         "--grep=[skip ci]", f"{recorded_commit}..HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    return int(result.stdout.strip())


def offending_commits(repo_root: Path, recorded_commit: str) -> list:
    """Zwraca czytelne linie (hash + temat) commitow policzonych przez
    count_real_commits_since - do komunikatu, nie tylko samej liczby."""
    result = subprocess.run(
        ["git", "log", "--invert-grep", "--fixed-strings", "--grep=[skip ci]",
         "--format=%h %s", f"{recorded_commit}..HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    return [ln for ln in result.stdout.splitlines() if ln.strip()]


def main() -> int:
    if not HISTORY_PATH.exists():
        print("VALIDATE_HISTORY_FRESHNESS: reports/history.json nie istnieje jeszcze, pomijam.")
        return 0

    try:
        history = load_history(HISTORY_PATH)
        recorded_commit = newest_recorded_commit(history)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"VALIDATE_HISTORY_FRESHNESS: {exc}")
        return 1

    try:
        gap = count_real_commits_since(REPO_ROOT, recorded_commit)
    except ValueError as exc:
        print(f"VALIDATE_HISTORY_FRESHNESS: {exc} - pomijam sprawdzenie.")
        return 0

    print(
        f"VALIDATE_HISTORY_FRESHNESS: najnowszy wpis kroniki wskazuje commit "
        f"{recorded_commit}; od tego czasu {gap} realny(ch) (nie-[skip ci]) "
        f"commit(ow) do HEAD wlacznie."
    )
    if gap > 1:
        print(
            f"VALIDATE_HISTORY_FRESHNESS: UWAGA: kronika (reports/history.json) jest "
            f"w tyle o {gap} realnych commitow (oczekiwano <= 1, patrz docstring modulu "
            "o strukturalnym jednym commicie spoznienia). Commity bez wpisu:"
        )
        for line in offending_commits(REPO_ROOT, recorded_commit):
            print(f"  {line}")
        return 1

    print("VALIDATE_HISTORY_FRESHNESS: OK (kronika swieza)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
