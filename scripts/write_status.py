"""Write Status - generuje reports/status.json w CI po zielonym pytest + walidatorach.

Zrodlo prawdy dla Panelu Badacza (SPRINT_v0.8.5.md, Priorytet 3, opcja a):
liczba testow i status CI nie sa wpisywane recznie do panel.js - panel czyta
ten plik. Skrypt uruchamia sie w .github/workflows/ci.yml WYLACZNIE PO tym,
jak pytest i wszystkie trzy walidatory juz przeszly (kazdy krok CI bez
`continue-on-error` przerywa joba przy niezerowym exit code) - wiec samo
dojscie do tego kroku jest dowodem, ze byly zielone.

SPRINT_v0.11.0.md Zadanie 3 (decyzja CTO 2026-07-18): plik VERSION w roocie
repo jest JEDYNYM zrodlem numeru sprintu - ten skrypt go czyta i wpisuje do
status.json jako pole "sprint". Panel czyta WYLACZNIE status.json (ZERO
literalow wersji w panel.js, egzekwowane przez scripts/validate_panel.py) -
zeby zmienic wersje widoczna w panelu, edytuje sie TYLKO plik VERSION.

Uzycie (w CI, po `pytest -q | tee pytest_output.txt`):
    python scripts/write_status.py pytest_output.txt reports/status.json
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PASSED_RE = re.compile(r"(\d+) passed")
VERSION_FILE = Path("VERSION")


def read_sprint_version() -> str:
    if not VERSION_FILE.exists():
        return ""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def parse_passed(pytest_output: str):
    m = PASSED_RE.search(pytest_output)
    return int(m.group(1)) if m else None


def git_commit_sha() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return ""


def main() -> int:
    pytest_log_path = sys.argv[1] if len(sys.argv) > 1 else "pytest_output.txt"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "reports/status.json"

    with open(pytest_log_path, encoding="utf-8") as f:
        pytest_output = f.read()

    passed = parse_passed(pytest_output)
    if passed is None:
        print(f"write_status: nie znaleziono wzorca 'N passed' w {pytest_log_path}", file=sys.stderr)
        return 1

    status = {
        "sprint": read_sprint_version(),
        "tests": {"passed": passed, "status": "green"},
        "validators": {
            "validate_publication": "OK",
            "validate_artifacts": "OK",
            "validate_panel": "OK",
        },
        "ci": {"conclusion": "success", "workflow": "ci.yml"},
        "commit": git_commit_sha(),
        "branch": os.environ.get("GITHUB_REF_NAME", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

    print(f"write_status: zapisano {out_path} ({passed} passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
