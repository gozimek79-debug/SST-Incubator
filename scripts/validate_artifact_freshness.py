"""Validate Artifact Freshness (SPRINT v0.11.0 P2 KROK 3 + KROK 4, CTO 2026-07-27).

CEL: zaden artefakt POCHODNY nie moze CICHO rozjechac sie z
reports/population/population_validation_v0_11_0.json (zrodlo prawdy re-runu
konfirmacyjnego). Ten walidator porownuje TRZY artefakty ze zrodlem:

  1. docs/METRIC_STATUS_TABLE.md      <- PRIORYTET: jedyny bez generatora
     (reczna proza+liczby - tu powstal realny bug: tabela mowila
     "Welch-pary (0/253)" dla Working Memory, podczas gdy zrodlo mowilo
     69/253 - patrz commit "v0.11 KOREKTA liczb parowych").
  2. publications/competency_profile.json  (generator: KROK 2 post-run /
     clos_scientist/competency_profile.py).
  3. reports/rerun_full_report_v0_11_0.md  (generator: scripts/report_composer.py).

KROK 3: sprawdzal WYLACZNIE pary FDR (n_fdr_significant_q_0_05/n_pairs).
KROK 4 (2026-07-27, domyka GAP-DOCS BEZ generowania tabeli - decyzja
audytora: wartoscia tabeli sa przypisy/uzasadnienia, ktorych generator nie
odtworzy; ten walidator chroni LICZBY, proza zostaje ludzka) rozszerza
pokrycie na CALA powierzchnie liczbowa, ktora artefakty faktycznie niosa:

  - RAPORT (8 kolumn, 7 poza juz istniejacym FDR): classification,
    valid_rate, n_genomes_valid/total, n (seedy, zakres per_genome.n),
    raw p<0.05, ANOVA f.
  - PROFIL (analogicznie, tylko pola ktore faktycznie niesie): classification,
    valid_rate, n_genomes_valid/total, ANOVA f, n_pairs_computable.
  - TABELA: spojnosc PROCENTU w "(X/Y, Z%)" - Z MUSI == round(100*X/Y) -
    lapie polowiczna poprawke (zmieniony ulamek, zapomniany procent).

Komorki, ktorych (lekcja, srodowisko, metryka) NIE ISTNIEJE w zrodle (np.
drift_world - poza zakresem re-runu, Architekt potwierdzil ze ten scenariusz
nie istnieje w danych v0.11) sa POMIJANE w ocenie PASS/FAIL, ale wypisywane
jako informacyjne "poza zakresem re-runu". Pole, ktorego NIE DA SIE
jednoznacznie sparsowac z prozy, jest wypisywane jako "niesprawdzalne" -
walidator NIGDY nie zgaduje ani nie milczy w takim przypadku. 0/253 to
POPRAWNA wartosc dla Pattern Retention/noise_world (tak mowi zrodlo) -
walidator NIGDY nie zaklada, ze 0 = blad; porownuje wylacznie z liczba w
zrodle.

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
PERCENT_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*,\s*(\d+)\s*%")

SourceKey = Tuple[str, str, str]  # (lesson, environment, metric_key)

# Sentinel: komorka NIE jest pusta ("—"), ale tez nie pasuje do zadnego
# oczekiwanego ksztaltu - "niesprawdzalne", NIE "zgadniete jako None".
UNPARSEABLE = object()

_DASH_VALUES = {"—", "-", "—/—", "-/-", ""}


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_source_lookup(population: Dict[str, Any]) -> Dict[SourceKey, Dict[str, Any]]:
    """(lekcja, srodowisko, metric_key) -> slownik WSZYSTKICH pol dostepnych
    w population_validation dla tej komorki - KROK 4 rozszerza to z samej
    pary FDR (KROK 3) na cala dostepna powierzchnie liczbowa."""
    out: Dict[SourceKey, Dict[str, Any]] = {}
    for lesson, envs in (population.get("lessons") or {}).items():
        for env, metrics in (envs or {}).items():
            for metric_key, entry in (metrics or {}).items():
                entry = entry or {}
                pc = entry.get("pairwise_comparisons") or {}
                if pc.get("n_pairs") is None:
                    continue
                anova = entry.get("omnibus_anova_raw") or {}
                per_genome = entry.get("per_genome") or {}
                n_values = [g.get("n") for g in per_genome.values() if g.get("n") is not None]
                out[(lesson, env, metric_key)] = {
                    "n_fdr": pc.get("n_fdr_significant_q_0_05"),
                    "n_pairs": pc.get("n_pairs"),
                    "n_pairs_computable": pc.get("n_pairs_computable"),
                    "n_raw_significant": pc.get("n_raw_significant_p_lt_0_05"),
                    "anova_f": anova.get("f") if anova.get("computable") else None,
                    "anova_computable": bool(anova.get("computable")),
                    "classification": entry.get("classification"),
                    "valid_rate": entry.get("valid_rate"),
                    "n_genomes_total": entry.get("n_genomes_total"),
                    "n_genomes_valid": entry.get("n_genomes_valid"),
                    "n_min": min(n_values) if n_values else None,
                    "n_max": max(n_values) if n_values else None,
                }
    return out


def _match_metric_key(table_name: str, lesson: str, env: str,
                       source: Dict[SourceKey, Dict[str, Any]]) -> Optional[str]:
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


# ============================================================================
# Parsery pojedynczych komorek (proza -> wartosc | None (pole puste, "—") |
# UNPARSEABLE (cos tam jest, ale nie pasuje do zadnego znanego ksztaltu))
# ============================================================================

def _parse_int_cell(s: str) -> Any:
    s = s.strip()
    if s in _DASH_VALUES:
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return UNPARSEABLE


def _parse_float4_cell(s: str) -> Any:
    """valid_rate: raport/profil pokazuja 4 miejsca po przecinku."""
    s = s.strip()
    if s in _DASH_VALUES:
        return None
    if re.fullmatch(r"-?\d+(?:\.\d+)?", s):
        return round(float(s), 4)
    return UNPARSEABLE


def _parse_anova_cell(s: str) -> Any:
    s = s.strip()
    if s == "nieobliczalne":
        return None
    m = re.fullmatch(r"f=(-?\d+(?:\.\d+)?)", s)
    if m:
        return round(float(m.group(1)), 4)
    return UNPARSEABLE


def _parse_int_pair_cell(s: str) -> Any:
    s = s.strip()
    if s in _DASH_VALUES:
        return None
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    return UNPARSEABLE


def _parse_n_range_cell(s: str) -> Any:
    s = s.strip()
    if s in _DASH_VALUES:
        return None
    m = re.fullmatch(r"n=(\d+)(?:[–-](\d+))?", s)
    if m:
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        return lo, hi
    return UNPARSEABLE


def _parse_text_cell(s: str) -> Any:
    s = s.strip()
    return None if s in _DASH_VALUES else s


def _fmt_val(v: Any) -> str:
    return "—" if v is None else str(v)


def _record(violations: List[str], info: List[str], artifact: str,
            lesson: str, env: str, metric: str, field: str,
            parsed: Any, expected: Any) -> None:
    if parsed is UNPARSEABLE:
        info.append(
            f"{artifact}: {lesson}/{env}/{metric}/{field} — niesprawdzalne "
            "(nie udalo sie jednoznacznie sparsowac komorki)"
        )
        return
    if parsed != expected:
        violations.append(
            f"{artifact}: {lesson}/{env}/{metric}/{field} — artefakt mowi "
            f"{_fmt_val(parsed)}, zrodlo mowi {_fmt_val(expected)}"
        )


# ============================================================================
# §4b docs/METRIC_STATUS_TABLE.md — pary FDR (KROK 3) + spojnosc procentu (KROK 4)
# ============================================================================

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
    text: str, source: Dict[SourceKey, Dict[str, Any]]
) -> Tuple[List[str], List[str]]:
    violations: List[str] = []
    info: List[str] = []
    for row in parse_metric_status_table_rows(text):
        pair = _extract_pair(row["test_cell"])
        if pair is not None:
            matched_key = _match_metric_key(row["metric"], row["lesson"], row["env"], source)
            if matched_key is None:
                info.append(
                    f"docs/METRIC_STATUS_TABLE.md: {row['lesson']}/{row['env']}/{row['metric']} "
                    f"— poza zakresem re-runu (brak w population_validation), pominieto"
                )
            else:
                expected = (source[(row["lesson"], row["env"], matched_key)]["n_fdr"],
                            source[(row["lesson"], row["env"], matched_key)]["n_pairs"])
                if pair != expected:
                    violations.append(
                        f"docs/METRIC_STATUS_TABLE.md: {row['lesson']}/{row['env']}/{row['metric']} "
                        f"— tabela mowi {pair[0]}/{pair[1]}, zrodlo (population_validation) mowi "
                        f"{expected[0]}/{expected[1]}"
                    )

        # KROK 4: spojnosc procentu - NIEZALEZNA od zrodla, czysto wewnetrzna
        # sprzecznosc "(X/Y, Z%)" - lapie polowiczna poprawke liczby bez
        # przeliczenia towarzyszacego procentu.
        pm = PERCENT_RE.search(row["test_cell"])
        if pm:
            x, y, z = int(pm.group(1)), int(pm.group(2)), int(pm.group(3))
            if y > 0:
                expected_pct = round(100 * x / y)
                if expected_pct != z:
                    violations.append(
                        f"docs/METRIC_STATUS_TABLE.md: {row['lesson']}/{row['env']}/{row['metric']} "
                        f"— procent niespojny z ulamkiem: {x}/{y} = {expected_pct}%, tabela mowi {z}%"
                    )
    return violations, info


# ============================================================================
# publications/competency_profile.json
# ============================================================================

def check_competency_profile(
    profile: Dict[str, Any], source: Dict[SourceKey, Dict[str, Any]]
) -> Tuple[List[str], List[str]]:
    violations: List[str] = []
    info: List[str] = []
    artifact = "competency_profile.json"
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
        metric = c["concept"]
        matched_key = _match_metric_key(metric, lesson, env, source)
        if matched_key is None:
            info.append(
                f"{artifact}: {lesson}/{env}/{metric} "
                f"— poza zakresem re-runu (brak w population_validation), pominieto"
            )
            continue
        expected = source[(lesson, env, matched_key)]

        pair = (comparison.get("n_fdr_significant_q_0_05"), comparison.get("n_pairs"))
        if pair != (expected["n_fdr"], expected["n_pairs"]):
            violations.append(
                f"{artifact}: {lesson}/{env}/{metric}/FDR pary — profil mowi "
                f"{pair[0]}/{pair[1]}, zrodlo mowi {expected['n_fdr']}/{expected['n_pairs']}"
            )

        _record(violations, info, artifact, lesson, env, metric, "classification",
                c.get("classification"), expected["classification"])
        vr = c.get("valid_rate")
        _record(violations, info, artifact, lesson, env, metric, "valid_rate",
                None if vr is None else round(vr, 4),
                None if expected["valid_rate"] is None else round(expected["valid_rate"], 4))
        _record(violations, info, artifact, lesson, env, metric, "n_genomes_valid",
                c.get("n_genomes_valid"), expected["n_genomes_valid"])
        _record(violations, info, artifact, lesson, env, metric, "n_genomes_total",
                c.get("n_genomes_total"), expected["n_genomes_total"])
        _record(violations, info, artifact, lesson, env, metric, "n_pairs_computable",
                comparison.get("n_pairs_computable"), expected["n_pairs_computable"])
        af = comparison.get("anova_f") if comparison.get("anova_computable") else None
        _record(violations, info, artifact, lesson, env, metric, "anova_f",
                None if af is None else round(af, 4),
                None if expected["anova_f"] is None else round(expected["anova_f"], 4))
    return violations, info


# ============================================================================
# reports/rerun_full_report_v0_11_0.md
# ============================================================================

def parse_analysis_report_rows(text: str) -> List[Dict[str, str]]:
    """reports/rerun_full_report_v0_11_0.md (scripts/report_composer.py):
    naglowki '### L1.1 / noise_world' dają kontekst (lekcja, srodowisko),
    tabela pod kazdym ma 8 kolumn: Metryka(1)/classification(2)/valid_rate(3)/
    n_valid_n_total(4)/n (seedy)(5)/FDR pary(6)/raw p<0.05(7)/ANOVA f(8) po
    splicie po "|" (BLAD ZLAPANY 2026-07-27 wlasnym testem negatywnym:
    pierwsza wersja uzywala cols[5] dla FDR pary, czyli kolumny 'n (seedy)' -
    "n=185" nie zawiera "/", wiec _extract_pair() zawsze zwracal None i caly
    ten artefakt byl CICHO pomijany, mimo ze walidator zglaszal "OK"). Metryka
    (indeks 1) to DOKLADNIE klucz z population_validation (report_composer go
    echuje 1:1, bez skracania)."""
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
        if len(cols) < 10 or cols[1] in ("Metryka", "---"):
            continue
        if set(cols[1]) <= {"-"}:
            continue
        rows.append({
            "lesson": lesson, "env": env, "metric": cols[1],
            "classification_cell": cols[2],
            "valid_rate_cell": cols[3],
            "n_valid_total_cell": cols[4],
            "n_seedy_cell": cols[5],
            "fdr_cell": cols[6],
            "raw_p_cell": cols[7],
            "anova_cell": cols[8],
        })
    return rows


def check_analysis_report(
    text: str, source: Dict[SourceKey, Dict[str, Any]]
) -> Tuple[List[str], List[str]]:
    violations: List[str] = []
    info: List[str] = []
    artifact = "rerun_full_report_v0_11_0.md"
    for row in parse_analysis_report_rows(text):
        pair = _extract_pair(row["fdr_cell"])
        key = (row["lesson"], row["env"], row["metric"])
        if key not in source:
            if pair is not None:
                info.append(
                    f"{artifact}: {row['lesson']}/{row['env']}/{row['metric']} "
                    f"— poza zakresem re-runu (brak w population_validation), pominieto"
                )
            continue
        expected = source[key]
        lesson, env, metric = row["lesson"], row["env"], row["metric"]

        if pair is not None and pair != (expected["n_fdr"], expected["n_pairs"]):
            violations.append(
                f"{artifact}: {lesson}/{env}/{metric}/FDR pary — raport mowi "
                f"{pair[0]}/{pair[1]}, zrodlo mowi {expected['n_fdr']}/{expected['n_pairs']}"
            )

        _record(violations, info, artifact, lesson, env, metric, "classification",
                _parse_text_cell(row["classification_cell"]), expected["classification"])

        expected_vr = None if expected["valid_rate"] is None else round(expected["valid_rate"], 4)
        _record(violations, info, artifact, lesson, env, metric, "valid_rate",
                _parse_float4_cell(row["valid_rate_cell"]), expected_vr)

        parsed_nt = _parse_int_pair_cell(row["n_valid_total_cell"])
        expected_nt = None
        if expected["n_genomes_valid"] is not None or expected["n_genomes_total"] is not None:
            expected_nt = (expected["n_genomes_valid"], expected["n_genomes_total"])
        _record(violations, info, artifact, lesson, env, metric, "n_valid/n_total",
                parsed_nt, expected_nt)

        parsed_n_range = _parse_n_range_cell(row["n_seedy_cell"])
        expected_n_range = None
        if expected["n_min"] is not None:
            expected_n_range = (expected["n_min"], expected["n_max"])
        _record(violations, info, artifact, lesson, env, metric, "n (seedy)",
                parsed_n_range, expected_n_range)

        _record(violations, info, artifact, lesson, env, metric, "raw p<0.05",
                _parse_int_cell(row["raw_p_cell"]), expected["n_raw_significant"])

        expected_anova = None if expected["anova_f"] is None else round(expected["anova_f"], 4)
        _record(violations, info, artifact, lesson, env, metric, "ANOVA f",
                _parse_anova_cell(row["anova_cell"]), expected_anova)
    return violations, info


# ============================================================================
# Orkiestracja
# ============================================================================

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
