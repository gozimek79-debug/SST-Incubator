"""Validate Artifacts - sprawdza spojnosc raportow Academy z definicja eksperymentu.

Zasady (SPRINT_v0.8.4.md, Priorytet 3; wyjatek cenzurowania: SPRINT_v0.9.md P5,
Odkrycie #2):
  1. Raport scenariusza stochastycznego (kazdy poza clos_world.scenarios
     CONTROL_ENVIRONMENTS, np. noise_world) NIE moze miec ci95_valid=False
     dla statystyk eksperymentalnych danego genomu - to sygnalizowaloby
     pseudoreplikacje albo brak realnej wariancji tam, gdzie powinna byc.
     WYJATEK: ci95_valid=False jest DOZWOLONE, jesli raport jawnie deklaruje
     cenzurowanie (per_genome[genom]["recovery_time_detail"] z polami
     n_total/n_censored/min_non_censored) I liczba NIEUCENZUROWANYCH
     (n_total - n_censored) faktycznie jest < min_non_censored - to jest
     prerejestrowany, zweryfikowany wynik (np. L1.2 - homeostaza nigdy nie
     wraca w oknie obserwacji), nie pseudoreplikacja. Walidator SPRAWDZA te
     liczby, nie ufa samej obecnosci pola - nie da sie tym wyjatkiem obejsc
     ochrony bez faktycznego niedoboru nieucenzurowanych prob.
  2. Raport musi zgadzac sie z prerejestracja lekcji (ten sam scenario,
     ten sam control_baseline, liczba seedow >= min_seeds).

Skanuje reports/academy/*.json (struktura zapisywana przez lekcje Academy,
patrz clos_academy/lesson_L1_1.py). Kazdemu raportowi odpowiada
publications/preregistration_<lesson_id>.json (kropki -> podkreslenia).

Uzycie:
    python scripts/validate_artifacts.py
Kod wyjscia: 0 = brak rozjazdu, 1 = znaleziono niespojnosc.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clos_world.scenarios import is_control

REPORTS_DIR = Path("reports/academy")
PUBLICATIONS_DIR = Path("publications")


def _prereg_path_for_lesson(lesson_id: str) -> Path:
    return PUBLICATIONS_DIR / f"preregistration_{lesson_id.replace('.', '_')}.json"


def _censoring_justifies_invalid_ci95(genome_stats: dict) -> bool:
    """True tylko jesli raport dowodzi (liczbami, nie samym polem), ze
    ci95_valid=False wynika z niedoboru nieucenzurowanych prob ponizej
    zadeklarowanego min_non_censored - a nie z czegos innego."""
    detail = genome_stats.get("recovery_time_detail")
    if not isinstance(detail, dict):
        return False
    n_total = detail.get("n_total")
    n_censored = detail.get("n_censored")
    min_non_censored = detail.get("min_non_censored")
    if not all(isinstance(v, int) for v in (n_total, n_censored, min_non_censored)):
        return False
    non_censored = n_total - n_censored
    return non_censored < min_non_censored


def validate_report(report_path: Path) -> list:
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    lesson = report.get("lesson")
    scenario = report.get("scenario")
    control_baseline = report.get("control_baseline")
    per_genome = report.get("per_genome", {})

    if not lesson or not scenario:
        return [f"{report_path}: brak wymaganych pol 'lesson'/'scenario' w raporcie"]

    errors = []

    # 1) ci95_valid nie moze byc False dla scenariusza stochastycznego.
    if is_control(scenario):
        errors.append(
            f"{report_path}: scenario '{scenario}' jest scenariuszem kontrolnym "
            "(is_control=True), oczekiwano stochastycznego scenariusza jako "
            "glownego eksperymentu"
        )
    else:
        for genome, stats in per_genome.items():
            exp_stats = stats.get("experimental_stats", {})
            if exp_stats.get("ci95_valid") is False:
                if _censoring_justifies_invalid_ci95(stats):
                    continue  # sankcjonowany wyjatek: cenzurowanie ponizej min_non_censored
                errors.append(
                    f"{report_path}: genom '{genome}', scenariusz stochastyczny "
                    f"'{scenario}' ma ci95_valid=False (n_effective="
                    f"{exp_stats.get('n_effective')}) - blad, oczekiwana "
                    "wariancja miedzyseedowa (brak uzasadnienia cenzurowaniem "
                    "w recovery_time_detail)"
                )

    # 2) zgodnosc z prerejestracja.
    prereg_path = _prereg_path_for_lesson(lesson)
    if not prereg_path.exists():
        errors.append(f"{report_path}: brak prerejestracji {prereg_path} dla lekcji '{lesson}'")
        return errors

    with open(prereg_path, encoding="utf-8") as f:
        prereg = json.load(f)

    design = prereg.get("experiment_design", {})
    prereg_scenario = design.get("scenario")
    if prereg_scenario != scenario:
        errors.append(
            f"{report_path}: scenario w raporcie ('{scenario}') != "
            f"prerejestracja ('{prereg_scenario}')"
        )

    prereg_control = design.get("control_baseline", {})
    prereg_control_scenario = (
        prereg_control.get("scenario") if isinstance(prereg_control, dict) else prereg_control
    )
    if control_baseline and prereg_control_scenario and control_baseline != prereg_control_scenario:
        errors.append(
            f"{report_path}: control_baseline ('{control_baseline}') != "
            f"prerejestracja ('{prereg_control_scenario}')"
        )

    min_seeds = design.get("min_seeds") or len(design.get("seeds", []))
    for genome, stats in per_genome.items():
        n = stats.get("experimental_stats", {}).get("n")
        if n is not None and min_seeds and n < min_seeds:
            errors.append(
                f"{report_path}: genom '{genome}' ma n={n} seedow < "
                f"min_seeds={min_seeds} z prerejestracji"
            )

    return errors


def main() -> int:
    if not REPORTS_DIR.exists():
        print(f"OK: brak katalogu {REPORTS_DIR} - nic do walidacji")
        return 0

    report_files = sorted(REPORTS_DIR.glob("*.json"))
    all_errors = []
    for report_path in report_files:
        all_errors.extend(validate_report(report_path))

    if all_errors:
        print(f"VALIDATE_ARTIFACTS: {len(all_errors)} problem(ow) w {len(report_files)} raportach")
        for e in all_errors:
            print(f"  FAIL: {e}")
        return 1

    print(f"VALIDATE_ARTIFACTS: OK ({len(report_files)} raportow sprawdzonych)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
