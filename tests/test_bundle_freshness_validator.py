"""SPRINT_v0.11.0.md, decyzja CTO 2026-07-17: frozen==true jako JEDYNY
dopuszczalny wyjatek od zasady kod==artefakt (scripts/validate_bundle_freshness.py).

Wymog CTO: wyjatek musi byc kontrolowany TAK SAMO rygorystycznie jak sama
regula - stad test negatywny na 4 scenariusze:
  (a) frozen=true bez ZADNEGO uzasadnienia          -> FAIL
  (b) frozen=true, brak frozen_reason               -> FAIL
  (c) frozen=true, brak regeneration_expected_diff  -> FAIL
  (d) frozen=true, oba pola obecne i niepuste        -> OK
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.validate_bundle_freshness import validate_bundle_metadata

VALID_REASON = "Bundle juz opublikowany i zreplikowany - regeneracja stworzylaby pozor zmiany historii."
VALID_DIFF = "Regeneracja zmienilaby wylacznie nazwy kluczy mse_*->mae_*, zero zmiany wartosci."


class TestFrozenExceptionControlledAsStrictlyAsRule:
    """(a)-(d): jeden wspolny test parametryzowany, zeby 4 scenariusze byly
    widoczne obok siebie i nie moglo dojsc do rozjazdu miedzy nimi."""

    def test_a_frozen_without_any_justification_fails(self):
        errors = validate_bundle_metadata("bundle_a", {"frozen": True})
        assert errors, "(a) frozen=true bez uzasadnienia MUSI dac blad"
        assert any("frozen_reason" in e for e in errors)
        assert any("regeneration_expected_diff" in e for e in errors)

    def test_b_frozen_missing_reason_only_fails(self):
        errors = validate_bundle_metadata(
            "bundle_b", {"frozen": True, "regeneration_expected_diff": VALID_DIFF}
        )
        assert errors, "(b) brak frozen_reason MUSI dac blad"
        assert any("frozen_reason" in e for e in errors)
        assert not any("regeneration_expected_diff" in e for e in errors), (
            "regeneration_expected_diff jest obecne - nie powinno byc zglaszane jako brakujace"
        )

    def test_c_frozen_missing_diff_only_fails(self):
        errors = validate_bundle_metadata(
            "bundle_c", {"frozen": True, "frozen_reason": VALID_REASON}
        )
        assert errors, "(c) brak regeneration_expected_diff MUSI dac blad"
        assert any("regeneration_expected_diff" in e for e in errors)
        assert not any(
            "frozen_reason" in e and "regeneration_expected_diff" not in e for e in errors
        )

    def test_d_frozen_fully_justified_passes(self):
        errors = validate_bundle_metadata(
            "bundle_d",
            {"frozen": True, "frozen_reason": VALID_REASON, "regeneration_expected_diff": VALID_DIFF},
        )
        assert errors == [], "(d) w pelni uzasadniony frozen NIE MOZE dac bledu"

    def test_empty_string_reason_treated_as_missing(self):
        """Pusty string to NIE jest uzasadnienie - ten sam blad co brak pola."""
        errors = validate_bundle_metadata(
            "bundle_e", {"frozen": True, "frozen_reason": "", "regeneration_expected_diff": VALID_DIFF}
        )
        assert any("frozen_reason" in e for e in errors)

    def test_non_frozen_bundle_is_out_of_scope(self):
        """frozen=false (lub brak pola) - ten walidator NIE zglasza bledu
        niezaleznie od tego, czy frozen_reason/regeneration_expected_diff
        istnieja - swiezosc bundla egzekwuja inne mechanizmy, nie ten."""
        assert validate_bundle_metadata("bundle_f", {}) == []
        assert validate_bundle_metadata("bundle_g", {"frozen": False}) == []


class TestRealFrozenBundleIsValid:
    """publications/L1_1_pattern_echo/metadata.json - jedyny obecnie frozen
    bundle w repo - musi przechodzic ten walidator bez bledu."""

    def test_l1_1_pattern_echo_bundle_passes(self):
        with open("publications/L1_1_pattern_echo/metadata.json", encoding="utf-8") as f:
            metadata = json.load(f)
        assert metadata.get("frozen") is True
        errors = validate_bundle_metadata("publications/L1_1_pattern_echo", metadata)
        assert errors == [], errors


class TestExitCodesEndToEnd:
    """Rzeczywiste kody wyjscia procesu (nie tylko funkcji Pythona) dla
    wszystkich 4 scenariuszy - buduje tymczasowy katalog publications/ i
    wywoluje skrypt jako subprocess, dokladnie jak CI/uzytkownik by go uruchomil."""

    def _run_against(self, tmp_path: Path, metadata: dict) -> int:
        pubs = tmp_path / "publications" / "bundle_x"
        pubs.mkdir(parents=True)
        (pubs / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        script = Path.cwd() / "scripts" / "validate_bundle_freshness.py"
        result = subprocess.run(
            [sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True
        )
        return result.returncode

    def test_a_exit_code_1(self, tmp_path):
        assert self._run_against(tmp_path, {"frozen": True}) == 1

    def test_b_exit_code_1(self, tmp_path):
        assert self._run_against(
            tmp_path, {"frozen": True, "regeneration_expected_diff": VALID_DIFF}
        ) == 1

    def test_c_exit_code_1(self, tmp_path):
        assert self._run_against(
            tmp_path, {"frozen": True, "frozen_reason": VALID_REASON}
        ) == 1

    def test_d_exit_code_0(self, tmp_path):
        assert self._run_against(
            tmp_path,
            {"frozen": True, "frozen_reason": VALID_REASON, "regeneration_expected_diff": VALID_DIFF},
        ) == 0
