"""Validate BH Family (B4C-05 v4, CTO pkt 4) - walidator zgodnosci dla
publications/pc_001_bh_family.json.

CEL: rodzina BH-FDR PC-001 (11 komorek, m zamrozone) jest DEKLARATYWNYM
plikiem, ktory bedzie chronil evaluator (B4C-2) i docelowo baseline (B5) -
musi wiec byc mechanicznie sprawdzalny, nie tylko przeczytany. Cztery
kontrole (dokladnie te zadane przez CTO):

  a) kazdy adres w pc_001_bh_family.json musi sie ROZWIAZYWAC - reuzywa
     TEJ SAMEJ gramatyki adresow i tych samych funkcji rozwiazujacych co
     scripts/validate_canonical_spec.py (SECTION_ADDR_RE/FRAGMENT_ADDR_RE/
     SYMBOL_ADDR_RE + resolve_*_in_file) - zero duplikacji logiki adresowej.
  b) kazda komorka aktywna musi wystepowac w Specyfikacji Kanonicznej §2.6
     (zrodlo: SPECYFIKACJA_KANONICZNA_PC_001.json, strukturalnie, nie regex
     na markdownie).
  c) liczba komorek aktywnych musi rownac sie polu 'm' uzytemu do progu BH
     (m ZAMROZONE, B4C-05 v4 pkt 2).
  d) zadna komorka o statusie WYKLUCZONYM (cells_excluded w TYM SAMYM pliku -
     nie osobna, potencjalnie dryfujaca lista) nie moze wystepowac wsrod
     aktywnych.

Dodatkowo (nie w oryginalnym zleceniu, ale bezposrednia konsekwencja
"srodowisko odczytane z CONFIG, nie literalem", B4C-05 v4 ZAKRES pkt 1):
kazda komorka deklarujaca srodowisko "Primary" musi zgadzac sie z
CONFIG::EXPERIMENT_CONFIG['environments']['primary'] - nie tylko istniec
jako symbol, ale miec ZGODNA WARTOSC (ten sam wzorzec co
tests/test_n_operational_seeds_provenance.py).

Uzycie:
    python scripts/validate_bh_family.py
Kod wyjscia: 0 = wszystkie kontrole PASS, 1 = co najmniej jedna FAIL.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_canonical_spec import (  # noqa: E402
    SECTION_ADDR_RE,
    FRAGMENT_ADDR_RE,
    SYMBOL_ADDR_RE,
    resolve_section_in_file,
    resolve_fragment_in_file,
    resolve_symbol_in_file,
    _file_for_token,
)
from clos_scientist.pc_001_experiment_config import EXPERIMENT_CONFIG  # noqa: E402

FAMILY_PATH = REPO_ROOT / "publications" / "pc_001_bh_family.json"
SPEC_JSON_PATH = REPO_ROOT / "SPECYFIKACJA_KANONICZNA_PC_001.json"

BASE_CONDITION_SUFFIX_RE = re.compile(r"-(A|B|separacja)$")
K3A_RE = re.compile(r"^(K3a)-warunek(\d+)$")


def load_family(path=FAMILY_PATH):
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_strings(obj):
    """Rekurencyjnie wszystkie wartosci-stringi w dowolnie zagniezdzonej
    strukturze JSON (dict/list) - adres moze wystapic w kazdym polu tekstowym,
    nie tylko w z gory ustalonych kluczach."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_strings(v)


