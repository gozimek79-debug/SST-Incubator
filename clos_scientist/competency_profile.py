"""Competency Profile - formatuje wyjscie Capability Analyzer do
competency_profile.json / competency_profile.md + auto-karty genomow.

Zero nowych obliczen: caly artefakt to reformatowanie
clos_scientist.capability_analyzer.build_capability_profile_from_population()
(re-run konfirmacyjny v0.11, 23 genomy, n=185 - SPRINT v0.11.0 P0, CTO
2026-07-22). Pojecia insufficient_data MUSZA byc w profilu, jawnie
oznaczone, bez zadnej wartosci liczbowej. Zero ocen slownych/gwiazdek/
poziomow - tylko liczby i status.

Profil minimalny vs pelny - PO PRZEJSCIU NA DANE KONFIRMACYJNE (SPRINT
v0.11.0 P0):
  - MINIMALNY (oficjalny) = WYLACZNIE pojecia ze statusem konfirmacyjnym
    VALIDATED (docs/METRIC_STATUS_TABLE.md) - NIE surowe ci95_valid.
    "ROBUST" (ci95 wiarygodne, pomiar dziala) i "VALIDATED" (przetrwalo
    Kruskal-Wallis/leave-one-out/Red Team, dyskryminuje genomy) to DWA
    ROZNE pytania (docs/VALIDITY_REPORT.md "Kluczowe odkrycie") - Pattern
    Retention jest 100% ci95-valid (ROBUST) ale tylko EXPERIMENTAL, wiec
    NIE wchodzi do profilu minimalnego mimo ze kazdy genom ma ci95_valid=True.
  - PELNY zachowuje WSZYSTKO: valid/degenerate to nadal ci95_valid (per
    genom, NIEZALEZNE od confirmatory_status), insufficient_data = brak
    lekcji/mechanizmu. Kazdy zmierzony koncept niesie WLASNY
    confirmatory_status, wiec czytelnik full_profile widzi obie osie
    naraz (wiarygodnosc pomiaru vs. status konfirmacyjny), nie tylko jedna.
  - Klasyfikacja (_concept_validity_state) MUSI byc zsynchronizowana z
    clos_studio/panel/panel.js:classifyConcepts() - to samo pytanie zadane
    w dwoch miejscach (artefakt .md/.json i panel na zywo), musi dawac ta
    sama odpowiedz.

Archiwum: profil eksploracyjny v0.10.1 (n=10, 2 genomy: default/
highly_plastic) NIE jest kasowany ani nadpisywany w miejscu - zachowany
osobno jako publications/competency_profile_v0_10_1_exploratory.{json,md}
(patrz archive_exploratory_profile() na dole pliku), dokladnie tak jak
population_validation_v0_10_1.json zostal obok population_validation_v0_11_0.json.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from clos_scientist.capability_analyzer import (
    POPULATION_PATH,
    build_capability_profile_from_population,
)

# publications/ (nie reports/academy/) - zeby nie kolidowac ze
# scripts/validate_artifacts.py, ktory oczekuje w reports/academy/ wylacznie
# raportow lekcji (pola 'lesson'/'scenario').
OUTPUT_DIR = Path("publications")

ARCHIVE_JSON_NAME = "competency_profile_v0_10_1_exploratory.json"
ARCHIVE_MD_NAME = "competency_profile_v0_10_1_exploratory.md"


def _concept_validity_state(c: Dict[str, Any]) -> str:
    """valid / degenerate / insufficient. Zwierciadlo
    clos_studio/panel/panel.js:classifyConcepts() - synchronizowac razem.
    Odpowiada WYLACZNIE na pytanie "czy pomiar jest wiarygodny per genom"
    (ci95_valid) - NIE na pytanie "czy koncept jest VALIDATED
    konfirmacyjnie" (patrz confirmatory_status na kazdym koncepcie).

    BLAD ZLAPANY PRZY WERYFIKACJI (2026-07-22, przed pokazaniem wyniku
    CTO): pierwsza wersja tej funkcji sprawdzala per-genom
    c["genomes"][g]["ci95_valid"] - ale w population_validation_v0_11_0.json
    ci95_valid=True dla WSZYSTKICH 23 genomow Adaptation, mimo ze
    classification=GENOME-FRAGILE (n_genomes_valid=13/23) - bo prog
    GENOME-ROBUST to ci95_valid=True ORAZ n_effective>=5 (pole
    'valid_population' w per_genome, NIE 'ci95_valid' - patrz
    docs/VALIDITY_REPORT.md). Rekonstrukcja tego progu tutaj z surowych
    pol bylaby DOKLADNIE tym bledem, ktoremu ma zapobiegac "zero nowych
    obliczen" - wiec czyta juz-policzone pole 'classification' wprost,
    zamiast zgadywac prog z ci95_valid."""
    if c["status"] != "measured":
        return "insufficient"
    if c.get("classification") == "GENOME-ROBUST":
        return "valid"
    if c.get("classification") == "GENOME-FRAGILE":
        return "degenerate"
    # Fallback dla danych bez pola "classification" (np. archiwalny profil
    # v0.10 z reports/academy/*.json, gdzie ci95_valid per genom BYL
    # jedynym dostepnym sygnalem, bez osobnego progu n_effective).
    genome_keys = list(c["genomes"].keys())
    all_valid = bool(genome_keys) and all(
        c["genomes"][g].get("ci95_valid") is True for g in genome_keys
    )
    return "valid" if all_valid else "degenerate"


def _all_genome_names(concepts: List[Dict[str, Any]]) -> List[str]:
    """Lista genomow odkrywana z samych danych (union przez wszystkie
    koncepty) - NIE zakodowana na sztywno. Homeostatic Resilience ma tylko
    14/23 genomow (cenzurowanie) - union daje pelne 23, karty genomow
    nieobecnych w danym koncepcie po prostu go pomijaja (patrz _genome_card)."""
    names = set()
    for c in concepts:
        names.update(c.get("genomes", {}).keys())
    return sorted(names)


def _genome_card(genome: str, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ten sam zestaw pojec, widziany z perspektywy jednego genomu."""
    card = []
    for c in concepts:
        entry = {
            "concept": c["concept"],
            "status": c["status"],
            "source_lesson": c["source_lesson"],
        }
        if c["status"] == "measured" and genome in c["genomes"]:
            entry.update(c["genomes"][genome])
        card.append(entry)
    return card


