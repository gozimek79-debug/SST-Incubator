"""BUILD-005 (Execution Package v0.11, Faza 1 Build, Architekt 2026-07-19;
AUD-001 ZAMKNIETE 2026-07-19 - patrz execution_package_v0_11/hashes/baseline_hash.txt).

Hard-Halt: jesli hash != baseline (AUD-001) -> HALT (wyjatek, NIE
warning/continue).

HISTORIA ROZBIEZNOSCI (rozwiazana): audytor podal poczatkowo sam hash
(cca6f8f9...ec935) bez definicji zakresu/algorytmu - 7 prob reprodukcji
(Core-only 4 katalogi, potem 24-plikowa rekonstrukcja wg kategorii "runtime+
World+lekcje+walidatory+prereg") nie dala zgodnosci. Audytor dostarczyl
kanoniczna specyfikacje (AUD_001_CANONICAL.txt): dokladna lista 24 sciezek +
dokladny algorytm agregacji. Nawet z ta lista, PIERWSZA proba (surowe bajty
z dysku) NIE zgadzala sie - przyczyna: `git config core.autocrlf=true` na
tym Windows-owym checkout'cie normalizuje konce linii na CRLF przy checkout,
podczas gdy AUD-001 zostal policzony na tresci znormalizowanej do LF (tak,
jak jest przechowywana w git/na Linuxie). Po normalizacji CRLF->LF PRZED
hashowaniem, hash odtwarza sie DOKLADNIE: cca6f8f933a73c1ff9ca9a3e482b966fef4c430ee50f3ed6c35137d3ab8ec935.

ALGORYTM (dokladnie wg AUD_001_CANONICAL.txt):
    h = sha256()
    for p in sorted(CRITICAL_FILES_AUD_001):
        content = read_bytes(p) z normalizacja CRLF->LF
        h.update(p.encode() + sha256(content).hexdigest().encode())
    baseline = h.hexdigest()

Normalizacja CRLF->LF jest zaimplementowana WPROST w kodzie (nie przez
wywolanie `git show`), zeby przyszly badacz mogl zweryfikowac hash z samego
katalogu roboczego, bez zaleznosci od gita/konkretnego commita - dziala
identycznie niezaleznie od platformy/ustawienia core.autocrlf.
"""

import hashlib
from pathlib import Path
from typing import List, Tuple

# --- Zakres waski (Core-only), zachowany dla wstecznej zgodnosci/referencji ---
CORE_DIRECTORIES = ["clos_brain", "clos_kernel", "genome", "birth"]

# --- AUD-001 KANONICZNE - dokladna lista 24 plikow (audytor, AUD_001_CANONICAL.txt) ---
CRITICAL_FILES_AUD_001 = [
    "clos_academy/echo_runtime.py",
    "clos_academy/lesson_L1_1.py",
    "clos_academy/lesson_L1_2.py",
    "clos_brain/runtime/__init__.py",
    "clos_brain/runtime/action.py",
    "clos_brain/runtime/homeostasis.py",
    "clos_brain/runtime/perception.py",
    "clos_brain/runtime/plasticity.py",
    "clos_brain/runtime/precision.py",
    "clos_brain/runtime/prediction.py",
    "clos_world/scenarios.py",
    "clos_world/world_runtime.py",
    "publications/preregistration_L1_1.json",
    "publications/preregistration_L1_1_ANEKS_2026-07-15_MSE_do_MAE.json",
    "publications/preregistration_L1_1_v0.8.json",
    "publications/preregistration_L1_2.json",
    "publications/preregistration_v0_10_1_population.json",
    "publications/preregistration_v0_11_0_ANEKS_2026-07-19_run_count_i_fdr.json",
    "publications/preregistration_v0_11_0_power_reproduction.json",
    "scripts/validate_artifacts.py",
    "scripts/validate_bundle_freshness.py",
    "scripts/validate_observability.py",
    "scripts/validate_panel.py",
    "scripts/validate_publication.py",
]
assert len(CRITICAL_FILES_AUD_001) == 24, f"oczekiwano 24 plikow, jest {len(CRITICAL_FILES_AUD_001)}"

AUD_001_BASELINE = "cca6f8f933a73c1ff9ca9a3e482b966fef4c430ee50f3ed6c35137d3ab8ec935"


class HardHaltError(Exception):
    """Podniesiony gdy hash nie zgadza sie z baseline - PRZERYWA natychmiast,
    nie loguje jako warning i nie kontynuuje."""


