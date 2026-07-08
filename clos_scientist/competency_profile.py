"""Competency Profile - formatuje wyjscie Capability Analyzer do
competency_profile.json / competency_profile.md + auto-karty genomow.

Zero nowych obliczen (SPRINT_v0.8.4.md, Priorytet 4.3): caly artefakt to
reformatowanie clos_scientist.capability_analyzer.build_capability_profile().
Pojecia insufficient_data MUSZA byc w profilu, jawnie oznaczone, bez zadnej
wartosci liczbowej. Zero ocen slownych/gwiazdek/poziomow - tylko liczby
i status.
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


def _genome_card(genome: str, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ten sam zestaw 13 pojec, widziany z perspektywy jednego genomu."""
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
    measured = sum(1 for c in concepts if c["status"] == "measured")
    total = len(concepts)

    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_concepts": total,
            "measured": measured,
            "insufficient_data": total - measured,
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


def render_markdown(profile: Dict[str, Any]) -> str:
    summary = profile["summary"]
    lines = [
        "# CLOS Competency Profile",
        "",
        f"Measured: {summary['measured']}/{summary['total_concepts']}",
        f"Insufficient data: {summary['insufficient_data']}/{summary['total_concepts']}",
        f"Generated at: {profile['generated_at']}",
        "",
        "Definicje pojec: [cognitive_ontology.md](../clos_academy/cognitive_ontology.md).",
        "",
        "## Pojecia",
        "",
        "| Concept | Status | Source lesson | default value | default n_eff | "
        "highly_plastic value | highly_plastic n_eff | mean_diff | cohens_d |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for c in profile["concepts"]:
        default_g = c["genomes"].get("default", {})
        plastic_g = c["genomes"].get("highly_plastic", {})
        comparison = c["genome_comparison"] or {}
        lines.append(
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
