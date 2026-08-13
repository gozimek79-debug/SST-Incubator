"""PC-001 Pilot Final (PF-01/PF-02): test GWARANCJI MECHANICZNEJ, nie deklaracji.
Analogiczny do tests/test_pilot_w2_power_analysis_guarantee.py (B4a-2),
rozszerzony o:
- dwa srodowiska (noise_world, pure_noise_world) zamiast jednego,
- 15 seedow (D-042) zamiast 5,
- druga wielkosc mierzona (spearman_early_rho) obok w_early_red,
- podloga zamrozona dla OBU srodowisk uzyta, nie przeliczona,
- "recovery" w FORBIDDEN_SUBSTRINGS (recovery_i jest wynikiem K3b, nigdy nie
  moze trafic do artefaktu pilota - publications/
  BEZPIECZENSTWO_POMIARU_recovery_spearman.md §2).
"""

import inspect
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "execution_package_v0_11"))
sys.path.insert(0, str(REPO_ROOT))

from runners.pilot_final import (  # noqa: E402
    PILOT_SEEDS, CONFIRMATORY_SEEDS_START, OUTPUT_PATH, ENVIRONMENTS, LESSON,
    W_EARLY_TICKS, SPEARMAN_WINDOW, FLOOR_BY_ENVIRONMENT,
)
from clos_scientist.pc_001_experiment_config import (  # noqa: E402
    FROZEN_FLOOR_NOISE_WORLD, FROZEN_FLOOR_PURE_NOISE_WORLD,
)

FORBIDDEN_SUBSTRINGS = [
    "w_late", "trajectory", "trajektoria", "beta", "slope", "nachylenie",
    "reduction", "redukcja", "delta", "trend", "recovery",
]

MAX_ALLOWED_NUMERIC_LIST_LENGTH = 10


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield (path, k, v)
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


@pytest.fixture(scope="module")
def pilot_report():
    if not OUTPUT_PATH.exists():
        pytest.skip(f"pilot jeszcze nie uruchomiony - brak {OUTPUT_PATH}")
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestSeedDisjointness:

    def test_pilot_seeds_below_confirmatory_start(self):
        assert max(PILOT_SEEDS) < CONFIRMATORY_SEEDS_START

    def test_confirmatory_seeds_start_is_1001(self):
        assert CONFIRMATORY_SEEDS_START == 1001

    def test_pilot_seeds_are_1_through_15(self):
        """D-042: 15 seedow, konserwatywna decyzja projektowa (nie wynik
        analizy - 5 bylo za malo, patrz ANALIZA_WARIANCJI_PILOTA_2026-08-03.md)."""
        assert PILOT_SEEDS == list(range(1, 16))
        assert len(PILOT_SEEDS) == 15


class TestTwoEnvironments:

    def test_both_environments_present(self):
        assert set(ENVIRONMENTS) == {"noise_world", "pure_noise_world"}

    def test_spearman_window_is_early_only(self):
        """publications/BEZPIECZENSTWO_POMIARU_recovery_spearman.md §3.2:
        WYLACZNIE okno [0,60) - nigdy pozne/cale/roznica."""
        assert SPEARMAN_WINDOW == [0, 60]
        assert SPEARMAN_WINDOW[1] == W_EARLY_TICKS


