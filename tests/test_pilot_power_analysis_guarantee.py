"""PC-001 B4a: test GWARANCJI MECHANICZNEJ pilota (D-008 pkt 1), nie
deklaracji. Ta sama zasada, co przy kazdym walidatorze w tym projekcie:
zabezpieczenie bez testu negatywnego jest dekoracja.

Sprawdza:
1. Plik wyjsciowy (reports/pilot/pilot_PE_distribution_W_early.json) NIE
   zawiera zadnego klucza/wartosci-stringa niosacego informacje o efekcie
   (W_late, trajektoria, beta/nachylenie, redukcja/delta/trend) - rekurencyjnie
   po calej strukturze.
2. Zadna lista w pliku wyjsciowym nie jest ksztaltu "trajektoria" (lista
   surowych liczb dluzsza niz kilka elementow) - jedyne dopuszczalne listy
   liczbowe to male, ustalone z gory (seeds_used, w_early_tick_window).
3. Pola obowiazkowe (purpose/NEVER_FOR_INFERENCE/recorded_quantity/
   seeds_used/confirmatory_seeds_start/lesson/environments) sa obecne i
   maja oczekiwane wartosci.
4. Seedy pilota (PILOT_SEEDS) sa rozlaczne z zakresem konfirmacyjnym
   (>= CONFIRMATORY_SEEDS_START) - D-008 pkt 5.
"""

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "execution_package_v0_11"))
sys.path.insert(0, str(REPO_ROOT))

from runners.pilot_power_analysis import (  # noqa: E402
    PILOT_SEEDS, CONFIRMATORY_SEEDS_START, OUTPUT_PATH, ENVIRONMENTS, LESSON,
    W_EARLY_TICKS,
)

FORBIDDEN_SUBSTRINGS = [
    "w_late", "trajectory", "trajektoria", "beta", "slope", "nachylenie",
    "reduction", "redukcja", "delta", "trend",
]

# Dlugosc powyzej ktorej lista SAMYCH liczb jest podejrzana o niesienie
# trajektorii per-tick (prawdziwy przeciek mialby dlugosc rzedu W_EARLY_TICKS
# (60) albo TICKS_TOTAL (300); zaden legalny skalar/maly parametr w tym pliku
# nie ma wiecej niz kilku elementow).
MAX_ALLOWED_NUMERIC_LIST_LENGTH = 10


def _walk(obj, path=""):
    """Generator (path, key_or_index, value) dla kazdego wezla w strukturze."""
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
    """D-008 pkt 5 - test dziala niezaleznie od tego, czy pilot juz sie
    uruchomil (sprawdza same stale w kodzie runnera)."""

    def test_pilot_seeds_below_confirmatory_start(self):
        assert max(PILOT_SEEDS) < CONFIRMATORY_SEEDS_START, (
            f"seedy pilota {PILOT_SEEDS} nie sa rozlaczne z zakresem "
            f"konfirmacyjnym (od {CONFIRMATORY_SEEDS_START}) - pilot skazilby "
            f"eksperyment doslownie, nie tylko interpretacyjnie"
        )

    def test_confirmatory_seeds_start_is_1001(self):
        assert CONFIRMATORY_SEEDS_START == 1001

    def test_pilot_seeds_are_1_through_5(self):
        assert PILOT_SEEDS == [1, 2, 3, 4, 5]


class TestMechanicalGuaranteeOnOutputFile:

    def test_required_fields_present_and_correct(self, pilot_report):
        assert pilot_report["purpose"] == "power_analysis_only"
        assert pilot_report["NEVER_FOR_INFERENCE"] is True
        assert pilot_report["recorded_quantity"] == "W_early_only"
        assert pilot_report["seeds_used"] == PILOT_SEEDS
        assert pilot_report["confirmatory_seeds_start"] == CONFIRMATORY_SEEDS_START
        assert pilot_report["lesson"] == LESSON
        assert pilot_report["environments"] == ENVIRONMENTS

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
        """Jedyne dopuszczalne listy liczbowe to male parametry z gory
        (seeds_used=5 elementow, w_early_tick_window=2 elementy) - PONIZEJ
        progu podejrzanego o przeciek trajektorii per-tick (60/300 elementow)."""
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

    def test_runs_carry_only_w_early_scalar_not_trajectory(self, pilot_report):
        for run in pilot_report["runs"]:
            assert set(run.keys()) == {"genome_id", "environment", "seed", "w_early", "status"}
            assert run["w_early"] is None or isinstance(run["w_early"], (int, float))

    def test_n_runs_total_matches_23_genomes_x_5_seeds_x_2_environments(self, pilot_report):
        assert pilot_report["n_runs_total"] == 23 * 5 * 2 == 230
        assert len(pilot_report["runs"]) == 230


class TestRunnerSourceDoesNotPersistTrajectory:
    """Dodatkowe, statyczne zabezpieczenie (poza testem na pliku wyjsciowym):
    kod zrodlowy runnera nie powinien nigdzie wolac save_to_file() ani
    liczyc W_late/nachylenia."""

    def test_runner_source_never_calls_save_to_file(self):
        """Szuka RZECZYWISTEGO wywolania (`.save_to_file(` w kodzie, nie w
        docstringu/komentarzu, gdzie fraza wystepuje CELOWO - wyjasnia, ze
        NIE jest wolane). Docstringi (potrojne cudzyslowy) i linie-komentarze
        sa usuwane przed szukaniem."""
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_power_analysis.py").read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        code_lines = [
            line for line in no_docstrings.splitlines()
            if not line.strip().startswith("#")
        ]
        code_only = "\n".join(code_lines)
        assert ".save_to_file(" not in code_only, (
            "runner pilota faktycznie wola .save_to_file() w kodzie (poza "
            "docstringiem/komentarzem) - to zapisaloby snapshoty na dysk, "
            "wbrew gwarancji mechanicznej"
        )

    def test_runner_source_does_not_reference_w_late_or_trend(self):
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "pilot_power_analysis.py").read_text(encoding="utf-8")
        # Dopuszczamy odniesienia w komentarzach/docstringu WYJASNIAJACYCH,
        # ze te wielkosci sa CELOWO pomijane (np. "NIE liczy W_late") - test
        # sprawdza wiec brak jakiegokolwiek WYWOLANIA/PRZYPISANIA zwiazanego
        # z ta wielkoscia, nie brak samego slowa w prozie.
        forbidden_code_patterns = [
            re.compile(r"w_late\s*=", re.IGNORECASE),
            re.compile(r"\bslope\s*=", re.IGNORECASE),
            re.compile(r"\btrend\s*=", re.IGNORECASE),
        ]
        for pattern in forbidden_code_patterns:
            assert not pattern.search(source), (
                f"runner zawiera przypisanie pasujace do {pattern.pattern} - "
                "podejrzenie liczenia wielkosci spoza zakresu pilota"
            )
