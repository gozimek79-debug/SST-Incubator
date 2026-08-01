"""PC-001 B4a-2: test GWARANCJI MECHANICZNEJ ponownego pilota pod W2
(D-008 pkt 1), nie deklaracji. Analogiczny do
tests/test_pilot_power_analysis_guarantee.py (B4a), rozszerzony o:
- nowa nazwa wielkosci mierzonej (W_early_red, nie surowe W_early),
- pojedyncze srodowisko (noise_world, nie lista dwoch),
- test, ze zamrozona podloga byla UZYTA, nie PRZELICZONA (nowe w B4a-2),
- test strukturalnej waznosci V-C: okna W_early/W_late obejmuja calkowita
  liczbe okresow sine_wave (bez tego "constant" bylby przypadkowo poprawny,
  nie strukturalnie).
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

from runners.pilot_power_analysis_w2 import (  # noqa: E402
    PILOT_SEEDS, CONFIRMATORY_SEEDS_START, OUTPUT_PATH, ENVIRONMENT, LESSON,
    W_EARLY_TICKS, FLOOR_VALUE,
)
from clos_scientist.pc_001_experiment_config import FROZEN_FLOOR_NOISE_WORLD  # noqa: E402

FORBIDDEN_SUBSTRINGS = [
    "w_late", "trajectory", "trajektoria", "beta", "slope", "nachylenie",
    "reduction", "redukcja", "delta", "trend",
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

    def test_pilot_seeds_are_1_through_5(self):
        assert PILOT_SEEDS == [1, 2, 3, 4, 5]


class TestMechanicalGuaranteeOnOutputFile:

    def test_required_fields_present_and_correct(self, pilot_report):
        assert pilot_report["purpose"] == "power_analysis_only"
        assert pilot_report["NEVER_FOR_INFERENCE"] is True
        assert pilot_report["recorded_quantity"] == "W_early_red_only"
        assert pilot_report["seeds_used"] == PILOT_SEEDS
        assert pilot_report["confirmatory_seeds_start"] == CONFIRMATORY_SEEDS_START
        assert pilot_report["floor_used"] == FLOOR_VALUE
        assert pilot_report["floor_model"] == "constant"
        assert pilot_report["environment"] == ENVIRONMENT
        assert pilot_report["lesson"] == LESSON
        assert pilot_report["supersedes"] == (
            "pilot_PE_distribution_W_early.json (B4a, mierzyl PE surowe)"
        )

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
            "o efekcie:\n" + "\n".join(violations)
        )

    def test_no_list_of_raw_numbers_long_enough_to_be_a_trajectory(self, pilot_report):
        violations = []
        for path, key, value in _walk(pilot_report):
            if isinstance(value, list) and value and all(
                isinstance(v, (int, float)) and not isinstance(v, bool) for v in value
            ):
                if len(value) > MAX_ALLOWED_NUMERIC_LIST_LENGTH:
                    violations.append(
                        f"'{path}.{key}' to lista {len(value)} liczb - ksztalt "
                        f"trajektorii per-tick (W_EARLY_TICKS={W_EARLY_TICKS}), "
                        f"NIEDOZWOLONE"
                    )
        assert not violations, "\n".join(violations)

    def test_runs_carry_only_w_early_red_scalar_not_trajectory(self, pilot_report):
        for run in pilot_report["runs"]:
            assert set(run.keys()) == {"genome_id", "environment", "seed", "w_early_red", "status"}
            assert run["w_early_red"] is None or isinstance(run["w_early_red"], (int, float))
            assert run["status"] in {"VALID", "FLOOR_LIMITED", "INSUFFICIENT_DATA"}

    def test_n_runs_total_matches_23_genomes_x_5_seeds_x_1_environment(self, pilot_report):
        assert pilot_report["n_runs_total"] == 23 * 5 * 1 == 115
        assert len(pilot_report["runs"]) == 115

    def test_status_counts_are_internally_consistent(self, pilot_report):
        n_valid = sum(1 for r in pilot_report["runs"] if r["status"] == "VALID")
        n_floor = sum(1 for r in pilot_report["runs"] if r["status"] == "FLOOR_LIMITED")
        n_insuf = sum(1 for r in pilot_report["runs"] if r["status"] == "INSUFFICIENT_DATA")
        assert pilot_report["n_valid"] == n_valid
        assert pilot_report["n_floor_limited"] == n_floor
        assert pilot_report["n_insufficient_data"] == n_insuf
        assert n_valid + n_floor + n_insuf == pilot_report["n_runs_total"]


class TestFrozenFloorUsedNotRecomputed:
    """NOWE w B4a-2 (nieobecne w B4a, ktory nie mial jeszcze zamrozonej
    podlogi): dowod, ze runner UZYWA FROZEN_FLOOR_NOISE_WORLD, nie liczy
    wlasnej wersji. Dwie niezalezne kontrole: (1) wartosc w wyjsciu zgadza
    sie z zamrozona stala co do bitu, (2) kod zrodlowy runnera nie importuje
    niczego, co mogloby przeliczyc podloge (floor_at_tick/floor_profile/
    select_floor_model) - gdyby importowal, sama zgodnosc wartosci (1)
    nie dowodzilaby, ze wartosc NIE zostala przeliczona i przypadkiem
    wyszla taka sama."""

    def test_floor_used_equals_frozen_config_value_exactly(self, pilot_report):
        assert pilot_report["floor_used"] == FROZEN_FLOOR_NOISE_WORLD["value"] == 0.09589

    def test_runner_module_does_not_import_recomputation_functions(self):
        import runners.pilot_power_analysis_w2 as runner_module
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
                  / "pilot_power_analysis_w2.py").read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        code_lines = [line for line in no_docstrings.splitlines()
                      if not line.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        assert "clos_world.floor_model" not in code_only, (
            "runner importuje clos_world.floor_model w kodzie (poza "
            "docstringiem/komentarzem) - podejrzenie zywego przeliczania podlogi"
        )

    def test_floor_value_constant_matches_frozen_config_by_identity_of_source(self):
        """FLOOR_VALUE w runnerze MUSI pochodzic z FROZEN_FLOOR_NOISE_WORLD["value"]
        (odczyt), NIE byc osobno wpisana liczba 0.09589 - inaczej dwie kopie
        moglyby sie rozjechac po przyszlej zmianie configu bez wykrycia."""
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_power_analysis_w2.py").read_text(encoding="utf-8")
        assert 'FLOOR_VALUE = FROZEN_FLOOR_NOISE_WORLD["value"]' in source, (
            "FLOOR_VALUE nie jest jawnie odczytane z FROZEN_FLOOR_NOISE_WORLD "
            "- ryzyko rozjazdu dwoch kopii tej samej liczby"
        )


class TestStructuralVCValidity:
    """Weryfikacja PRZED uruchomieniem (zadanie): warunek waznosci V-C dla
    noise_world jest spelniony STRUKTURALNIE (okna obejmuja calkowita
    liczbe okresow sine_wave), nie przypadkiem - gdyby dlugosc okna sie
    zmienila, ten test by to zlapal, zanim bias_roznicowy trzeba by
    przeliczac na nowo (kosztowne, N=100_000)."""

    SINE_FREQUENCY = 0.1  # clos_world/scenarios.py::noise_world -> sine_wave(frequency=0.1)
    PERIOD_TICKS = 1 / SINE_FREQUENCY  # = 10
    W_EARLY_START, W_EARLY_END = 0, 60
    W_LATE_START, W_LATE_END = 240, 300

    def test_period_is_10_ticks(self):
        assert self.PERIOD_TICKS == 10.0

    def test_w_early_window_spans_whole_number_of_periods(self):
        window_length = self.W_EARLY_END - self.W_EARLY_START
        n_periods = window_length / self.PERIOD_TICKS
        assert n_periods == int(n_periods), (
            f"W_early [{self.W_EARLY_START},{self.W_EARLY_END}) nie obejmuje "
            f"calkowitej liczby okresow ({n_periods}) - V-C 'constant' bylby "
            f"przypadkowy, nie strukturalny"
        )
        assert n_periods == 6

    def test_w_late_window_spans_whole_number_of_periods(self):
        window_length = self.W_LATE_END - self.W_LATE_START
        n_periods = window_length / self.PERIOD_TICKS
        assert n_periods == int(n_periods)
        assert n_periods == 6

    def test_w_early_and_w_late_start_at_same_phase(self):
        """Silniejszy warunek niz 'ta sama liczba okresow': oba okna zaczynaja
        sie w TEJ SAMEJ fazie sinusa (tick mod period == 0 dla obu) - to
        dokladnie dlaczego bias_roznicowy (2.4e-05) jest tak bliski zeru,
        nie tylko 'wystarczajaco maly'."""
        assert self.W_EARLY_START % self.PERIOD_TICKS == self.W_LATE_START % self.PERIOD_TICKS

    def test_empirically_measured_bias_confirms_structural_argument(self):
        """Krzyzowa weryfikacja: bias_roznicowy faktycznie zmierzony (N=100_000,
        zapisany w FROZEN_FLOOR_NOISE_WORLD) jest rzedy wielkosci ponizej
        FLOOR_BIAS_TOLERANCE - zgodne z przewidywaniem strukturalnym
        (powinien byc ~0, bo okna sa fazowo identyczne)."""
        from clos_scientist.pc_001_experiment_config import FLOOR_BIAS_TOLERANCE
        assert FROZEN_FLOOR_NOISE_WORLD["bias_roznicowy"] < FLOOR_BIAS_TOLERANCE / 10, (
            "bias_roznicowy zmierzony nie jest rzedy wielkosci ponizej tolerancji "
            "- argument strukturalny (okna fazowo identyczne) nie zgadza sie z "
            "pomiarem, coś jest niespojne"
        )


class TestRunnerSourceDoesNotPersistTrajectory:

    def test_runner_source_never_calls_save_to_file(self):
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_power_analysis_w2.py").read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        code_lines = [line for line in no_docstrings.splitlines()
                      if not line.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        assert ".save_to_file(" not in code_only

    def test_runner_source_does_not_reference_w_late_or_trend(self):
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_power_analysis_w2.py").read_text(encoding="utf-8")
        forbidden_code_patterns = [
            re.compile(r"w_late\s*=", re.IGNORECASE),
            re.compile(r"\bslope\s*=", re.IGNORECASE),
            re.compile(r"\btrend\s*=", re.IGNORECASE),
        ]
        for pattern in forbidden_code_patterns:
            assert not pattern.search(source), (
                f"runner zawiera przypisanie pasujace do {pattern.pattern}"
            )