def build_competency_profile(population_path: Optional[Path] = None) -> Dict[str, Any]:
    """population_path (SPRINT v0.11.0 P2 KROK 2, CTO 2026-07-27): domyslnie
    None -> build_capability_profile_from_population() czyta swoj wlasny
    domyslny POPULATION_PATH (prawdziwy artefakt repo, bez zmiany
    zachowania). Jawny override istnieje, zeby run_post_run_artifacts()
    (execution_package_v0_11/runners/pipeline.py) i testy mogly wskazac
    DOKLADNIE ten plik population_validation, ktory wlasnie zapisal etap 1
    - inaczej profil czytalby cicho z INNEGO (domyslnego) pliku niz ten,
    ktory faktycznie przekazano na wejsciu, co jest dokladnie tym rodzajem
    rozjazdu, ktory caly ten sprint (P2) ma wyeliminowac."""
    concepts = build_capability_profile_from_population(
        population_path=population_path or POPULATION_PATH
    )
    states = {c["concept"]: _concept_validity_state(c) for c in concepts}

    valid_concepts = [c for c in concepts if states[c["concept"]] == "valid"]
    degenerate_concepts = [c for c in concepts if states[c["concept"]] == "degenerate"]
    insufficient_concepts = [c for c in concepts if states[c["concept"]] == "insufficient"]

    # SPRINT v0.11.0 P0 (CTO 2026-07-22): profil MINIMALNY na statusie
    # konfirmacyjnym VALIDATED, nie na ci95_valid - patrz docstring modulu.
    validated_concepts = [c for c in concepts if c.get("confirmatory_status") == "VALIDATED"]
    validated_cognitive = [c for c in validated_concepts if c.get("kind") == "cognitive"]
    validated_physiological = [c for c in validated_concepts if c.get("kind") == "physiological_state"]

    measured = sum(1 for c in concepts if c["status"] == "measured")
    total = len(concepts)

    return {
        "generated_at": datetime.now().isoformat(),
        "dataset_status": (
            "CONFIRMATORY (NIE Exploratory) - re-run konfirmacyjny 12765 przebiegow "
            "(23 genomy x n=185/93/92 wg experiment_manifest.json), Hard-Halt PASS "
            f"caly bieg, zakonczony 2026-07-20. Zrodlo: {POPULATION_PATH}. Statusy "
            "per pojecie (VALIDATED/EXPERIMENTAL) z docs/METRIC_STATUS_TABLE.md po "
            "korekcie Red Teamu (2026-07-20). Ten profil ZASTEPUJE Exploratory "
            "Dataset v0.10 (n=10, 2 genomy) jako zywy artefakt - archiwum "
            f"zachowane, nietkniete, w {ARCHIVE_JSON_NAME}."
        ),
        "summary": {
            "total_concepts": total,
            "measured": measured,
            "insufficient_data": total - measured,
            "valid_ci95": len(valid_concepts),
            "degenerate": len(degenerate_concepts),
            "validated": len(validated_concepts),
        },
        "minimal_profile": {
            "description": (
                "Oficjalny profil kompetencji - WYLACZNIE pojecia ze statusem "
                "konfirmacyjnym VALIDATED (docs/METRIC_STATUS_TABLE.md: przetrwaly "
                "Welch-pary+FDR ORAZ/LUB Kruskal-Wallis, leave-one-out, Red Team). "
                "UWAGA: ci95_valid=True ('ROBUST', pomiar wiarygodny) NIE oznacza "
                "VALIDATED ('dyskryminuje genomy', potwierdzone konfirmacyjnie) - "
                "to dwa rozne pytania, patrz docs/VALIDITY_REPORT.md 'Kluczowe "
                "odkrycie'. Przyklad: Pattern Retention jest 100% ci95-valid, ale "
                "tylko EXPERIMENTAL - nie wchodzi tutaj."
            ),
            "axes": [c["concept"] for c in validated_concepts],
            "cognitive_axes": [c["concept"] for c in validated_cognitive],
            "physiological_state_variables": [c["concept"] for c in validated_physiological],
            "cognitive_vs_physiological_note": (
                f"{len(validated_cognitive)} osi poznawczych VALIDATED + "
                f"{len(validated_physiological)} zmienna(ych) stanu fizjologicznego "
                "VALIDATED. Zmienna stanu fizjologicznego mierzy STAN systemu "
                "(np. poziom energii), NIE jego zdolnosc do czegokolwiek - nie "
                "sumowac z osiami poznawczymi jako rownowazne wpisy 'kompetencji'."
            ),
            "concepts": validated_concepts,
        },
        "full_profile": {
            "description": (
                "Wszystkie pojecia z ontologii, w tym zdegenerowane i "
                "insufficient_data - jawnie oznaczone, nie ukryte. 'valid'/"
                "'degenerate' ponizej to WYLACZNIE ci95_valid (wiarygodnosc "
                "pomiaru per genom) - NIEZALEZNE od confirmatory_status "
                "(VALIDATED/EXPERIMENTAL), ktory jest polem na kazdym koncepcie."
            ),
            "valid": valid_concepts,
            "degenerate": degenerate_concepts,
            "insufficient_data": insufficient_concepts,
        },
        "concepts": concepts,
        "genome_cards": {genome: _genome_card(genome, concepts) for genome in _all_genome_names(concepts)},
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _fdr_pairs_str(comparison: Optional[Dict[str, Any]]) -> str:
    if not comparison or comparison.get("n_fdr_significant_q_0_05") is None or not comparison.get("n_pairs"):
        return "-"
    return f"{comparison['n_fdr_significant_q_0_05']}/{comparison['n_pairs']}"


def _concept_row(c: Dict[str, Any]) -> str:
    comparison = c.get("genome_comparison") or {}
    return (
        "| {concept} | {status} | {conf} | {lesson} | {classification} | {valid_rate} | "
        "{n_valid}/{n_total} | {pairs} | {anova_f} |".format(
            concept=c["concept"],
            status=c["status"],
            conf=c.get("confirmatory_status") or "-",
            lesson=_fmt(c.get("source_lesson")),
            classification=c.get("classification") or "-",
            valid_rate=_fmt(c.get("valid_rate")),
            n_valid=_fmt(c.get("n_genomes_valid")),
            n_total=_fmt(c.get("n_genomes_total")),
            pairs=_fdr_pairs_str(comparison),
            anova_f=_fmt(comparison.get("anova_f")),
        )
    )


_CONCEPT_TABLE_HEADER = [
    "| Concept | Status | Confirmatory | Source (lekcja/środowisko) | Classification | "
    "valid_rate | n_valid/n_total | FDR pary | ANOVA f (surowe) |",
    "|---|---|---|---|---|---|---|---|---|",
]


def _secondary_observations_lines(concepts: List[Dict[str, Any]]) -> List[str]:
    """Zachowane dla zgodnosci ksztaltu - profil konfirmacyjny nie ma
    obecnie zadnych secondary_observations (pole zawsze [] w
    analyze_concept_from_population), wiec ta sekcja bedzie pusta, dopoki
    ktos nie doda mappingu z pool=False do POPULATION_METRIC_MAP."""
    with_secondary = [c for c in concepts if c.get("secondary_observations")]
    if not with_secondary:
        return []

    lines = [
        "",
        "## Obserwacje dodatkowe (nie wliczone do puli CI95)",
        "",
        "| Concept | Lekcja | Genom | value | ci95_valid | deterministic | n | note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in with_secondary:
        for obs in c["secondary_observations"]:
            for genome, stats in obs["genomes"].items():
                lines.append(
                    "| {concept} | {lesson} | {genome} | {value} | {valid} | {det} | {n} | {note} |".format(
                        concept=c["concept"], lesson=obs["lesson"], genome=genome,
                        value=_fmt(stats.get("value")), valid=_fmt(stats.get("ci95_valid")),
                        det=_fmt(stats.get("deterministic")), n=_fmt(stats.get("n")),
                        note=obs.get("note", "").split(" - ")[0],
                    )
                )
    return lines


def render_markdown(profile: Dict[str, Any]) -> str:
    summary = profile["summary"]
    minimal = profile["minimal_profile"]
    full = profile["full_profile"]

    lines = [
        "# CLOS Competency Profile",
        "",
        profile["dataset_status"],
        "",
        f"Profil minimalny (VALIDATED): {summary['validated']} osi / {summary['total_concepts']} pojec",
        f"Measured: {summary['measured']}/{summary['total_concepts']}",
        f"Insufficient data: {summary['insufficient_data']}/{summary['total_concepts']}",
        f"ci95_valid (ROBUST, wszystkie obecne genomy): {summary['valid_ci95']}/{summary['total_concepts']}",
        f"Generated at: {profile['generated_at']}",
        "",
        "Definicje pojec: [cognitive_ontology.md](../clos_academy/cognitive_ontology.md). "
        "Statusy konfirmacyjne: [METRIC_STATUS_TABLE.md](../docs/METRIC_STATUS_TABLE.md).",
        "",
        "## Profil minimalny (oficjalny, VALIDATED)",
        "",
        minimal["description"],
        "",
        minimal["cognitive_vs_physiological_note"],
        "",
        "Osie poznawcze: " + (", ".join(minimal["cognitive_axes"]) if minimal["cognitive_axes"] else "(brak)"),
        "",
        "Zmienne stanu fizjologicznego: " + (", ".join(minimal["physiological_state_variables"]) if minimal["physiological_state_variables"] else "(brak)"),
        "",
    ] + _CONCEPT_TABLE_HEADER + [_concept_row(c) for c in minimal["concepts"]] + [
        "",
        "## Profil pelny (wszystkie pojecia, luki jawne)",
        "",
        full["description"],
        "",
        f"### ci95_valid = True dla wszystkich obecnych genomow, tzw. ROBUST ({len(full['valid'])})",
        "",
    ] + _CONCEPT_TABLE_HEADER + [_concept_row(c) for c in full["valid"]] + [
        "",
        f"### Zdegenerowane, tzw. FRAGILE ({len(full['degenerate'])}) - zmierzone, ale co najmniej "
        "jeden genom bez wiarygodnej wariancji",
        "",
    ] + _CONCEPT_TABLE_HEADER + [_concept_row(c) for c in full["degenerate"]] + [
        "",
        f"### Insufficient data ({len(full['insufficient_data'])}) - brak lekcji/mechanizmu",
        "",
    ] + _CONCEPT_TABLE_HEADER + [_concept_row(c) for c in full["insufficient_data"]]

    lines += _secondary_observations_lines(profile["concepts"])
    lines += ["", "## Karty genomow (23 genomy: default/highly_plastic/minimal + pop_000..pop_019)"]

    genome_names = sorted(profile["genome_cards"].keys())
    for genome in genome_names:
        lines += [
            "",
            f"### {genome}",
            "",
            "| Concept | Status | Source | value | ci95_low | ci95_high | "
            "n | n_effective | ci95_valid |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for entry in profile["genome_cards"][genome]:
            lines.append(
                "| {concept} | {status} | {lesson} | {value} | {lo} | {hi} | "
                "{n} | {neff} | {valid} |".format(
                    concept=entry["concept"],
                    status=entry["status"],
                    lesson=_fmt(entry["source_lesson"]),
                    value=_fmt(entry.get("value")),
                    lo=_fmt(entry.get("ci95_low")),
                    hi=_fmt(entry.get("ci95_high")),
                    n=_fmt(entry.get("n")),
                    neff=_fmt(entry.get("n_effective")),
                    valid=_fmt(entry.get("ci95_valid")),
                )
            )

    lines.append("")
    return "\n".join(lines)


def archive_exploratory_profile(output_dir: Path = OUTPUT_DIR) -> Optional[Dict[str, Path]]:
    """SPRINT v0.11.0 P0 (CTO 2026-07-22): przed pierwszym nadpisaniem
    zywego competency_profile.json/.md danymi konfirmacyjnymi, zachowuje
    OBECNA (Exploratory v0.10.1, n=10) zawartosc pod osobna, jawnie
    nazwana sciezka - NIGDY nie nadpisuje w miejscu, dokladnie tak jak
    population_validation_v0_10_1.json zostal obok v0_11_0. Idempotentne:
    jesli archiwum juz istnieje ALBO zywy plik jest juz CONFIRMATORY (nie
    Exploratory), nic nie robi - nie ma czego archiwizowac ponownie."""
    json_path = output_dir / "competency_profile.json"
    archive_json = output_dir / ARCHIVE_JSON_NAME
    archive_md = output_dir / ARCHIVE_MD_NAME

    if archive_json.exists():
        return None
    if not json_path.exists():
        return None

    with open(json_path, encoding="utf-8") as f:
        current = json.load(f)
    if not str(current.get("dataset_status", "")).startswith("Exploratory"):
        return None

    shutil.copy2(json_path, archive_json)
    md_path = output_dir / "competency_profile.md"
    if md_path.exists():
        shutil.copy2(md_path, archive_md)
    return {"json": archive_json, "md": archive_md}


def write_competency_profile(
    output_dir: Path = OUTPUT_DIR, population_path: Optional[Path] = None
) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_exploratory_profile(output_dir)

    profile = build_competency_profile(population_path=population_path)

    json_path = output_dir / "competency_profile.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    md_path = output_dir / "competency_profile.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(profile))

    return {"json": json_path, "md": md_path}


if __name__ == "__main__":
    paths = write_competency_profile()
    print(f"Competency Profile: {paths['json']}, {paths['md']}")
