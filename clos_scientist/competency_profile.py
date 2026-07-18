"""Competency Profile - formatuje wyjscie Capability Analyzer do
competency_profile.json / competency_profile.md + auto-karty genomow.

Zero nowych obliczen (SPRINT_v0.8.4.md, Priorytet 4.3): caly artefakt to
reformatowanie clos_scientist.capability_analyzer.build_capability_profile().
Pojecia insufficient_data MUSZA byc w profilu, jawnie oznaczone, bez zadnej
wartosci liczbowej. Zero ocen slownych/gwiazdek/poziomow - tylko liczby
i status.

Profil minimalny vs pelny (SPRINT_v0.9.md, Priorytet 6, Kroki 4-5):
  - MINIMALNY (oficjalny) = WYLACZNIE pojecia, dla ktorych WSZYSTKIE obecne
    genomy maja ci95_valid=True. To jest jedyny profil, na ktory mozna sie
    powolac jako "co system faktycznie mierzy wiarygodnie".
  - PELNY zachowuje WSZYSTKO: pojecia zmierzone ale zdegenerowane
    (ci95_valid=False dla wszystkich obecnych genomow, np. Adaptation/
    Stability z L1.1) oraz insufficient_data (brak lekcji) - jako osobne,
    jawnie oznaczone kategorie. Nic nie jest ukrywane, tylko rozdzielone.
  - Klasyfikacja (_concept_validity_state) MUSI byc zsynchronizowana z
    clos_studio/panel/panel.js:competencyRowState() - to samo pytanie
    zadane w dwoch miejscach (artefakt .md/.json i panel na zywo), musi
    dawac ta sama odpowiedz.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from clos_scientist.capability_analyzer import GENOMES, build_capability_profile

# publications/ (nie reports/academy/) - zeby nie kolidowac ze
# scripts/validate_artifacts.py, ktory oczekuje w reports/academy/ wylacznie
# raportow lekcji (pola 'lesson'/'scenario').
OUTPUT_DIR = Path("publications")


def _concept_validity_state(c: Dict[str, Any]) -> str:
    """valid / degenerate / insufficient. Zwierciadlo
    clos_studio/panel/panel.js:competencyRowState() - synchronizowac razem."""
    if c["status"] != "measured":
        return "insufficient"
    genome_keys = list(c["genomes"].keys())
    all_valid = bool(genome_keys) and all(
        c["genomes"][g].get("ci95_valid") is True for g in genome_keys
    )
    return "valid" if all_valid else "degenerate"


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


def build_competency_profile() -> Dict[str, Any]:
    concepts = build_capability_profile()
    states = {c["concept"]: _concept_validity_state(c) for c in concepts}

    valid_concepts = [c for c in concepts if states[c["concept"]] == "valid"]
    degenerate_concepts = [c for c in concepts if states[c["concept"]] == "degenerate"]
    insufficient_concepts = [c for c in concepts if states[c["concept"]] == "insufficient"]

    # SPRINT_v0.11.0.md P1 (decyzja CTO 2026-07-17): profil minimalny miesza
    # OSIE POZNAWCZE (kandydatow na/lub zmierzone zdolnosci poznawcze) ze
    # ZMIENNYMI STANU FIZJOLOGICZNEGO ("Final Energy Level", dawniej "Energy
    # Efficiency" - mierzy stan systemu, nie jego zdolnosc do czegokolwiek,
    # patrz clos_scientist/capability_analyzer.py:CONCEPT_KIND i
    # docs/ENERGY_EFFICIENCY_ONTOLOGY_DECISION.md). Rozroznienie musi byc
    # JAWNE w artefakcie - nie tylko w dokumentacji - zeby "7 osi" nigdy nie
    # bylo czytane jako "7 zdolnosci poznawczych".
    valid_cognitive = [c for c in valid_concepts if c.get("kind") == "cognitive"]
    valid_physiological = [c for c in valid_concepts if c.get("kind") == "physiological_state"]

    measured = sum(1 for c in concepts if c["status"] == "measured")
    total = len(concepts)

    return {
        "generated_at": datetime.now().isoformat(),
        "dataset_status": ("Exploratory Dataset v0.10 (SPRINT_v0.11.0.md P0) - profil oparty na n=10/genom "
                            "(2 genomy anchor: default, highly_plastic). Moc statystyczna wystarcza tylko dla "
                            "efektow bardzo duzych po korekcie. Nie poprawiane, nie wycofywane. Power/"
                            "Confirmatory validity: PENDING do re-run zatwierdzonego przez CTO. Patrz "
                            "publications/preregistration_v0_11_0_power_reproduction.json."),
        "summary": {
            "total_concepts": total,
            "measured": measured,
            "insufficient_data": total - measured,
            "valid_ci95": len(valid_concepts),
            "degenerate": len(degenerate_concepts),
        },
        "minimal_profile": {
            "description": (
                "Oficjalny profil kompetencji - WYLACZNIE pojecia, dla ktorych "
                "wszystkie obecne genomy maja ci95_valid=True. UWAGA: to NIE "
                "jest jednorodna lista zdolnosci poznawczych - patrz "
                "cognitive_axes vs physiological_state_variables ponizej."
            ),
            "axes": [c["concept"] for c in valid_concepts],
            "cognitive_axes": [c["concept"] for c in valid_cognitive],
            "physiological_state_variables": [c["concept"] for c in valid_physiological],
            "cognitive_vs_physiological_note": (
                f"{len(valid_cognitive)} osi poznawczych (zmierzonych zdolnosci lub "
                f"kandydatow na nie) + {len(valid_physiological)} zmienna(ych) stanu "
                "fizjologicznego. Zmienna stanu fizjologicznego mierzy STAN systemu "
                "(np. poziom energii), NIE jego zdolnosc do czegokolwiek - nie "
                "sumowac z osiami poznawczymi jako rownowazne wpisy 'kompetencji'."
            ),
            "concepts": valid_concepts,
        },
        "full_profile": {
            "description": (
                "Wszystkie pojecia z ontologii, w tym zdegenerowane i "
                "insufficient_data - jawnie oznaczone, nie ukryte."
            ),
            "valid": valid_concepts,
            "degenerate": degenerate_concepts,
            "insufficient_data": insufficient_concepts,
        },
        "concepts": concepts,
        "genome_cards": {genome: _genome_card(genome, concepts) for genome in GENOMES},
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _concept_row(c: Dict[str, Any]) -> str:
    default_g = c["genomes"].get("default", {})
    plastic_g = c["genomes"].get("highly_plastic", {})
    comparison = c["genome_comparison"] or {}
    return (
        "| {concept} | {status} | {lesson} | {dv} | {dn} | {pv} | {pn} | {md} | {cd} |".format(
            concept=c["concept"],
            status=c["status"],
            lesson=_fmt(c["source_lesson"]),
            dv=_fmt(default_g.get("value")),
            dn=_fmt(default_g.get("n_effective")),
            pv=_fmt(plastic_g.get("value")),
            pn=_fmt(plastic_g.get("n_effective")),
            md=_fmt(comparison.get("mean_diff")),
            cd=_fmt(comparison.get("cohens_d")),
        )
    )


_CONCEPT_TABLE_HEADER = [
    "| Concept | Status | Source lesson | default value | default n_eff | "
    "highly_plastic value | highly_plastic n_eff | mean_diff | cohens_d |",
    "|---|---|---|---|---|---|---|---|---|",
]


def _secondary_observations_lines(concepts: List[Dict[str, Any]]) -> List[str]:
    """SPRINT_v0.10.md P4: obserwacje z lekcji NIE wliczonych do puli CI95
    pojecia (mapping "pool": False) - musza byc widoczne, nie tylko w JSON."""
    with_secondary = [c for c in concepts if c.get("secondary_observations")]
    if not with_secondary:
        return []

    lines = [
        "",
        "## Obserwacje dodatkowe (nie wliczone do puli CI95)",
        "",
        "Wartosci z lekcji jawnie oznaczonych `\"pool\": False` w "
        "`CONCEPT_METRIC_MAP` (clos_scientist/capability_analyzer.py) - "
        "policzone osobno, NIGDY nie mieszane ze wartoscia oficjalna "
        "pojecia powyzej. Powod zawsze podany w `note`.",
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
        f"Profil minimalny: {summary['valid_ci95']} osi z waznym CI95 / {summary['total_concepts']} pojec",
        f"Measured: {summary['measured']}/{summary['total_concepts']}",
        f"Insufficient data: {summary['insufficient_data']}/{summary['total_concepts']}",
        f"Generated at: {profile['generated_at']}",
        "",
        "Definicje pojec: [cognitive_ontology.md](../clos_academy/cognitive_ontology.md).",
        "",
        "## Profil minimalny (oficjalny)",
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
        f"### Wazne (CI95, {len(full['valid'])})",
        "",
    ] + _CONCEPT_TABLE_HEADER + [_concept_row(c) for c in full["valid"]] + [
        "",
        f"### Zdegenerowane ({len(full['degenerate'])}) - zmierzone, ale bez wiarygodnej wariancji",
        "",
    ] + _CONCEPT_TABLE_HEADER + [_concept_row(c) for c in full["degenerate"]] + [
        "",
        f"### Insufficient data ({len(full['insufficient_data'])}) - brak lekcji/mechanizmu",
        "",
    ] + _CONCEPT_TABLE_HEADER + [_concept_row(c) for c in full["insufficient_data"]]

    lines += _secondary_observations_lines(profile["concepts"])
    lines += ["", "## Karty genomow"]

    for genome in GENOMES:
        lines += [
            "",
            f"### {genome}",
            "",
            "| Concept | Status | Source lesson | value | ci95_low | ci95_high | "
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


def write_competency_profile(output_dir: Path = OUTPUT_DIR) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = build_competency_profile()

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
