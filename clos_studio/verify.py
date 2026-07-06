"""Verify Layer v0.6 – z weryfikacją wersji CLOS."""

import math, json
from typing import Dict, Any, List
from clos_studio.manifest.matrix_schema import MatrixManifest
from clos_studio.metadata_index import MetadataIndex
from clos_studio.artifacts.manager import ArtifactManager, ArtifactStatus


class VerifyResult:
    def __init__(self):
        self.passed = True
        self.checks: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    def add_check(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed: self.passed = False; self.errors.append(f"[{name}] {detail}")

    def summary(self) -> str:
        lines = ["=" * 60, f"VERIFY RESULT: {'PASS' if self.passed else 'FAIL'}", "=" * 60]
        for check in self.checks:
            status = "PASS" if check["passed"] else "FAIL"
            lines.append(f"  [{status}] {check['name']}")
            if check["detail"]: lines.append(f"         {check['detail']}")
        lines.append("=" * 60)
        return "\n".join(lines)


def verify_experiment(experiment_id: str, manifest: MatrixManifest, metadata_index: MetadataIndex, artifact_manager: ArtifactManager) -> VerifyResult:
    result = VerifyResult()

    # 1. Integralność artefaktów
    integrity = artifact_manager.check_integrity(experiment_id)
    for name, status in integrity.items():
        if isinstance(status, ArtifactStatus):
            result.add_check(f"artifact:{name}", status == ArtifactStatus.COMPLETE, f"Status: {status.value}")

    # 2. Kompletność
    runs = metadata_index.get_experiment_runs(experiment_id)
    expected = manifest.get_total_runs()
    result.add_check("completeness:run_count", len(runs) == expected, f"Expected {expected}, got {len(runs)}")
    status_counts = metadata_index.get_run_count_by_status(experiment_id)
    completed = status_counts.get("COMPLETE", 0)
    failed = status_counts.get("FAILED", 0)
    result.add_check("completeness:all_completed", failed == 0 and completed == expected, f"Completed: {completed}, Failed: {failed}")

    # 3. Wersja workflow
    version_ok = all(run.get("workflow_version") == manifest.workflow_version for run in runs)
    result.add_check("version:workflow", version_ok, f"Expected v{manifest.workflow_version}")

    # ZADANIE 3: Weryfikacja zgodności wersji CLOS
    manifest_version = manifest.workflow_version
    clos_version = "0.6"  # Wersja z kodu
    version_match = manifest_version == clos_version
    result.add_check("version:clos_match", version_match, f"Manifest: v{manifest_version}, Code: v{clos_version}")

    # 4. Seed policy
    declared = set(manifest.seeds)
    actual = set(run["seed"] for run in runs)
    result.add_check("seed_policy", declared == actual, f"Declared={declared}, Actual={actual}")

    return result
