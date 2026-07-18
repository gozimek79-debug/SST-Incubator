"""Validate Bundle Freshness - frozen==true jako JEDYNY dopuszczalny wyjatek
od zasady kod==artefakt dla Publication Bundles (SPRINT_v0.11.0.md, decyzja
CTO 2026-07-17).

Zasada projektu: kazdy bundle w publications/ powinien byc regenerowalny z
biezacego kodu bez zmiany wartosci (kod==artefakt) - to gwarantuja
scripts/publish_*.py i tests/test_genome_params_regression.py dla
wewnetrznych golden-baseline'ow. JEDYNY dopuszczalny wyjatek: bundle jawnie
oznaczony "frozen": true w metadata.json (np. juz opublikowany i
niezaleznie zreplikowany, patrz publications/L1_1_pattern_echo/metadata.json).

Wyjatek musi byc uzasadniony TAK SAMO rygorystycznie jak sama regula -
frozen=true BEZ pelnego uzasadnienia jest BLEDEM tego walidatora, nie
zwolnieniem z odpowiedzialnosci:
  - brak/pusty "frozen_reason"              -> FAIL
  - brak/pusty "regeneration_expected_diff" -> FAIL
  - oba obecne i niepuste                   -> OK dla tego bundla

Bundle bez "frozen" (lub frozen=false) jest poza zakresem tego walidatora -
oczekuje sie od niego swiezosci, ktora egzekwuja inne mechanizmy (patrz
docstring wyzej), nie ten skrypt.

Uzycie:
    python scripts/validate_bundle_freshness.py
Kod wyjscia: 0 = kazdy frozen bundle ma pelne uzasadnienie (lub nie ma
zadnego frozen bundla); 1 = ktorys bundle ma frozen=true bez frozen_reason
i/lub regeneration_expected_diff.
"""

import json
import sys
from pathlib import Path
from typing import List

PUBLICATIONS_DIR = Path("publications")


def validate_bundle_metadata(bundle_label: str, metadata: dict) -> List[str]:
    """Czysta funkcja (label, metadata-dict) -> lista bledow - testowalna
    bez dotykania dysku, uzywana zarowno przez main() jak i testy."""
    if not metadata.get("frozen", False):
        return []

    errors = []
    if not metadata.get("frozen_reason"):
        errors.append(
            f"{bundle_label}: frozen=true ale brak 'frozen_reason' - "
            "wyjatek od zasady kod==artefakt bez uzasadnienia"
        )
    if not metadata.get("regeneration_expected_diff"):
        errors.append(
            f"{bundle_label}: frozen=true ale brak 'regeneration_expected_diff' - "
            "nie wiadomo co konkretnie zmieniloby sie przy regeneracji"
        )
    return errors


def validate_bundle_dir(bundle_dir: Path) -> List[str]:
    metadata_path = bundle_dir / "metadata.json"
    if not metadata_path.exists():
        return []  # brak metadata.json to zakres scripts/validate_publication.py, nie tego walidatora

    with open(metadata_path, encoding="utf-8") as f:
        metadata = json.load(f)

    return validate_bundle_metadata(str(bundle_dir), metadata)


def main() -> int:
    if not PUBLICATIONS_DIR.exists():
        print(f"OK: brak katalogu {PUBLICATIONS_DIR} - nic do walidacji")
        return 0

    bundle_dirs = sorted(p for p in PUBLICATIONS_DIR.iterdir() if p.is_dir())
    all_errors: List[str] = []
    for bundle_dir in bundle_dirs:
        all_errors.extend(validate_bundle_dir(bundle_dir))

    if all_errors:
        print(f"VALIDATE_BUNDLE_FRESHNESS: {len(all_errors)} problem(ow)")
        for e in all_errors:
            print(f"  FAIL: {e}")
        return 1

    n_frozen = sum(
        1 for d in bundle_dirs
        if (d / "metadata.json").exists()
        and json.loads((d / "metadata.json").read_text(encoding="utf-8")).get("frozen", False)
    )
    print(
        f"VALIDATE_BUNDLE_FRESHNESS: OK ({len(bundle_dirs)} bundli sprawdzonych, "
        f"{n_frozen} frozen z pelnym uzasadnieniem)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
