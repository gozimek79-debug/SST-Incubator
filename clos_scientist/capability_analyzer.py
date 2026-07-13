"""Capability Analyzer - mapuje endpointy lekcji Academy na pojecia z
clos_academy/cognitive_ontology.md.

Zasady (SPRINT_v0.8.4.md, Priorytet 4; relacja N:M: SPRINT_v0.9.md P6,
Odkrycie #1 opcja 2):
  - Czyta reports/academy/*.json oraz odpowiadajace prerejestracje
    (publications/preregistration_<lesson_id>.json) - scenariusz do
    porownania brany jest z prerejestracji, nie hardkodowany.
  - CONCEPT_METRIC_MAP mapuje pojecie -> LISTA lekcji (N:M: jedno pojecie
    moze byc zasilane przez wiele lekcji, jedna lekcja moze zasilac wiele
    pojec). Wartosci z wielu lekcji dla tego samego genomu sa laczone w
    jedna pule przed policzeniem CI95 - to jest agregacja replik, nie
    wybor "lepszej" lekcji. WYJATEK: mapping z "pool": False (patrz nizej).
  - REGULA AGREGACJI, gdy jeden mapping ma "pool": False (SPRINT_v0.10.md
    P4, przypadek Adaptation): wartosc NIE wchodzi do wspolnej puli
    genome_values / oficjalnego CI95 pojecia. Zamiast tego trafia do
    osobnego pola "secondary_observations" (lista, per lekcja: lesson,
    pooled=False, note, per-genom CI95/deterministic policzone OSOBNO).
    Powod: pooling zaklada, ze wartosci z roznych lekcji sa NIEZALEZNYMI
    REPLIKAMI TEGO SAMEGO zjawiska. Gdy zrodlo jest metryka strukturalnie
    stala z powodu konstrukcji sceny (nie realnym pomiarem tego pojecia w
    tamtej lekcji), wrzucenie jej do puli po cichu obnizylby wariancje i
    zafalszowal CI95 pojecia bez ostrzezenia - stad jawna flaga "pool" w
    CONCEPT_METRIC_MAP zamiast automatycznej heurystyki (decyzja ma byc
    czytelna w kodzie, nie zgadywana w locie z danych).
  - Kazde pojecie z CONCEPT_METRIC_MAP uzywa DOKLADNIE tej samej nazwy co
    naglowek w cognitive_ontology.md.
  - Pojecie bez zadnej lekcji (mappings=None) dostaje status
    "insufficient_data" i ZERO wartosci liczbowych (pusty "genomes",
    "genome_comparison": None). Pojecie z lekcja(-ami), ale bez zadnego
    dopasowanego raportu/wartosci, dostaje to samo - z intencja zachowana
    w source_lesson (jakiej lekcji brakuje), nie zgadywana.
  - extract() moze zwrocic None (np. run ucenzurowany) - filtrowane przed
    CI95, NIE liczone jako 0.0 ani pomijane cicho z calego runu.
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

# Mapowanie pojecie -> LISTA {lesson, extract, pool?, note?} (N:M, patrz
# docstring modulu). None = pojecie bez zadnej lekcji (zgodnie z
# cognitive_ontology.md). "pool" domyslnie True (wartosci wchodza do
# wspolnej puli CI95 pojecia); "pool": False = wartosc widoczna tylko w
# "secondary_observations", NIGDY nie miesza sie z oficjalna wartoscia.
#
# Adaptation (SPRINT_v0.10.md P4): L1.2 rowniez ma teraz realne snapshoty
# (v0.10 P3), ale jej adaptation_tick jest STALA (=10) dla wszystkich 10
# seedow, obu genomow - to NIE jest degeneracja adaptacji do szoku, tylko
# strukturalny artefakt konstrukcji L1.2: t_shock zawsze >= 20 (patrz
# _shock_tick() w lesson_L1_2.py), a detect_phases()._find_chaos_end()
# sprawdza pierwsze okno od tick=10 - zawsze PRZED szokiem, gdzie entropia
# narasta identycznym, gladkim rampem niezaleznie od seeda/genomu (zaden
# genom-specyficzny/szokowy sygnal jeszcze tam nie dotarl). Innymi slowy:
# L1.2 adaptation_tick mierzy "kiedy stabilizuje sie baseline PRZED
# szokiem", nie "adaptacje DO szoku" - inne zjawisko niz L1.1's
# adaptation_tick (tick stabilizacji PO usunieciu bodzca). Polaczenie ich w
# jedna pule zafalszowaloby CI95 (mieszaloby dwa rozne zjawiska pod jedna
# nazwa metryki) - stad "pool": False. Zobacz RAPORT_v0.10.md i
# clos_academy/cognitive_ontology.md#Adaptation.
CONCEPT_METRIC_MAP = {
    "Perception": None,
    "Attention": None,
    "Pattern Recognition": [
        {"lesson": "L1.1", "extract": lambda r: r["mse_stimulus_phase"]},
    ],
    "Pattern Retention": [
        {"lesson": "L1.1", "extract": lambda r: r["memory_decay_rate"]},
    ],
    "Working Memory": [
        {"lesson": "L1.1", "extract": lambda r: r["primary_endpoint"]["value"]},
    ],
    "Long-term Memory": None,
    "Prediction": None,
    "Adaptation": [
        {"lesson": "L1.1", "extract": lambda r: r["adaptation_tick"]},
        {
            "lesson": "L1.2", "extract": lambda r: r["adaptation_tick"], "pool": False,
            "note": (
                "L1.2 adaptation_tick jest stala (=10, wszystkie seedy/genomy): "
                "mierzy stabilizacje entropii w oknie PRZED szokiem (t_shock zawsze "
                ">=20), nie adaptacje DO szoku. Nie laczona z pula L1.1 - inne "
                "zjawisko pod ta sama nazwa metryki. Patrz RAPORT_v0.10.md."
            ),
        },
    ],
    "Exploration": None,
    "Generalization": None,
    "Planning": None,
    "Stability": [
        {"lesson": "L1.1", "extract": lambda r: r["stability_score"]},
        # L1.2 stability_score jest teraz tez ci95_valid (v0.10 P3), ale NIE jest
        # tu dolaczona jako pool=True: L1.1 (pattern echo, stymulacja+cisza) i
        # L1.2 (shock recovery, jednorazowa perturbacja) to rozne konteksty
        # zadaniowe - czy sa wspolmierne jako "repliki" ogolnej stabilnosci
        # genomu, czy nie, to osobna decyzja naukowa, swiadomie odlozona poza
        # zakres P4 (SPRINT_v0.10.md p.2 pytal wprost tylko o Adaptation).
    ],
    "Energy Efficiency": [
        {"lesson": "L1.1", "extract": lambda r: r["final_energy"]},
    ],
    "Homeostatic Resilience": [
        # None dla runow ucenzurowanych (recovery_time niezdefiniowany w oknie W) -
        # filtrowane przez analyze_concept(), nie liczone jako 0.
        {"lesson": "L1.2", "extract": lambda r: r["primary_endpoint"]["value"]},
    ],
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


def _insufficient(concept: str, source_lessons: List[str],
                   secondary_observations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    return {
        "concept": concept,
        "status": "insufficient_data",
        "source_lesson": ", ".join(source_lessons) if source_lessons else None,
        "source_lessons": list(source_lessons),
        "genomes": {},
        "genome_comparison": None,
        "secondary_observations": secondary_observations or [],
    }


def _genome_stats(values: List[float]) -> Dict[str, Any]:
    stats = compute_ci95(values)
    return {
        "value": stats["mean"],
        "std": stats["std"],
        "ci95_low": stats["ci95_low"],
        "ci95_high": stats["ci95_high"],
        "n": stats["n"],
        "n_effective": stats["n_effective"],
        "ci95_valid": stats["ci95_valid"],
        "deterministic": stats["deterministic"],
    }


def analyze_concept(concept: str, mappings: Optional[List[Dict[str, Any]]],
                     reports: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if not mappings:
        return _insufficient(concept, [])

    intended_lessons = [m["lesson"] for m in mappings]
    pooled_lessons: List[str] = []
    secondary_observations: List[Dict[str, Any]] = []
    genome_values: Dict[str, List[float]] = {g: [] for g in GENOMES}
    any_data_found = False

    for mapping in mappings:
        lesson_id = mapping["lesson"]
        report = reports.get(lesson_id)
        if report is None:
            continue

        prereg = _load_json(_prereg_path_for_lesson(lesson_id))
        scenario = (
            prereg.get("experiment_design", {}).get("scenario")
            if prereg else report.get("scenario")
        )

        extract = mapping["extract"]
        lesson_genome_values: Dict[str, List[float]] = {}
        for genome in GENOMES:
            raw_values = [
                extract(r) for r in report.get("results", [])
                if r.get("genome") == genome and r.get("scenario") == scenario
            ]
            lesson_genome_values[genome] = [v for v in raw_values if v is not None]

        if not any(lesson_genome_values.values()):
            continue
        any_data_found = True

        if mapping.get("pool", True):
            pooled_lessons.append(lesson_id)
            for genome, values in lesson_genome_values.items():
                genome_values[genome].extend(values)
        else:
            genome_stats = {
                genome: _genome_stats(values)
                for genome, values in lesson_genome_values.items() if values
            }
            secondary_observations.append({
                "lesson": lesson_id,
                "pooled": False,
                "note": mapping.get("note", ""),
                "genomes": genome_stats,
            })

    if not any_data_found:
        return _insufficient(concept, intended_lessons, secondary_observations)

    if not pooled_lessons:
        # Wylacznie sekundarne (nie-pooled) obserwacje - brak oficjalnej wartosci.
        return _insufficient(concept, intended_lessons, secondary_observations)

    genomes_out: Dict[str, Any] = {}
    for genome, values in genome_values.items():
        if not values:
            continue
        genomes_out[genome] = _genome_stats(values)

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
        "source_lesson": ", ".join(pooled_lessons),
        "source_lessons": pooled_lessons,
        "genomes": genomes_out,
        "genome_comparison": comparison,
        "secondary_observations": secondary_observations,
    }


def build_capability_profile(reports_dir: Path = REPORTS_DIR) -> List[Dict[str, Any]]:
    """Zwraca liste rekordow (jeden na pojecie z CONCEPT_METRIC_MAP)."""
    reports = load_academy_reports(reports_dir)
    return [analyze_concept(concept, mappings, reports)
            for concept, mappings in CONCEPT_METRIC_MAP.items()]


if __name__ == "__main__":
    profile = build_capability_profile()
    print(json.dumps(profile, indent=2, ensure_ascii=False))
