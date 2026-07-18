"""Publication Bundle – tworzy kompletne archiwum eksperymentu.

ZASADA "kod==artefakt": kazdy bundle w publications/ MUSI byc regenerowalny
z biezacego kodu (uruchomienie odpowiedniego lesson/publish_*.py) dajac
BAJTOWO IDENTYCZNE wyniki (poza metadanymi prowenancji: git_commit,
config_hash, manifest_hash, timestamp - te ZAWSZE zmieniaja sie przy kazdej
regeneracji). To gwarantuje, ze opublikowany bundle jest zawsze wiernym
zapisem tego, co kod FAKTYCZNIE liczy, nie zamrozona migawka, ktora moze
cicho rozjechac sie z prawda.

JEDYNY dopuszczalny wyjatek (SPRINT_v0.11.0.md, decyzja CTO 2026-07-17):
bundle jawnie oznaczony "frozen": true w metadata.json - dla przypadkow, gdy
regeneracja zmienilaby WYLACZNIE nazwy pol/etykiety (nie wartosci), a bundle
zostal juz opublikowany i niezaleznie zweryfikowany (np. slepa replikacja
zewnetrznego audytora - patrz publications/L1_1_pattern_echo/metadata.json,
pierwszy i na razie jedyny taki przypadek: pola mse_*->mae_*, SPRINT_v0.11.0.md
P1). Regeneracja w takiej sytuacji stworzylaby pozor retroaktywnej zmiany
historii publikacji bez realnej korzysci - "frozen" jest swiadomym wyjatkiem,
nie zapomnianym TODO.

Wyjatek jest kontrolowany TAK SAMO rygorystycznie jak sama regula:
frozen=true BEZ pol "frozen_reason" (dlaczego zamrozony) i
"regeneration_expected_diff" (co konkretnie zmieniloby sie przy regeneracji)
jest BLEDEM, egzekwowanym przez scripts/validate_bundle_freshness.py
(4 scenariusze testowe: frozen bez uzasadnienia / brak frozen_reason / brak
regeneration_expected_diff / poprawny frozen - patrz
tests/test_bundle_freshness_validator.py).
"""

import json
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def _git_commit() -> str:
    """Zwraca aktualny commit HEAD lub '' gdy niedostępny (brak repo)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _config_hash(manifest_dict: Dict[str, Any]) -> str:
    """Stabilny sha256 kanonicznego manifestu — pin konfiguracji eksperymentu."""
    canonical = json.dumps(manifest_dict, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def build_bundle(
    experiment_id: str,
    manifest_dict: Dict[str, Any],
    provenance_dict: Dict[str, Any],
    results: list,
    artifacts_base: str = "experiments",
    output_dir: str = "publications",
) -> str:
    """Tworzy kompletne archiwum publikacyjne.

    Args:
        experiment_id: ID eksperymentu.
        manifest_dict: Manifest jako słownik.
        provenance_dict: Proweniencja jako słownik.
        results: Lista wyników runów.
        artifacts_base: Katalog z artefaktami.
        output_dir: Katalog wyjściowy.

    Returns:
        Ścieżka do archiwum.
    """
    bundle_path = Path(output_dir) / experiment_id
    bundle_path.mkdir(parents=True, exist_ok=True)

    # Manifest
    manifest_path = bundle_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2, ensure_ascii=False)

    # Provenance
    with open(bundle_path / "provenance.json", "w", encoding="utf-8") as f:
        json.dump(provenance_dict, f, indent=2, ensure_ascii=False)

    # Results
    results_dir = bundle_path / "runs"
    results_dir.mkdir(exist_ok=True)
    for i, result in enumerate(results):
        with open(results_dir / f"run_{i:04d}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    # Metadata
    # git_commit: użyj z provenance, a gdy pusty — automatycznie z repo.
    git_commit = provenance_dict.get("git_commit", "") or _git_commit()
    timestamp = datetime.now().isoformat()
    # manifest_hash: sha256 pliku manifest.json zapisanego na dysku (integralnosc
    # artefaktu) — odrebne od config_hash (sha256 kanonicznego slownika konfiguracji,
    # stabilne niezaleznie od formatowania pliku).
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    metadata = {
        "experiment_id": experiment_id,
        "git_commit": git_commit,
        "config_hash": _config_hash(manifest_dict),
        "manifest_hash": manifest_hash,
        "timestamp": timestamp,
        "clos_version": provenance_dict.get("clos_version", ""),
        "cli_version": provenance_dict.get("cli_version", ""),
        "manifest_version": manifest_dict.get("schema_version", 1),
        "bundled_at": timestamp,
        "total_runs": len(results),
        "reproducible": bool(git_commit),
    }
    with open(bundle_path / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Kopiuj istniejące artefakty
    artifacts_src = Path(artifacts_base) / experiment_id
    if artifacts_src.exists():
        artifacts_dst = bundle_path / "artifacts"
        shutil.copytree(artifacts_src, artifacts_dst, dirs_exist_ok=True)

    return str(bundle_path)
