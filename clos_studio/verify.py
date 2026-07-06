"""Verify Layer – bramka jakości laboratorium."""

import math
import json
from typing import Dict, Any, List
from clos_studio.manifest.matrix_schema import MatrixManifest
from clos_studio.metadata_index import MetadataIndex
from clos_studio.artifacts.manager import ArtifactManager, ArtifactStatus


class VerifyResult:
    def __init__(self):
        self.passed = True
        self.checks: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_check(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            self.passed = False
            self.errors.append(f"[{name}] {detail}")

    def summary(self) -> str:
        lines = [
            "=" * 60,
            f"VERIFY RESULT: {'PASS' if self.passed else 'FAIL'}",
            "=" * 60,
        ]
        for check in self.checks:
            status = "PASS" if check["passed"] else "FAIL"
            lines.append(f"  [{status}] {check['name']}")
            if check["detail"]:
                lines.append(f"         {check['detail']}")
        if self.warnings:
            lines.append("\nWARNINGS:")
            for w in self.warnings:
                lines.append(f"  ! {w}")
        lines.append("=" * 60)
        return "\n".join(lines)


def verify_experiment(
    experiment_id: str,
    manifest: MatrixManifest,
    metadata_index: MetadataIndex,
    artifact_manager: ArtifactManager,
) -> VerifyResult:
    """Weryfikuje kompletność i integralność eksperymentu."""
    result = VerifyResult()

    # 1. Integralność artefaktów
    integrity = artifact_manager.check_integrity(experiment_id)
    # Sprawdź czy manifest istnieje
    manifest_ok = integrity.get("manifest") == ArtifactStatus.COMPLETE
    result.add_check("artifact:manifest", manifest_ok, str(integrity.get("manifest", "N/A")))

    # 2. Kompletność batcha
    runs = metadata_index.get_experiment_runs(experiment_id)
    expected_runs = manifest.get_total_runs()
    actual_runs = len(runs)
    runs_ok = actual_runs == expected_runs
    result.add_check("completeness:run_count", runs_ok, f"Expected {expected_runs}, got {actual_runs}")

    # 3. Statusy
    status_counts = metadata_index.get_run_count_by_status(experiment_id)
    completed = status_counts.get("COMPLETE", 0)
    failed = status_counts.get("FAILED", 0)
    all_ok = failed == 0 and completed == expected_runs
    result.add_check("completeness:all_completed", all_ok, f"Completed: {completed}, Failed: {failed}")

    # 4. Zgodność wersji
    version_ok = all(run.get("workflow_version") == manifest.workflow_version for run in runs)
    result.add_check("version:workflow", version_ok, f"Expected v{manifest.workflow_version}")

    # 5. Seed policy
    declared_seeds = set(manifest.seeds)
    actual_seeds = set(run["seed"] for run in runs)
    seeds_ok = declared_seeds == actual_seeds
    result.add_check("seed_policy", seeds_ok, f"Declared={declared_seeds}, Actual={actual_seeds}")

    return result