class TestMechanicalGuaranteeOnOutputFile:

    def test_required_fields_present_and_correct(self, pilot_report):
        assert pilot_report["purpose"] == "power_analysis_only"
        assert pilot_report["NEVER_FOR_INFERENCE"] is True
        assert pilot_report["recorded_quantity"] == "W_early_red_and_spearman_early_only"
        assert pilot_report["seeds_used"] == PILOT_SEEDS
        assert pilot_report["confirmatory_seeds_start"] == CONFIRMATORY_SEEDS_START
        assert set(pilot_report["environment"]) == set(ENVIRONMENTS)
        assert pilot_report["lesson"] == LESSON
        assert pilot_report["w_early_tick_window"] == [0, W_EARLY_TICKS]
        assert pilot_report["spearman_early_window"] == SPEARMAN_WINDOW

    def test_no_forbidden_keys_or_string_values_anywhere(self, pilot_report):
        violations = []
        for path, key, value in _walk(pilot_report):
            key_l = str(key).lower()
            for bad in FORBIDDEN_SUBSTRINGS:
                if bad in key_l:
                    violations.append(f"klucz '{path}.{key}' zawiera zakazany wzorzec '{bad}'")
            if isinstance(value, str):
                value_l = value.lower()
                for bad in FORBIDDEN_SUBSTRINGS:
                    if bad in value_l:
                        violations.append(
                            f"wartosc-string pod '{path}.{key}' zawiera zakazany wzorzec '{bad}': {value!r}"
                        )
        assert not violations, (
            "GWARANCJA MECHANICZNA ZLAMANA - plik wyjsciowy niesie informacje "
            "o efekcie lub o recovery_i (wynik K3b):\n" + "\n".join(violations)
        )

    def test_no_list_of_raw_numbers_long_enough_to_be_a_trajectory(self, pilot_report):
        # "seeds_used" jest jawnie wymaganym polem metadanych (PF-01/PF-02),
        # nie pomiarem per-tick - D-042 podniosl liczbe seedow do 15, wiec
        # jego dlugosc (15) przekracza prog trajektorii (10) samym rozmiarem
        # puli seedow, nie ksztaltem danych. Wykluczony PO NAZWIE KLUCZA (waski
        # wyjatek), nie przez podniesienie progu dla wszystkiego - prawdziwa
        # trajektoria (W_EARLY_TICKS=60+) nadal zostanie zlapana wszedzie indziej.
        violations = []
        for path, key, value in _walk(pilot_report):
            if key == "seeds_used":
                continue
            if isinstance(value, list) and value and all(
                isinstance(v, (int, float)) and not isinstance(v, bool) for v in value
            ):
                if len(value) > MAX_ALLOWED_NUMERIC_LIST_LENGTH:
                    violations.append(
                        f"'{path}.{key}' to lista {len(value)} liczb - ksztalt "
                        f"trajektorii per-tick, NIEDOZWOLONE"
                    )
        assert not violations, "\n".join(violations)

    def test_runs_carry_only_declared_scalars_not_trajectory(self, pilot_report):
        for run in pilot_report["runs"]:
            assert set(run.keys()) == {
                "genome_id", "environment", "seed", "w_early_red",
                "spearman_early_rho", "status",
            }
            assert run["w_early_red"] is None or isinstance(run["w_early_red"], (int, float))
            assert run["spearman_early_rho"] is None or isinstance(run["spearman_early_rho"], (int, float))
            assert run["status"] in {"VALID", "FLOOR_LIMITED", "INSUFFICIENT_DATA"}
            assert run["environment"] in ENVIRONMENTS

    def test_n_runs_total_matches_23_genomes_x_15_seeds_x_2_environments(self, pilot_report):
        assert pilot_report["n_runs_total"] == 23 * 15 * 2 == 690
        assert len(pilot_report["runs"]) == 690

    def test_status_counts_are_internally_consistent(self, pilot_report):
        n_valid = sum(1 for r in pilot_report["runs"] if r["status"] == "VALID")
        n_floor = sum(1 for r in pilot_report["runs"] if r["status"] == "FLOOR_LIMITED")
        n_insuf = sum(1 for r in pilot_report["runs"] if r["status"] == "INSUFFICIENT_DATA")
        assert pilot_report["n_valid"] == n_valid
        assert pilot_report["n_floor_limited"] == n_floor
        assert pilot_report["n_insufficient_data"] == n_insuf
        assert n_valid + n_floor + n_insuf == pilot_report["n_runs_total"]

    def test_by_environment_breakdown_not_aggregated(self, pilot_report):
        """PF-02: 'NIE agreguj - to sa dwie rozne wielkosci o roznym znaczeniu'
        - noise_world i pure_noise_world musza miec ODDZIELNE liczniki."""
        by_env = pilot_report["by_environment"]
        assert set(by_env.keys()) == {"noise_world", "pure_noise_world"}
        for env in ENVIRONMENTS:
            env_data = by_env[env]
            env_runs = [r for r in pilot_report["runs"] if r["environment"] == env]
            n_valid = sum(1 for r in env_runs if r["status"] == "VALID")
            n_floor = sum(1 for r in env_runs if r["status"] == "FLOOR_LIMITED")
            n_insuf = sum(1 for r in env_runs if r["status"] == "INSUFFICIENT_DATA")
            assert env_data["n_runs_total"] == len(env_runs) == 23 * 15
            assert env_data["n_valid"] == n_valid
            assert env_data["n_floor_limited"] == n_floor
            assert env_data["n_insufficient_data"] == n_insuf