def check_addresses_resolve(family: dict) -> list:
    """(a) Kazdy adres (§, ->"fragment", ::symbol) znaleziony w dowolnym
    polu tekstowym musi sie rozwiazywac - ta sama gramatyka/funkcje co
    validate_canonical_spec.py."""
    problems = []
    seen = set()
    for text in _iter_strings(family):
        for m in SECTION_ADDR_RE.finditer(text):
            token, num = m.group(1), m.group(2)
            key = ("section", token, num)
            if key in seen:
                continue
            seen.add(key)
            path = _file_for_token(token)
            if not resolve_section_in_file(path, num):
                problems.append(f"{token} §{num} nie rozwiazuje sie w {path.name}")
        for m in FRAGMENT_ADDR_RE.finditer(text):
            token, fragment = m.group(1), m.group(2)
            key = ("fragment", token, fragment)
            if key in seen:
                continue
            seen.add(key)
            path = _file_for_token(token)
            if not resolve_fragment_in_file(path, fragment):
                problems.append(f'{token} -> "{fragment}" nie rozwiazuje sie w {path.name}')
        for m in SYMBOL_ADDR_RE.finditer(text):
            token, symbol = m.group(1), m.group(2)
            key = ("symbol", token, symbol)
            if key in seen:
                continue
            seen.add(key)
            path = _file_for_token(token)
            if not resolve_symbol_in_file(path, symbol):
                problems.append(f"{token}::{symbol} nie rozwiazuje sie w {path.name}")
    if not seen:
        problems.append(
            "ZERO adresow (§/→/::) znalezionych w calym artefakcie - notacja jest "
            "albo zniszczona, albo plik jest pusty (B4C-05 v5, ta sama luka co w "
            "validate_canonical_spec.py)"
        )
    return problems


def count_addresses(family: dict) -> int:
    """Do resolved_count w main() - liczy TE SAME dopasowania co
    check_addresses_resolve, bez duplikowania logiki resolve/problem."""
    seen = set()
    for text in _iter_strings(family):
        for m in SECTION_ADDR_RE.finditer(text):
            seen.add(("section", m.group(1), m.group(2)))
        for m in FRAGMENT_ADDR_RE.finditer(text):
            seen.add(("fragment", m.group(1), m.group(2)))
        for m in SYMBOL_ADDR_RE.finditer(text):
            seen.add(("symbol", m.group(1), m.group(2)))
    return len(seen)


def cell_base_condition(cell_id: str) -> str:
    """'K1-A' -> 'K1', 'K4-separacja' -> 'K4', 'K3a-warunek1' -> 'K3a warunek 1'."""
    m = K3A_RE.match(cell_id)
    if m:
        return f"{m.group(1)} warunek {m.group(2)}"
    return BASE_CONDITION_SUFFIX_RE.sub("", cell_id)


def load_spec_2_6_labels(spec_json_path=SPEC_JSON_PATH) -> set:
    """Etykiety warunkow z §2.6 (kolumna 'Warunek'), strukturalnie z JSON-a
    Specyfikacji - nie regex na markdownie. Usuwa '**' i bierze tekst PRZED
    em-dash (—), zgodnie z konwencja tabeli."""
    data = json.loads(spec_json_path.read_text(encoding="utf-8"))
    labels = set()
    for section in data["sections"]:
        if section["id"] != "2.6":
            continue
        for block in section["blocks"]:
            if block["type"] != "table":
                continue
            for row in block["rows"]:
                raw = row.get("Warunek")
                if not raw:
                    continue
                cleaned = raw.replace("**", "")
                label = cleaned.split("—")[0].strip()
                labels.add(label)
    return labels


def check_cells_in_spec_2_6(family: dict, spec_2_6_labels: set) -> list:
    """(b) Kazda komorka aktywna musi miec odpowiadajacy warunek w §2.6.

    B4C-05 v5: podatna na ta sama luke co check_addresses_resolve - pusta
    cells_active dawalaby [] (wszystkie zero komorek 'przechodza', bo petla
    sie nie wykonuje). Guard ponizej odrozina 'sprawdzilem 11 komorek, wszystkie
    OK' od 'nie mialem czego sprawdzic'."""
    problems = []
    active = family.get("cells_active", [])
    for cell in active:
        base = cell_base_condition(cell["id"])
        if base not in spec_2_6_labels:
            problems.append(f"komorka {cell['id']} (baza '{base}') nie wystepuje w Specyfikacji §2.6")
    if not active:
        problems.append("ZERO komorek aktywnych do sprawdzenia - cells_active jest puste (B4C-05 v5)")
    return problems


def check_count_matches_m(family: dict) -> list:
    """(c) len(cells_active) == family['m'], i obie liczby > 0."""
    m = family.get("m")
    n_active = len(family.get("cells_active", []))
    if m is None:
        return ["brak pola 'm' w artefakcie"]
    if m == 0 or n_active == 0:
        return [f"m={m}, komorek aktywnych={n_active} - rodzina pusta/zerowa nie jest poprawnym stanem (B4C-05 v5)"]
    if n_active != m:
        return [f"liczba komorek aktywnych ({n_active}) != m ({m})"]
    return []


