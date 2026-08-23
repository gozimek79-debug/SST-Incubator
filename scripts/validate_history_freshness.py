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

TOLERANCJA JEST ROZMIAREM PUSHU, NIE STALYM "gap<=1" (B4C-05 v10, znalezisko
CTO): entries[0]["commit"] wskazuje na commit PRACY, ktory dany wpis opisuje -
a sam wpis moze zostac dopisany WYLACZNIE w NASTEPNYM, ODREBNYM commicie (nie
mozna odwolac sie do wlasnego, jeszcze nieistniejacego hasha - ten sam powod,
dla ktorego PC_001_BASELINE nie moze byc literalem wewnatrz hard_halt.py).
Jeden commit "spoznienia" jest wiec STRUKTURALNIE nieunikniony.

SPRZECZNOSC ZGLOSZONA PRZEZ CTO: sztywne "gap<=1" zaklada CICHO jeden entry
na JEDEN commit - a ten projekt regularnie dzieli jedna prace na kilka
commitow (B4b/B4C-01 rozdzielone, B4C-05 v9 rozdzielone na trzy), bo kronika
ma dokumentowac PRACE, nie commity. Odpowiedz NIE jest przypieta wieksza
liczba (np. "3", bo dzisiejszy split mial 3 commity) - to bylby dokladnie ten
sam blad co progi Z9C (liczba dobrana pod dzisiejszy przypadek zamiast pod
zasade). Odpowiedzia jest ROZMIAR OSTATNIEGO PUSHU, wyliczony, nie zgadywany:

  tolerancja = 1 (commit dopisujacy wpis) + liczba realnych commitow
               WPROWADZONYCH przez OSTATNI PUSH (github.event.before w CI,
               upstream branch @{u} lokalnie)

  ...ALE WYLACZNIE jesli kronika byla juz aktualna (gap<=1) na POCZATKU tego
  pushu - w przeciwnym razie tolerancja spada z powrotem do 1, zeby nie
  ukrywac zaleglosci SPRZED biezacego pushu pod plaszczykiem "to jest jeden
  push". Bez tego warunku ROSNACY dlug moglby sie kumulowac bez konca -
  wystarczyloby nigdy nie pushowac kroniki, a kazdy kolejny push
  "dziedziczylby" cala historie jako "swoj rozmiar".

Push-boundary: w CI ustawiane jako zmienna GITHUB_EVENT_BEFORE (patrz
ci.yml, github.event.before) - GitHub wysyla 40 zer przy pierwszym pushu
nowej galezi, traktowane jak "brak informacji". Lokalnie (poza CI) - branch
upstream (@{u}). Gdy zadne zrodlo niedostepne: bezpieczny fallback do
starej tolerancji (1), nie zgadywanie rozmiaru pushu.

Commity "[skip ci]" wykluczone z liczenia (wlasne auto-commity CI nie licza
sie jako "praca bez wpisu") - identyczny wzorzec co reports/status.json.

Uzycie:
    python scripts/validate_history_freshness.py
Kod wyjscia: 0 = kronika swieza (gap <= tolerancja) lub brak historii do
sprawdzenia, 1 = co najmniej jeden commit "roboczy" bez odpowiadajacego
wpisu w kronice, ponad dopuszczalna tolerancje.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = REPO_ROOT / "reports" / "history.json"
ZERO_SHA = "0" * 40


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


def count_real_commits_since(repo_root: Path, recorded_commit: str, until: str = "HEAD") -> int:
    """Liczy commity NIE-[skip ci] od recorded_commit (wylacznie) do `until`
    (wlacznie, domyslnie HEAD) - identyczny wzorzec co krok "Check
    reports/status.json freshness" w ci.yml. Parametr `until` (B4C-05 v10)
    pozwala zmierzyc dystans do dowolnego punktu w historii (np. do
    poczatku biezacego pushu), nie tylko do HEAD."""
    ancestor_check = subprocess.run(
        ["git", "merge-base", "--is-ancestor", recorded_commit, until],
        cwd=repo_root,
    )
    if ancestor_check.returncode != 0:
        raise ValueError(
            f"commit {recorded_commit} zapisany w reports/history.json nie jest "
            f"przodkiem {until} (przepisana historia?) - nie moge policzyc dystansu"
        )
    result = subprocess.run(
        ["git", "rev-list", "--count", "--invert-grep", "--fixed-strings",
         "--grep=[skip ci]", f"{recorded_commit}..{until}"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    return int(result.stdout.strip())


def push_before_ref(repo_root: Path) -> str:
    """SHA sprzed biezacego pushu, jesli da sie je ustalic - GITHUB_EVENT_BEFORE
    (github.event.before, ustawiane w ci.yml) w CI, upstream branch @{u}
    lokalnie. None gdy niedostepne (pierwszy push nowej galezi - GitHub
    wysyla wtedy 40 zer - albo brak zdalnego trackingu lokalnie)."""
    env_before = os.environ.get("GITHUB_EVENT_BEFORE")
    if env_before and env_before != ZERO_SHA:
        check = subprocess.run(
            ["git", "cat-file", "-e", env_before + "^{commit}"],
            cwd=repo_root, capture_output=True,
        )
        if check.returncode == 0:
            return env_before

    upstream = subprocess.run(
        ["git", "rev-parse", "@{u}"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if upstream.returncode == 0:
        return upstream.stdout.strip()
    return None


def effective_tolerance(repo_root: Path, recorded_commit: str) -> int:
    """1 + rozmiar biezacego pushu (realne commity), o ile kronika byla juz
    aktualna (gap<=1) NA POCZATKU tego pushu - inaczej wraca do sztywnego 1,
    zeby nie ukrywac zaleglosci sprzed biezacego pushu. Patrz uzasadnienie
    w docstringu modulu (B4C-05 v10)."""
    before = push_before_ref(repo_root)
    if before is None:
        return 1
    try:
        gap_before_push = count_real_commits_since(repo_root, recorded_commit, until=before)
    except ValueError:
        return 1
    if gap_before_push > 1:
        return 1
    try:
        push_size = count_real_commits_since(repo_root, before, until="HEAD")
    except ValueError:
        return 1
    return 1 + push_size


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

    tolerance = effective_tolerance(REPO_ROOT, recorded_commit)

    print(
        f"VALIDATE_HISTORY_FRESHNESS: najnowszy wpis kroniki wskazuje commit "
        f"{recorded_commit}; od tego czasu {gap} realny(ch) (nie-[skip ci]) "
        f"commit(ow) do HEAD wlacznie (tolerancja: {tolerance})."
    )
    if gap > tolerance:
        print(
            f"VALIDATE_HISTORY_FRESHNESS: UWAGA: kronika (reports/history.json) jest "
            f"w tyle o {gap} realnych commitow (oczekiwano <= {tolerance} - 1 za commit "
            "spoznienia + rozmiar biezacego pushu, patrz docstring modulu). Commity bez wpisu:"
        )
        for line in offending_commits(REPO_ROOT, recorded_commit):
            print(f"  {line}")
        return 1

    print("VALIDATE_HISTORY_FRESHNESS: OK (kronika swieza)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
