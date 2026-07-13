"""Validate Observability - warunek 5 CTO (SPRINT_v0.10.md P5).

Sprawdza reports/academy/*.json: kazdy run (results + baseline_results) musi
miec pole "snapshot_diagnostics" (patrz clos_scientist/telemetry.py,
uzupelniane przez clos_academy/lesson_L1_1.py i lesson_L1_2.py przy
generowaniu raportu) i musi ono byc CZYSTE - brak snapshotow, niekompletnosc
ponizej progu, niemonotoniczny timeline, dziura w sekwencji tickow lub
cofajace sie timestampy kazde z osobna blokuja scalenie (exit!=0).

To NIE re-uruchamia lekcji (szybki, statyczny walidator CI - ten sam wzorzec
co scripts/validate_artifacts.py/validate_publication.py) - czyta wylacznie
diagnostyke juz policzona i zapisana w raporcie.

Uzycie:
    python scripts/validate_observability.py
Kod wyjscia: 0 = wszystkie runy maja czysta telemetrie, 1 = znaleziono problem.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clos_scientist.telemetry import diagnostics_errors

REPORTS_DIR = Path("reports/academy")


def validate_report(report_path: Path) -> list:
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    lesson = report.get("lesson", report_path.stem)
    errors = []

    for group in ("results", "baseline_results"):
        for run in report.get(group, []):
            run_id = run.get("run_id", "?")
            label = f"{report_path.name}/{group}/{run_id}"
            diag = run.get("snapshot_diagnostics")
            if diag is None:
                errors.append(
                    f"{label}: brak pola 'snapshot_diagnostics' - telemetria "
                    "nigdy nie zostala zmierzona dla tego runu"
                )
                continue
            errors.extend(diagnostics_errors(diag, label=label))

    if not report.get("results") and not report.get("baseline_results"):
        errors.append(f"{report_path}: brak 'results'/'baseline_results' - nic do zwalidowania")

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
        print(f"VALIDATE_OBSERVABILITY: {len(all_errors)} problem(ow) telemetrii w {len(report_files)} raportach")
        for e in all_errors:
            print(f"  FAIL: {e}")
        return 1

    print(f"VALIDATE_OBSERVABILITY: OK ({len(report_files)} raportow, telemetria kompletna)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