def check_no_excluded_among_active(family: dict) -> list:
    """(d) Zadna komorka wykluczona (z cells_excluded W TYM SAMYM pliku)
    nie moze wystapic wsrod aktywnych."""
    excluded_ids = {c["id"] for c in family.get("cells_excluded", [])}
    active_ids = {c["id"] for c in family.get("cells_active", [])}
    if not active_ids:
        return ["ZERO komorek aktywnych - brak overlapu jest wiec bezprzedmiotowy, nie dowod poprawnosci (B4C-05 v5)"]
    overlap = excluded_ids & active_ids
    if overlap:
        return [f"komorki wykluczone wystepujace wsrod aktywnych: {sorted(overlap)}"]
    return []


VALID_KIERUNEK_WSPARCIA = {"ODRZUCENIE_H0", "BRAK_ODRZUCENIA_H0"}


def check_kierunek_wsparcia(family: dict) -> list:
    """(f) B4C-2 (07), decyzja CTO: kazda komorka aktywna MUSI miec pole
    'kierunek_wsparcia' (wartosc w VALID_KIERUNEK_WSPARCIA) i niepuste
    'kierunek_wsparcia_zrodlo' - brak pola/pusty zrodlo/wartosc spoza zbioru
    to FAIL, nie wartosc domyslna (ten sam blad klasy, ktorego evaluator ma
    unikac - zero domyslnych wartosci dla kierunku, patrz clos_scientist/
    pc_001_evaluator.py). Liczby zadeklarowane na poziomie glownym artefaktu
    (kierunek_ODRZUCENIE_H0/kierunek_BRAK_ODRZUCENIA_H0) musza zgadzac sie z
    faktycznym rozkladem pol per komorka - rozjazd oznacza, ze artefakt sam
    sobie zaprzecza."""
    problems = []
    active = family.get("cells_active", [])
    if not active:
        return ["ZERO komorek aktywnych - brak przedmiotu kontroli (ten sam wzorzec co b/d/e)"]

    counts = {"ODRZUCENIE_H0": 0, "BRAK_ODRZUCENIA_H0": 0}
    for cell in active:
        cell_id = cell.get("id", "<brak id>")
        kierunek = cell.get("kierunek_wsparcia")
        if kierunek is None:
            problems.append(f"komorka {cell_id}: brak pola 'kierunek_wsparcia'")
            continue
        if kierunek not in VALID_KIERUNEK_WSPARCIA:
            problems.append(
                f"komorka {cell_id}: 'kierunek_wsparcia'={kierunek!r} spoza "
                f"dozwolonego zbioru {sorted(VALID_KIERUNEK_WSPARCIA)}"
            )
            continue
        counts[kierunek] += 1
        zrodlo = cell.get("kierunek_wsparcia_zrodlo")
        if not zrodlo or not str(zrodlo).strip():
            problems.append(f"komorka {cell_id}: puste lub brakujace 'kierunek_wsparcia_zrodlo'")

    declared_odrzucenie = family.get("kierunek_ODRZUCENIE_H0")
    declared_brak = family.get("kierunek_BRAK_ODRZUCENIA_H0")
    if declared_odrzucenie is None or declared_brak is None:
        problems.append(
            "brak zadeklarowanych liczb na poziomie glownym artefaktu "
            "('kierunek_ODRZUCENIE_H0'/'kierunek_BRAK_ODRZUCENIA_H0')"
        )
    else:
        if counts["ODRZUCENIE_H0"] != declared_odrzucenie:
            problems.append(
                f"faktyczna liczba komorek ODRZUCENIE_H0 ({counts['ODRZUCENIE_H0']}) != "
                f"zadeklarowana (kierunek_ODRZUCENIE_H0={declared_odrzucenie})"
            )
        if counts["BRAK_ODRZUCENIA_H0"] != declared_brak:
            problems.append(
                f"faktyczna liczba komorek BRAK_ODRZUCENIA_H0 ({counts['BRAK_ODRZUCENIA_H0']}) != "
                f"zadeklarowana (kierunek_BRAK_ODRZUCENIA_H0={declared_brak})"
            )
    return problems


