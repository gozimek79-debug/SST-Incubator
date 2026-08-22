"""N_OPERATIONAL_SEEDS zgadza sie z artefaktem B4b (B4B-03).

W ODROZNIENIU od tests/test_condition_b_threshold_provenance.py (zrodlo:
prerejestracja, MARKDOWN - wartosc niesie WYLACZNIE proza, stad parsowanie
tekstu z kotwicami), zrodlem N_OPERATIONAL_SEEDS jest publications/
power_analysis_PC_001.json - JSON, wiec wartosc jest odczytywalna
STRUKTURALNIE (klucz required_seeds.n_operational.value). Parsowanie prozy
tutaj byloby regresja wobec dostepnego, prostszego, mniej kruchego sposobu
weryfikacji - patrz warunek zatrzymania B4B-03.

Test negatywny: funkcja weryfikujaca dostaje BLEDNA oczekiwana wartosc i
MUSI zglosic niezgodnosc - nie samo issnienie klucza w JSON (ktore nigdy
by nie zmienilo sie samo z siebie), tylko rzeczywiste porownanie z CONFIG.
"""

import json
from pathlib import Path

from clos_scientist.pc_001_experiment_config import N_OPERATIONAL_SEEDS

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "publications" / "power_analysis_PC_001.json"


def load_n_operational_from_artifact(artifact_path: Path) -> int:
    with open(artifact_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["required_seeds"]["n_operational"]["value"]


def verify_n_operational_provenance(artifact_value: int, expected_config_value: int):
    """Zwraca liste problemow (pusta = OK)."""
    problems = []
    if artifact_value != expected_config_value:
        problems.append(
            f"artefakt required_seeds.n_operational.value={artifact_value} != "
            f"CONFIG N_OPERATIONAL_SEEDS={expected_config_value}"
        )
    return problems


REAL_ARTIFACT_VALUE = load_n_operational_from_artifact(ARTIFACT_PATH)


class TestConstantValue:
    def test_constant_is_eight(self):
        assert N_OPERATIONAL_SEEDS == 8


class TestArtifactStructurallyReadable:
    """Warunek zatrzymania B4B-03: jesli wartosc nie jest odczytywalna
    strukturalnie z JSON-a, to wada artefaktu, nie powod do parsowania
    prozy. Ten test dowodzi, ze klucz istnieje i jest liczba calkowita."""

    def test_artifact_has_structural_int_field(self):
        assert isinstance(REAL_ARTIFACT_VALUE, int)

    def test_n_power_field_also_structurally_readable_and_unchanged(self):
        """B4B-03 zakaz: NIE przepisuj N_power. Dowod, ze artefakt nadal
        niesie n_power=6 jako ODREBNE pole, nieporuszone przez ta zmiane."""
        with open(ARTIFACT_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert data["required_seeds"]["n_power"]["value"] == 6
        assert data["required_seeds"]["n_power"]["value"] != REAL_ARTIFACT_VALUE, (
            "n_power i n_operational musza byc dwiema ROZNYMI liczbami - "
            "identycznosc sugerowalaby, ze ktos po cichu zunifikowal je z powrotem"
        )


class TestEndToEndVerification:
    def test_real_artifact_matches_config(self):
        problems = verify_n_operational_provenance(REAL_ARTIFACT_VALUE, N_OPERATIONAL_SEEDS)
        assert problems == []


class TestNegativeWrongExpectedValue:
    """Zmieniona (bledna) oczekiwana wartosc -> FAIL, nie ciche PASS."""

    def test_wrong_expected_value_is_caught(self):
        problems = verify_n_operational_provenance(REAL_ARTIFACT_VALUE, expected_config_value=6)
        assert problems != []
        assert "!=" in problems[0]

    def test_wrong_artifact_value_is_caught(self):
        problems = verify_n_operational_provenance(artifact_value=99, expected_config_value=N_OPERATIONAL_SEEDS)
        assert problems != []
        assert "!=" in problems[0]