class TestFrozenFloorUsedNotRecomputedBothEnvironments:
    """Rozszerzenie TestFrozenFloorUsedNotRecomputed (B4a-2) na oba srodowiska -
    dowod, ze runner UZYWA obu zamrozonych podlog, nie liczy wlasnej wersji."""

    def test_floor_used_equals_frozen_config_value_exactly_noise_world(self, pilot_report):
        assert pilot_report["by_environment"]["noise_world"]["floor_used"] == FROZEN_FLOOR_NOISE_WORLD["value"]

    def test_floor_used_equals_frozen_config_value_exactly_pure_noise_world(self, pilot_report):
        assert pilot_report["by_environment"]["pure_noise_world"]["floor_used"] == FROZEN_FLOOR_PURE_NOISE_WORLD["value"]

    def test_floor_model_recorded_not_assumed(self, pilot_report):
        """PF-02: floor_model dla pure_noise_world NIE zalozony - zapisany
        wynik mechanicznego testu V-C (select_floor_model), moze byc
        'constant' albo 'per_tick'."""
        assert pilot_report["by_environment"]["noise_world"]["floor_model"] == FROZEN_FLOOR_NOISE_WORLD["floor_model"]
        assert pilot_report["by_environment"]["pure_noise_world"]["floor_model"] == FROZEN_FLOOR_PURE_NOISE_WORLD["floor_model"]
        assert pilot_report["by_environment"]["pure_noise_world"]["floor_model"] in {"constant", "per_tick"}

    def test_runner_module_does_not_import_recomputation_functions(self):
        import runners.pilot_final as runner_module
        module_globals = vars(runner_module)
        forbidden_names = {"floor_at_tick", "floor_profile", "select_floor_model",
                            "verify_frozen_floor_env"}
        imported_forbidden = forbidden_names & set(module_globals.keys())
        assert not imported_forbidden, (
            f"runner importuje funkcje przeliczajace podloge: {imported_forbidden} - "
            "to podwaza gwarancje 'uzyta zamrozona wartosc, nie przeliczona'"
        )

    def test_runner_source_does_not_reference_floor_model_module(self):
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_final.py").read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        code_lines = [line for line in no_docstrings.splitlines()
                      if not line.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        assert "clos_world.floor_model" not in code_only, (
            "runner importuje clos_world.floor_model w kodzie (poza "
            "docstringiem/komentarzem) - podejrzenie zywego przeliczania podlogi"
        )

    def test_floor_value_constants_come_from_frozen_config_by_identity_of_source(self):
        """FLOOR_BY_ENVIRONMENT musi pochodzic z FROZEN_FLOOR_*["value"]
        (odczyt), nie byc osobno wpisanymi liczbami - inaczej kopie moglyby
        sie rozjechac po przyszlej zmianie configu bez wykrycia."""
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_final.py").read_text(encoding="utf-8")
        assert 'FROZEN_FLOOR_NOISE_WORLD["value"]' in source
        assert 'FROZEN_FLOOR_PURE_NOISE_WORLD["value"]' in source


class TestRunnerSourceDoesNotPersistTrajectoryOrForbiddenQuantities:

    def test_runner_source_never_calls_save_to_file(self):
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_final.py").read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        code_lines = [line for line in no_docstrings.splitlines()
                      if not line.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        assert ".save_to_file(" not in code_only

    def test_runner_source_does_not_reference_w_late_trend_or_recovery(self):
        # Docstringi wykluczone (opisuja PROZA, ze recovery_i NIE jest mierzone -
        # sama proza zawiera slowo "recovery"). Wzorzec "recovery_i" (nie samo
        # "recovery") - runner LEGALNIE importuje/wola run_shock_recovery()
        # (nazwa funkcji lekcji L1.2, ten sam import co w B4a-2) - to nie jest
        # obliczanie zakazanej wielkosci recovery_i (Aneks 1, K3b).
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_final.py").read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        forbidden_code_patterns = [
            re.compile(r"w_late\s*=", re.IGNORECASE),
            re.compile(r"\bslope\s*=", re.IGNORECASE),
            re.compile(r"\btrend\s*=", re.IGNORECASE),
            re.compile(r"recovery_i\b", re.IGNORECASE),
        ]
        for pattern in forbidden_code_patterns:
            assert not pattern.search(no_docstrings), (
                f"runner zawiera wzorzec zakazany {pattern.pattern}"
            )

    def test_spearman_computed_exactly_once_on_early_window_only(self):
        """Statyczna kontrola przeciw rozszerzeniu okna Spearmana w przyszlosci
        bez wykrycia - spearman_rho() ma dokladnie jedno miejsce wywolania,
        na danych zebranych pod warunkiem tick < W_EARLY_TICKS (ten sam
        filtr co dla prediction_error)."""
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_final.py").read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        code_lines = [line for line in no_docstrings.splitlines()
                      if not line.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        assert code_only.count("spearman_rho(") == 1, (
            "spearman_rho() powinno byc wywolane dokladnie raz - wiecej "
            "wywolan sugeruje pomiar poza oknem wczesnym"
        )