def _normalized_content_hash(path: Path) -> str:
    """sha256(zawartosc) PO normalizacji CRLF->LF - eliminuje zaleznosc od
    platformy/core.autocrlf. Plik przechowywany w git jako LF (konwencja
    tego repo) da IDENTYCZNY hash niezaleznie od tego, czy checkout jest
    Windows (CRLF na dysku) czy Linux (LF na dysku)."""
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def compute_files_hash(repo_root: Path, files: List[str]) -> str:
    """AUD-001 KANONICZNY ALGORYTM: dla kazdego pliku (posortowane sciezki)
    -> sha256(sciezka_bytes + sha256(znormalizowana_zawartosc)_hex_bytes),
    agregowane w jeden sha256. NIE to samo co "sciezka + surowa zawartosc"
    (poprzednia, bledna implementacja) - tu zawartosc jest NAJPIERW haszowana
    OSOBNO, a jej HEX jest tym, co wchodzi do agregatu."""
    h = hashlib.sha256()
    for rel in sorted(files):
        p = repo_root / rel
        content_hash_hex = _normalized_content_hash(p)
        h.update(rel.encode("utf-8") + content_hash_hex.encode("utf-8"))
    return h.hexdigest()


def compute_core_hash(repo_root: Path, core_dirs: List[str] = None) -> str:
    """ZACHOWANE dla referencji/wstecznej zgodnosci - Core-only (4 katalogi),
    STARY algorytm (sciezka+surowa zawartosc, bez normalizacji CRLF). NIE
    jest to AUD-001 - tylko punkt odniesienia z wczesniejszej iteracji."""
    core_dirs = core_dirs or CORE_DIRECTORIES
    files: List[Path] = []
    for d in core_dirs:
        base = repo_root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts:
                files.append(p)

    h = hashlib.sha256()
    for p in sorted(files, key=lambda x: x.relative_to(repo_root).as_posix()):
        rel = p.relative_to(repo_root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(p.read_bytes())
    return h.hexdigest()


def check_critical_files_hash(repo_root: Path, baseline: str,
                               files: List[str] = None) -> Tuple[bool, str]:
    """Zwraca (matches, current_hash) dla zakresu AUD-001 (24 pliki krytyczne,
    domyslnie CRITICAL_FILES_AUD_001, algorytm kanoniczny). NIE podnosi
    wyjatku - to robi enforce_hard_halt()."""
    files = files if files is not None else CRITICAL_FILES_AUD_001
    current = compute_files_hash(repo_root, files)
    return current == baseline, current


def enforce_hard_halt(repo_root: Path, baseline: str = AUD_001_BASELINE,
                       files: List[str] = None) -> str:
    """BUILD-005: jesli hash != baseline -> HardHaltError (HALT), nie warning.
    DOMYSLNIE uzywa AUD-001 (24 pliki krytyczne, algorytm kanoniczny).
    Zwraca current_hash gdy zgodny."""
    matches, current = check_critical_files_hash(repo_root, baseline, files)
    if not matches:
        raise HardHaltError(
            f"HARD-HALT: hash plikow krytycznych ({current}) != baseline ({baseline}). "
            f"Jeden z 24 plikow krytycznych (runtime/World/lekcje/walidatory/prereg) "
            f"zostal zmieniony wzgledem zatwierdzonego baseline'u AUD-001 - "
            f"wykonanie PRZERWANE, nie kontynuowane."
        )
    return current


def check_stable_world_disjoint_seeds(package_root: Path) -> None:
    """AUD-004: cross-lesson contamination = 0 dla stable_world - seedy
    L1.1 i L1.2 musza byc rozlaczne (zero czesci wspolnej)."""
    import json

    l11 = json.loads((package_root / "environments" / "stable_world" / "L1_1_pattern_echo" / "seed_policy.json").read_text(encoding="utf-8"))
    l12 = json.loads((package_root / "environments" / "stable_world" / "L1_2_shock_recovery" / "seed_policy.json").read_text(encoding="utf-8"))

    def _parse_range(expr: str) -> set:
        # "range(1, 94)" -> range object -> set
        inner = expr[expr.index("(") + 1: expr.index(")")]
        lo, hi = (int(x.strip()) for x in inner.split(","))
        return set(range(lo, hi))

    seeds_l11 = _parse_range(l11["seeds"])
    seeds_l12 = _parse_range(l12["seeds"])
    overlap = seeds_l11 & seeds_l12
    if overlap:
        raise HardHaltError(
            f"AUD-004 FAIL: seedy stable_world L1.1/L1.2 NAKLADAJA SIE ({sorted(overlap)[:5]}...) "
            f"- kontaminacja miedzy-lekcyjna wykryta, oczekiwano zbioru pustego."
        )
    if len(seeds_l11) + len(seeds_l12) != 185:
        raise HardHaltError(
            f"AUD-004 FAIL: suma seedow stable_world = {len(seeds_l11) + len(seeds_l12)}, oczekiwano 185."
        )
