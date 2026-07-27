"""Validate Artifact Freshness (SPRINT v0.11.0 P2 KROK 3, CTO 2026-07-27).

CEL: zaden artefakt POCHODNY nie moze CICHO rozjechac sie z
reports/population/population_validation_v0_11_0.json (zrodlo prawdy re-runu
konfirmacyjnego). Ten walidator porownuje TRZY artefakty ze zrodlem:

  1. docs/METRIC_STATUS_TABLE.md      <- PRIORYTET: jedyny bez generatora
     (reczna proza+liczby - tu powstal realny bug: tabela mowila
     "Welch-pary (0/253)" dla Working Memory, podczas gdy zrodlo mowilo
     69/253 - patrz commit "v0.11 KOREKTA liczb parowych").
  2. publications/competency_profile.json  (generator: KROK 2 post-run /
     clos_scientist/competency_profile.py - ALE moze byc reczne uruchomienie
     ktore ktos zapomnial powtorzyc po nowym re-runie).
  3. reports/rerun_full_report_v0_11_0.md  (generator: scripts/report_composer.py -
     ta sama uwaga: plik w repo moze byc STARSZY niz population_validation).

MECHANIKA (ta sama dla wszystkich trzech): z kazdego artefaktu wyciagana
jest para liczb "n_fdr_significant_q_0_05 / n_pairs" per (lekcja, srodowisko,
metryka), i porownywana z DOKLADNIE tym samym polem w
population_validation_v0_11_0.json. Rozjazd = FAIL z nazwa
artefaktu+wiersza+liczbami (oczekiwane vs znalezione). Komorki, ktorych
(lekcja, srodowisko, metryka) NIE ISTNIEJE w zrodle (np. drift_world - poza
zakresem re-runu, Architekt potwierdzil ze ten scenariusz nie istnieje w
danych v0.11) sa POMIJANE w ocenie PASS/FAIL, ale wypisywane jako
informacyjne "poza zakresem re-runu", zeby nikt nie pomylil pominiecia z
rozjazdem. 0/253 to POPRAWNA wartosc dla Pattern Retention/noise_world (tak
mowi zrodlo) - walidator NIGDY nie zaklada, ze 0 = blad; porownuje wylacznie
z liczba w zrodle.

Uzycie:
    python scripts/validate_artifact_freshness.py
Kod wyjscia: 0 = wszystkie trzy artefakty zgodne ze zrodlem, 1 = co najmniej
jeden rozjazd znaleziony.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

POPULATION_PATH = Path("reports/population/population_validation_v0_11_0.json")
METRIC_STATUS_TABLE_PATH = Path("docs/METRIC_STATUS_TABLE.md")
COMPETENCY_PROFILE_PATH = Path("publications/competency_profile.json")
ANALYSIS_REPORT_PATH = Path("reports/rerun_full_report_v0_11_0.md")

# Wylapuje "X/Y" gdziekolwiek w kolumnie/komorce (np. "Welch-pary (69/253, 27%)",
# "75/78 obliczalnych", czyste "69/253") - PIERWSZE dopasowanie w komorce.
PAIR_RE = re.compile(r"(\d+)\s*/\s*(\d+)")

SourceKey = Tuple[str, str, str]  # (lesson, environment, metric_key)


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_source_lookup(population: Dict[str, Any]) -> Dict[SourceKey, Tuple[Optional[int], Optional[int]]]:
    """(lekcja, srodowisko, metric_key) -> (n_fdr_significant_q_0_05, n_pairs)
    dla kazdej komorki faktycznie obecnej w population_validation."""
    out: Dict[SourceKey, Tuple[Optional[int], Optional[int]]] = {}
    for lesson, envs in (population.get("lessons") or {}).items():
        for env, metrics in (envs or {}).items():
            for metric_key, entry in (metrics or {}).items():
                pc = (entry or {}).get("pairwise_comparisons") or {}
                if pc.get("n_pairs") is not None:
                    out[(lesson, env, metric_key)] = (
                        pc.get("n_fdr_significant_q_0_05"), pc.get("n_pairs")
                    )
    return out


def _match_metric_key(table_name: str, lesson: str, env: str,
                       source: Dict[SourceKey, Tuple[Optional[int], Optional[int]]]) -> Optional[str]:
    """Nazwa z tabeli/raportu (np. 'Working Memory') moze byc SKROCONA wzgledem
    klucza w population_validation (np. 'Working Memory (MAE@50)') - dopasowanie
    po rowności ALBO po prefiksie 'nazwa ('."""
    for (l, e, m) in source:
        if l == lesson and e == env and (m == table_name or m.startswith(table_name + " (")):
            return m
    return None


def _extract_pair(cell_text: str) -> Optional[Tuple[int, int]]:
    m = PAIR_RE.search(cell_text)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def parse_metric_status_table_rows(text: str) -> List[Dict[str, str]]:
    """Parsuje WYLACZNIE tabele §4b (naglowek '| Lekcja | Środ. | Metryka |
    ... | Test | Rekomendacja |') - §4a (NOT_MEASURED) ma inny ksztalt
    kolumn i jest pomijana (Perception/Attention/... nie maja par FDR do
    porownania niczego). Zwraca liste {lesson, env, metric, test_cell,
    raw_line} - jedna na wiersz danych (nie naglowek/separator)."""
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Lekcja | Środ. | Metryka |"):
            header_idx = i
            break
    if header_idx is None:
        return []

    rows = []
    # +2: pomin linie naglowka i separatora "|---|---|...|"
    for line in lines[header_idx + 2:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cols = [c.strip() for c in stripped.split("|")]
        # ['', Lekcja, Środ., Metryka, Definicja, Interpretacja, Measurement,
        #  Construct, Power, Confirm., Test, Rekomendacja, '']
        if len(cols) < 12:
            break
        lesson, env, metric, test_cell = cols[1], cols[2], cols[3], cols[10]
        if not re.match(r"^L\d", lesson):
            break
        rows.append({"lesson": lesson, "env": env, "metric": metric,
                      "test_cell": test_cell, "raw_line": stripped})
    return rows


def check_metric_status_table(
    text: str, source: Dict[SourceKey, Tuple[Optional[int], Optional[int]]]
) -> Tuple[List[str], List[str]]:
    violations: List[str] = []
    info: List[str] = []
    for row in parse_metric_status_table_rows(text):
        pair = _extract_pair(row["test_cell"])
        if pair is None:
            continue  # np. "—" (kontrola) albo "Welch-pary" bez liczby - nic do porownania
        matched_key = _match_metric_key(row["metric"], row["lesson"], row["env"], source)
        if matched_key is None:
            info.append(
                f"docs/METRIC_STATUS_TABLE.md: {row['lesson']}/{row['env']}/{row['metric']} "
                f"— poza zakresem re-runu (brak w population_validation), pominieto"
            )
            continue
        expected = source[(row["lesson"], row["env"], matched_key)]
        if pair != expected:
            violations.append(
                f"docs/METRIC_STATUS_TABLE.md: {row['lesson']}/{row['env']}/{row['metric']} "
                f"— tabela mowi {pair[0]}/{pair[1]}, zrodlo (population_validation) mowi "
                f"{expected[0]}/{expected[1]}"
            )
    return violations, info


def check_competency_profile(
    profile: Dict[str, Any], source: Dict[SourceKey, Tuple[Optional[int], Optional[int]]]
) -> Tuple[List[str], List[str]]:
    violations: List[str] = []
    info: List[str] = []
    for c in profile.get("concepts", []):
        if c.get("status") != "measured":
            continue
        source_lesson = c.get("source_lesson") or ""
        if "/" not in source_lesson:
            continue
        lesson, env = source_lesson.split("/", 1)
        comparison = c.get("genome_comparison") or {}
        if comparison.get("n_pairs") is None:
            continue
        pair = (comparison.get("n_fdr_significant_q_0_05"), comparison.get("n_pairs"))
        matched_key = _match_metric_key(c["concept"], lesson, env, source)
        if matched_key is None:
            info.append(
                f"competency_profile.json: {lesson}/{env}/{c['concept']} "
                f"— poza zakresem re-runu (brak w population_validation), pominieto"
            )
            continue
        expected = source[(lesson, env, matched_key)]
        if pair != expected:
            violations.append(
                f"competency_profile.json: {lesson}/{env}/{c['concept']} "
                f"— profil mowi {pair[0]}/{pair[1]}, zrodlo mowi {expected[0]}/{expected[1]}"
            )
    return violations, info


def parse_analysis_report_rows(text: str) -> List[Dict[str, str]]:
    """reports/rerun_full_report_v0_11_0.md (scripts/report_composer.py):
    naglowki '### L1.1 / noise_world' dają kontekst (lekcja, srodowisko),
    tabela pod kazdym ma 8 kolumn (Metryka/classification/valid_rate/
    n_valid_n_total/n (seedy)/FDR pary/raw p<0.05/ANOVA f) - 'FDR pary' to
    indeks 6 po splicie, NIE 5 (BLAD ZLAPANY 2026-07-27 wlasnym testem
    negatywnym: pierwsza wersja uzywala cols[5], czyli kolumny 'n (seedy)'
    - "n=185" nie zawiera "/", wiec _extract_pair() zawsze zwracal None i
    caly ten artefakt byl CICHO pomijany, mimo ze walidator zglaszal "OK".
    Dokladnie ten sam rodzaj bledu, ktoremu ten walidator ma zapobiegac u
    INNYCH - zlapany tutaj przez test negatywny z doslownym, prawdziwym
    wierszem, ktory przestal pasowac). Metryka (indeks 1) to DOKLADNIE
    klucz z population_validation (report_composer go echuje 1:1, bez
    skracania)."""
    rows = []
    lesson, env = None, None
    header_re = re.compile(r"^###\s+(L\d\.\d)\s*/\s*([a-z_]+)")
    for line in text.splitlines():
        h = header_re.match(line.strip())
        if h:
            lesson, env = h.group(1), h.group(2)
            continue
        stripped = line.strip()
        if not stripped.startswith("|") or lesson is None:
            continue
        cols = [c.strip() for c in stripped.split("|")]
        # ['', Metryka, classification, valid_rate, n_valid/n_total,
        #  n (seedy), FDR pary, raw p<0.05, ANOVA f, '']
        if len(cols) < 10 or cols[1] in ("Metryka", "---"):
            continue
        if set(cols[1]) <= {"-"}:
            continue
        rows.append({"lesson": lesson, "env": env, "metric": cols[1], "fdr_cell": cols[6]})
    return rows


def check_analysis_report(
    text: str, source: Dict[SourceKey, Tuple[Optional[int], Optional[int]]]
) -> Tuple[List[str], List[str]]:
    violations: List[str] = []
    info: List[str] = []
    for row in parse_analysis_report_rows(text):
        pair = _extract_pair(row["fdr_cell"])
        if pair is None:
            continue
        key = (row["lesson"], row["env"], row["metric"])
        if key not in source:
            info.append(
                f"rerun_full_report_v0_11_0.md: {row['lesson']}/{row['env']}/{row['metric']} "
                f"— poza zakresem re-runu (brak w population_validation), pominieto"
            )
            continue
        expected = source[key]
        if pair != expected:
            violations.append(
                f"rerun_full_report_v0_11_0.md: {row['lesson']}/{row['env']}/{row['metric']} "
                f"— raport mowi {pair[0]}/{pair[1]}, zrodlo mowi {expected[0]}/{expected[1]}"
            )
    return violations, info


def run_all_checks(
    population: Dict[str, Any],
    table_text: str,
    profile: Dict[str, Any],
    report_text: str,
) -> Tuple[List[str], List[str]]:
    source = build_source_lookup(population)
    all_violations: List[str] = []
    all_info: List[str] = []
    for check in (
        lambda: check_metric_status_table(table_text, source),
        lambda: check_competency_profile(profile, source),
        lambda: check_analysis_report(report_text, source),
    ):
        v, i = check()
        all_violations += v
        all_info += i
    return all_violations, all_info


def main() -> int:
    missing = [p for p in (POPULATION_PATH, METRIC_STATUS_TABLE_PATH,
                           COMPETENCY_PROFILE_PATH, ANALYSIS_REPORT_PATH) if not p.exists()]
    if missing:
        print("VALIDATE_ARTIFACT_FRESHNESS: brak plikow: " + ", ".join(str(p) for p in missing))
        return 1

    population = _load_json(POPULATION_PATH)
    table_text = METRIC_STATUS_TABLE_PATH.read_text(encoding="utf-8")
    profile = _load_json(COMPETENCY_PROFILE_PATH)
    report_text = ANALYSIS_REPORT_PATH.read_text(encoding="utf-8")

    violations, info = run_all_checks(population, table_text, profile, report_text)

    for line in info:
        print(f"VALIDATE_ARTIFACT_FRESHNESS: info: {line}")

    if violations:
        print(f"VALIDATE_ARTIFACT_FRESHNESS: {len(violations)} rozjazd(ow) ze zrodlem")
        for v in violations:
            print(f"  FAIL: {v}")
        return 1

    print("VALIDATE_ARTIFACT_FRESHNESS: OK (tabela/profil/raport zgodne z population_validation)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
