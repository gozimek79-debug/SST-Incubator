"""Validate Publication - sprawdza kompletnosc prowenancji Publication Bundle.

Kazdy bundle w publications/ (poza oznaczonymi provenance="legacy-pre-0.7.2")
musi miec w metadata.json niepuste pola: git_commit, config_hash, manifest_hash,
timestamp, experiment_id (SPRINT_v0.8.4.md, Priorytet 3).

Legacy bundle (EXP-* sprzed prowenancji) sa pomijane - nie fabrykujemy im
git_commit ani hashy.

Uzycie:
    python scripts/validate_publication.py
Kod wyjscia: 0 = wszystkie bundle kompletne, 1 = brakuje ktoregos pola.
"""

import json
import sys
from pathlib import Path

PUBLICATIONS_DIR = Path("publications")
REQUIRED_FIELDS = ["git_commit", "config_hash", "manifest_hash", "timestamp", "experiment_id"]
LEGACY_MARKER = "legacy-pre-0.7.2"


def validate_bundle(bundle_dir: Path) -> list:
    metadata_path = bundle_dir / "metadata.json"
    if not metadata_path.exists():
        return [f"{bundle_dir}: brak metadata.json"]

    with open(metadata_path, encoding="utf-8") as f:
        metadata = json.load(f)

    if metadata.get("provenance") == LEGACY_MARKER:
        return []

    errors = []
    for field in REQUIRED_FIELDS:
        if not metadata.get(field):
            errors.append(f"{bundle_dir}: pole '{field}' puste lub brakujace w metadata.json")
    return errors


def main() -> int:
    if not PUBLICATIONS_DIR.exists():
        print(f"OK: brak katalogu {PUBLICATIONS_DIR} - nic do walidacji")
        return 0

    bundle_dirs = sorted(p for p in PUBLICATIONS_DIR.iterdir() if p.is_dir())
    all_errors = []
    for bundle_dir in bundle_dirs:
        all_errors.extend(validate_bundle(bundle_dir))

    if all_errors:
        print(f"VALIDATE_PUBLICATION: {len(all_errors)} problem(ow) w {len(bundle_dirs)} bundlach")
        for e in all_errors:
            print(f"  FAIL: {e}")
        return 1

    print(f"VALIDATE_PUBLICATION: OK ({len(bundle_dirs)} bundli sprawdzonych)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
