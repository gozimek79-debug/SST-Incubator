"""Capability Analyzer - mapuje endpointy lekcji Academy na pojecia z
clos_academy/cognitive_ontology.md.

Zasady (SPRINT_v0.8.4.md, Priorytet 4):
  - Czyta reports/academy/*.json oraz odpowiadajaca prerejestracje
    (publications/preregistration_<lesson_id>.json) - scenariusz do
    porownania brany jest z prerejestracji, nie hardkodowany.
  - Kazde pojecie z CONCEPT_METRIC_MAP uzywa DOKLADNIE tej samej nazwy co
    naglowek w cognitive_ontology.md.
  - Pojecie bez lekcji (albo lekcja z ontologii jeszcze nie istnieje w
    reports/academy/) dostaje status "insufficient_data" i ZERO wartosci
    liczbowych (pusty "genomes", "genome_comparison": None).
  - Porownanie genomow liczy Cohen's d MIEDZY GENOMAMI (nie Glass's delta
    wzgledem kontroli - to inne porownanie, uzywane w samej lekcji).
  - Zero interpretacji/ocen slownych w wyjsciu - tylko liczby i status.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from clos_curriculum.laboratory.statistics import compute_ci95

REPORTS_DIR = Path("reports/academy")
PUBLICATIONS_DIR = Path("publications")

GENOMES = ["default", "highly_plastic"]

# Mapowanie pojecie -> lekcja + ekstraktor wartosci z pojedynczego run-dicta
# (patrz clos_academy/lesson_L1_1.py:run_pattern_echo -> output).
# None = pojecie bez zadnej lekcji (zgodnie z cognitive_ontology.md).
CONCEPT_METRIC_MAP = {
    "Perception": None,
    "Attention": None,
    "Pattern Recognition": {"lesson": "L1.1", "extract": lambda r: r["mse_stimulus_phase"]},
    "Pattern Retention": {"lesson": "L1.1", "extract": lambda r: r["memory_decay_rate"]},
    "Working Memory": {"lesson": "L1.1", "extract": lambda r: r["primary_endpoint"]["value"]},
    "Long-term Memory": None,
    "Prediction": None,
    "Adaptation": {"lesson": "L1.1", "extract": lambda r: r["adaptation_tick"]},
    "Exploration": None,
    "Generalization": None,
    "Planning": None,
    "Stability": {"lesson": "L1.1", "extract": lambda r: r["stability_score"]},
    "Energy Efficiency": {"lesson": "L1.1", "extract": lambda r: r["final_energy"]},
}


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _prereg_path_for_lesson(lesson_id: str) -> Path:
    return PUBLICATIONS_DIR / f"preregistration_{lesson_id.replace('.', '_')}.json"


def load_academy_reports(reports_dir: Path = REPORTS_DIR) -> Dict[str, Dict[str, Any]]:
    """Wczytuje reports/academy/*.json, indeksowane po polu 'lesson'."""
    reports: Dict[str, Dict[str, Any]] = {}
    if not reports_dir.exists():
        return reports
    for path in sorted(reports_dir.glob("*.json")):
        report = _load_json(path)
        lesson = report.get("lesson") if report else None
        if lesson:
            reports[lesson] = report
    return reports


def _cohens_d_with_flag(group_a: List[float], group_b: List[float]) -> Dict[str, Any]:
    """Cohen's d z jawna flaga 'computable' (statistics.cohens_d zwraca 0.0
    zarowno dla 'nieobliczalne', jak i dla realnego zerowego efektu -
    tutaj to rozroznienie jest jawne)."""
    if len(group_a) < 2 or len(group_b) < 2:
        return {"cohens_d": None, "computable": False}
    mean_a = sum(group_a) / len(group_a)
    mean_b = sum(group_b) / len(group_b)
    var_a = sum((v - mean_a) ** 2 for v in group_a) / (len(group_a) - 1)
    var_b = sum((v - mean_b) ** 2 for v in group_b) / (len(group_b) - 1)
    pooled_std = math.sqrt((var_a + var_b) / 2)
    if pooled_std < 1e-9:
        return {"cohens_d": None, "computable": False}
    return {"cohens_d": round((mean_b - mean_a) / pooled_std, 6), "computable": True}


def _insufficient(concept: str, source_lesson: Optional[str]) -> Dict[str, Any]:
    return {
        "concept": concept,
        "status": "insufficient_data",
        "source_lesson": source_lesson,
        "genomes": {},
        "genome_comparison": None,
    }


def analyze_concept(concept: str, mapping: Optional[Dict[str, Any]],
                     reports: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if mapping is None:
        return _insufficient(concept, None)

    lesson_id = mapping["lesson"]
    report = reports.get(lesson_id)
    if report is None:
        return _insufficient(concept, lesson_id)

    prereg = _load_json(_prereg_path_for_lesson(lesson_id))
    scenario = (
        prereg.get("experiment_design", {}).get("scenario")
        if prereg else report.get("scenario")
    )

    extract = mapping["extract"]
    genome_values: Dict[str, List[float]] = {}
    for genome in GENOMES:
        values = [
            extract(r) for r in report.get("results", [])
            if r.get("genome") == genome and r.get("scenario") == scenario
        ]
        genome_values[genome] = values

    if not any(genome_values.values()):
        return _insufficient(concept, lesson_id)

    genomes_out: Dict[str, Any] = {}
    for genome, values in genome_values.items():
        if not values:
            continue
        stats = compute_ci95(values)
        genomes_out[genome] = {
            "value": stats["mean"],
            "std": stats["std"],
            "ci95_low": stats["ci95_low"],
            "ci95_high": stats["ci95_high"],
            "n": stats["n"],
            "n_effective": stats["n_effective"],
            "ci95_valid": stats["ci95_valid"],
        }

    comparison = None
    if genome_values.get("default") and genome_values.get("highly_plastic"):
        a, b = genome_values["default"], genome_values["highly_plastic"]
        d = _cohens_d_with_flag(a, b)
        comparison = {
            "mean_diff": round((sum(b) / len(b)) - (sum(a) / len(a)), 6),
            "cohens_d": d["cohens_d"],
            "computable": d["computable"],
        }

    return {
        "concept": concept,
        "status": "measured",
        "source_lesson": lesson_id,
        "genomes": genomes_out,
        "genome_comparison": comparison,
    }


def build_capability_profile(reports_dir: Path = REPORTS_DIR) -> List[Dict[str, Any]]:
    """Zwraca liste rekordow (jeden na pojecie z CONCEPT_METRIC_MAP)."""
    reports = load_academy_reports(reports_dir)
    return [analyze_concept(concept, mapping, reports)
            for concept, mapping in CONCEPT_METRIC_MAP.items()]


if __name__ == "__main__":
    profile = build_capability_profile()
    print(json.dumps(profile, indent=2, ensure_ascii=False))