def check_primary_environment_matches_config(family: dict) -> list:
    """Dodatkowa kontrola (nie literal, sprawdzone przeciw CONFIG): kazda
    komorka twierdzaca, ze jej srodowisko to Primary, musi zgadzac sie z
    faktyczna wartoscia CONFIG::EXPERIMENT_CONFIG['environments']['primary'].

    B4C-05 v5: guard na ZERO komorek deklarujacych Primary - wiemy z definicji
    rodziny (A, B, K1-A/B, K5-A/B, K6 = 7 komorek), ze taka deklaracja MUSI
    wystapic; zero oznaczaloby, ze wlasny heurystyczny detektor tej kontroli
    (dopasowanie 'primary' w tekscie) sam sie zepsul, nie ze wszystko jest OK."""
    primary = EXPERIMENT_CONFIG["environments"]["primary"]
    problems = []
    n_claiming_primary = 0
    for cell in family.get("cells_active", []):
        srodowisko = cell.get("srodowisko", "")
        if "primary" in srodowisko.lower() or "['primary']" in srodowisko:
            n_claiming_primary += 1
            if primary not in srodowisko:
                problems.append(
                    f"komorka {cell['id']} deklaruje srodowisko Primary, ale nie zawiera "
                    f"aktualnej wartosci CONFIG ('{primary}'): {srodowisko!r}"
                )
    if n_claiming_primary == 0:
        problems.append(
            "ZERO komorek deklarujacych srodowisko Primary znalezionych - oczekiwano "
            "co najmniej jednej (A/B/K1/K5/K6); detektor tej kontroli sam sie zepsul "
            "albo artefakt jest pusty (B4C-05 v5)"
        )
    return problems


def run_all_checks(family: dict) -> dict:
    spec_2_6_labels = load_spec_2_6_labels()
    return {
        "a_adresy_rozwiazuja_sie": check_addresses_resolve(family),
        "b_komorki_w_spec_2_6": check_cells_in_spec_2_6(family, spec_2_6_labels),
        "c_licznosc_rowna_m": check_count_matches_m(family),
        "d_brak_wykluczonych_wsrod_aktywnych": check_no_excluded_among_active(family),
        "e_srodowisko_primary_zgodne_z_config": check_primary_environment_matches_config(family),
        "f_kierunek_wsparcia": check_kierunek_wsparcia(family),
    }


def resolved_count_label(name: str, family: dict) -> str:
    """B4C-05 v5/v6: liczba rozwiazanych/sprawdzonych elementow, wypisywana
    NAWET przy PASS - nagly spadek ma byc widoczny czlowiekowi."""
    n_active = len(family.get("cells_active", []))
    if name == "a_adresy_rozwiazuja_sie":
        return f"resolved={count_addresses(family)}"
    if name == "b_komorki_w_spec_2_6":
        return f"resolved={n_active}/{n_active} komorek w §2.6"
    if name == "c_licznosc_rowna_m":
        return f"resolved={n_active} (m={family.get('m')})"
    if name == "d_brak_wykluczonych_wsrod_aktywnych":
        return f"resolved={n_active} komorek aktywnych sprawdzonych"
    if name == "e_srodowisko_primary_zgodne_z_config":
        primary = EXPERIMENT_CONFIG["environments"]["primary"]
        n = sum(
            1 for c in family.get("cells_active", [])
            if "primary" in c.get("srodowisko", "").lower() or "['primary']" in c.get("srodowisko", "")
        )
        return f"resolved={n} (deklarujacych Primary='{primary}')"
    if name == "f_kierunek_wsparcia":
        n_with_field = sum(1 for c in family.get("cells_active", []) if c.get("kierunek_wsparcia") is not None)
        return f"resolved={n_with_field}/{n_active} komorek z kierunek_wsparcia"
    return ""


def main() -> int:
    family = load_family()
    results = run_all_checks(family)
    failed = False
    for name, problems in results.items():
        label = resolved_count_label(name, family)
        if problems:
            failed = True
            print(f"VALIDATE_BH_FAMILY: FAIL {name} - {label}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"VALIDATE_BH_FAMILY: PASS {name} - {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
