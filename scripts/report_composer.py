"""Report Composer - generuje reports/rerun_full_report_v0_11_0.md z danych
re-runu konfirmacyjnego (SPRINT v0.11.0, KROK 1 P2, decyzja architektoniczna
CTO 2026-07-26).

JEDNO ZRODLO PRAWDY raportu: ten generator Python. Przycisk "Generuj raport
do analizy" w panelu NIE sklada raportu w JS - tylko FETCHUJE ten gotowy
plik i pobiera go (Blob/download). Ten sam kod da sie pozniej (P2, KROK 2)
zawolac z pipeline.run_full_experiment() po re-runie - zero drugiej
implementacji, zero ryzyka transkrypcji (patrz GAP-DOCS w audycie P2).

ZERO OCENY / INTERPRETACJI DODANEJ PRZEZ GENERATOR. Kazda liczba i kazdy
status w raporcie to ECHO pola JUZ OBLICZONEGO w zrodlach:
  - reports/population/population_validation_v0_11_0.json (surowe wyniki
    re-runu: classification/valid_rate/pairwise_comparisons/omnibus_anova_raw
    per (lekcja x srodowisko x metryka), per_genome mean/ci95).
  - publications/competency_profile.json (profil: minimal VALIDATED, full,
    confirmatory_status per pojecie - to pole POCHODZI z
    docs/METRIC_STATUS_TABLE.md, generator go tylko przepisuje z atrybucja
    zrodla, NIE wylicza go sam).

Liczby w raporcie == liczby na ekranie panelu (sekcje "Lekcje i wyniki" i
"Porownanie genomow") - bo panel i ten generator czytaja TE SAME pliki. Nie
ma osobnego liczenia po zadnej stronie.

Auto-discovery jak w panelu (Object.keys sortowane na kazdym poziomie):
dodanie L1.3 do population_validation pojawi sie w raporcie bez zmiany tego
skryptu (ten sam wzorzec co sekcja Lekcje #3 w panel.js).

srodowiska kontrolne (stable_world) sa jawnie oznaczone
"[kontrola-zdegenerowane]" - deterministyczne, n_effective=1, CI95 nie ma
zastosowania z definicji (nie porazka pomiaru).

Uzycie:
    python scripts/report_composer.py
    (opcjonalnie: python scripts/report_composer.py <population.json> <profile.json> <out.md>)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

POPULATION_PATH = Path("reports/population/population_validation_v0_11_0.json")
PROFILE_PATH = Path("publications/competency_profile.json")
OUTPUT_PATH = Path("reports/rerun_full_report_v0_11_0.md")

CONTROL_ENVIRONMENTS = {"stable_world"}
CONTROL_MARKER = "[kontrola-zdegenerowane]"


def _load(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _fdr_pairs(entry: Dict[str, Any]) -> str:
    pc = entry.get("pairwise_comparisons") or {}
    if pc.get("n_pairs") is None:
        return "—"
    return f"{pc.get('n_fdr_significant_q_0_05')}/{pc.get('n_pairs')}"


def _raw_sig_pairs(entry: Dict[str, Any]) -> str:
    pc = entry.get("pairwise_comparisons") or {}
    n = pc.get("n_raw_significant_p_lt_0_05")
    return "—" if n is None else str(n)


def _anova_f(entry: Dict[str, Any]) -> str:
    a = entry.get("omnibus_anova_raw") or {}
    if not a.get("computable"):
        return "nieobliczalne"
    return f"f={_fmt(a.get('f'))}"


def _n_range(entry: Dict[str, Any]) -> str:
    pg = entry.get("per_genome") or {}
    ns = [g.get("n") for g in pg.values() if g.get("n") is not None]
    if not ns:
        return "—"
    lo, hi = min(ns), max(ns)
    return f"n={lo}" if lo == hi else f"n={lo}–{hi}"


def _metadata_section(population: Dict[str, Any], profile: Dict[str, Any]) -> List[str]:
    fdr = population.get("fdr_correction_omnibus") or {}
    return [
        "## 1. Metadane re-runu",
        "",
        "| Pole | Wartość | Źródło |",
        "|---|---|---|",
        f"| study_id | `{population.get('study_id', '—')}` | population_validation_v0_11_0.json |",
        f"| git_commit | `{population.get('git_commit', '—')}` | jw. |",
        f"| hard_halt_baseline (AUD-001) | `{population.get('hard_halt_baseline', '—')}` | jw. |",
        f"| manifest | `{population.get('manifest', '—')}` | jw. |",
        f"| n_raw_records | {population.get('n_raw_records', '—')} | jw. |",
        f"| fdr_correction.n_real_testable_cells | {fdr.get('n_real_testable_cells', '—')} | jw. |",
        f"| fdr_correction.alpha | {_fmt(fdr.get('alpha'), 6)} | jw. |",
        f"| profil.generated_at | {profile.get('generated_at', '—')} | competency_profile.json |",
        "",
        "**dataset_status (population):** " + str(population.get("dataset_status", "—")),
        "",
        "**dataset_status (profil):** " + str(profile.get("dataset_status", "—")),
        "",
    ]


def _results_section(population: Dict[str, Any]) -> List[str]:
    lines = [
        "## 2. Wyniki per (lekcja × środowisko × metryka)",
        "",
        "Liczby wprost z `population_validation_v0_11_0.json` — identyczne z sekcją "
        "„Lekcje i wyniki” panelu. `FDR pary` = pary genomów istotne po korekcie "
        "Benjamini-Hochberg (q=0.05) na teście Welcha; `raw p<0.05` = przed korektą; "
        "`ANOVA f` = surowy effect size (wejście do oceny mocy, NIE werdykt).",
        "",
        f"Środowiska kontrolne oznaczone `{CONTROL_MARKER}` — deterministyczne "
        "(n_effective=1, CI95 nie dotyczy z definicji, nie porażka pomiaru).",
        "",
    ]
    lessons = population.get("lessons") or {}
    for lesson_key in sorted(lessons.keys()):
        envs = lessons[lesson_key] or {}
        for env_key in sorted(envs.keys()):
            is_control = env_key in CONTROL_ENVIRONMENTS
            marker = f" {CONTROL_MARKER}" if is_control else ""
            metrics = envs[env_key] or {}
            lines.append(f"### {lesson_key} / {env_key}{marker}")
            lines.append("")
            lines.append("| Metryka | classification | valid_rate | n_valid/n_total | n (seedy) | FDR pary | raw p<0.05 | ANOVA f |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for metric_key in sorted(metrics.keys()):
                entry = metrics[metric_key] or {}
                lines.append(
                    "| {m} | {cls} | {vr} | {nv}/{nt} | {nr} | {fdr} | {raw} | {anova} |".format(
                        m=metric_key,
                        cls=entry.get("classification", "—"),
                        vr=_fmt(entry.get("valid_rate"), 4),
                        nv=entry.get("n_genomes_valid", "—"),
                        nt=entry.get("n_genomes_total", "—"),
                        nr=_n_range(entry),
                        fdr=_fdr_pairs(entry),
                        raw=_raw_sig_pairs(entry),
                        anova=_anova_f(entry),
                    )
                )
            lines.append("")
    return lines


def _profile_section(profile: Dict[str, Any]) -> List[str]:
    minimal = profile.get("minimal_profile") or {}
    full = profile.get("full_profile") or {}
    summary = profile.get("summary") or {}
    concept_by_name = {c["concept"]: c for c in profile.get("concepts", [])}

    lines = [
        "## 3. Profil kompetencji (z competency_profile.json)",
        "",
        f"Zmierzone: {summary.get('measured', '—')}/{summary.get('total_concepts', '—')} · "
        f"VALIDATED: {summary.get('validated', '—')} · "
        f"ci95_valid (ROBUST): {summary.get('valid_ci95', '—')}",
        "",
        "**Profil minimalny (VALIDATED)** — osie, dla których status konfirmacyjny "
        "to VALIDATED (źródło statusu: `docs/METRIC_STATUS_TABLE.md`, generator "
        "przepisuje pole `confirmatory_status`, nie wylicza go sam):",
        "",
        "- Osie poznawcze: " + (", ".join(minimal.get("cognitive_axes") or []) or "(brak)"),
        "- Zmienne stanu fizjologicznego: " + (", ".join(minimal.get("physiological_state_variables") or []) or "(brak)"),
        "",
        "**Profil pełny** (wszystkie 14 pojęć ontologii; `confirmatory_status` echo "
        "z METRIC_STATUS_TABLE.md):",
        "",
        "| Pojęcie | Rodzaj | Status pomiaru | confirmatory_status | classification | valid_rate | Źródło (lekcja/środ.) |",
        "|---|---|---|---|---|---|---|",
    ]

    order = (
        [c["concept"] for c in full.get("valid", [])]
        + [c["concept"] for c in full.get("degenerate", [])]
        + [c["concept"] for c in full.get("insufficient_data", [])]
    )
    for name in order:
        c = concept_by_name.get(name, {})
        lines.append(
            "| {name} | {kind} | {status} | {conf} | {cls} | {vr} | {src} |".format(
                name=name,
                kind=c.get("kind", "—"),
                status=c.get("status", "—"),
                conf=c.get("confirmatory_status") or "—",
                cls=c.get("classification") or "—",
                vr=_fmt(c.get("valid_rate"), 4),
                src=c.get("source_lesson") or "—",
            )
        )
    lines.append("")
    return lines


def _per_genome_section(population: Dict[str, Any]) -> List[str]:
    lines = [
        "## 4. Dane per-genom (surowe, załącznik)",
        "",
        "Średnia ± CI95 per genom, wprost z `per_genome` w "
        "`population_validation_v0_11_0.json`. Środowiska kontrolne pominięte "
        "(deterministyczne, patrz §2).",
        "",
    ]
    lessons = population.get("lessons") or {}
    for lesson_key in sorted(lessons.keys()):
        envs = lessons[lesson_key] or {}
        for env_key in sorted(envs.keys()):
            if env_key in CONTROL_ENVIRONMENTS:
                continue
            metrics = envs[env_key] or {}
            for metric_key in sorted(metrics.keys()):
                entry = metrics[metric_key] or {}
                pg = entry.get("per_genome") or {}
                if not pg:
                    continue
                lines.append(f"### {lesson_key} / {env_key} / {metric_key}")
                lines.append("")
                lines.append("| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |")
                lines.append("|---|---|---|---|---|---|---|")
                for genome in sorted(pg.keys()):
                    g = pg[genome]
                    lines.append(
                        "| {g} | {mean} | {lo} | {hi} | {n} | {neff} | {valid} |".format(
                            g=genome,
                            mean=_fmt(g.get("mean"), 6),
                            lo=_fmt(g.get("ci95_low"), 6),
                            hi=_fmt(g.get("ci95_high"), 6),
                            n=g.get("n", "—"),
                            neff=g.get("n_effective", "—"),
                            valid=g.get("ci95_valid", "—"),
                        )
                    )
                lines.append("")
    return lines


def compose_report(population: Dict[str, Any], profile: Dict[str, Any]) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = [
        "# Raport re-runu konfirmacyjnego v0.11.0 — dane do analizy",
        "",
        f"> Wygenerowany {generated} przez `scripts/report_composer.py` z "
        "`reports/population/population_validation_v0_11_0.json` + "
        "`publications/competency_profile.json`. **ZERO oceny/interpretacji "
        "dodanej przez generator** — każda liczba i status to echo pola już "
        "obliczonego w źródłach. Liczby identyczne z panelem (sekcje „Lekcje i "
        "wyniki” oraz „Porównanie genomów”) — ten sam plik źródłowy, brak "
        "osobnego liczenia.",
        "",
    ]
    body = (
        _metadata_section(population, profile)
        + _results_section(population)
        + _profile_section(profile)
        + _per_genome_section(population)
    )
    return "\n".join(header + body) + "\n"


def write_report(
    population_path: Path = POPULATION_PATH,
    profile_path: Path = PROFILE_PATH,
    out_path: Path = OUTPUT_PATH,
) -> Path:
    population = _load(population_path)
    profile = _load(profile_path)
    report = compose_report(population, profile)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    return out_path


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    pop = Path(argv[0]) if len(argv) > 0 else POPULATION_PATH
    prof = Path(argv[1]) if len(argv) > 1 else PROFILE_PATH
    out = Path(argv[2]) if len(argv) > 2 else OUTPUT_PATH
    path = write_report(pop, prof, out)
    print(f"Report composed: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
