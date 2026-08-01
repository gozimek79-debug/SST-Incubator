"""PC-001 W-01 (D-025 pkt 1): test GWARANCJI MECHANICZNEJ, analogicznie do
tests/test_pilot_power_analysis_guarantee.py / test_pilot_w2_power_analysis_
guarantee.py. SCISLEJSZE ograniczenie raportowania niz przy W_early_red
(D-025, ograniczenie CTO): WYLACZNIE mediana/IQR/max + liczniki agregatowe
(n_censored/n_censored_at_ceiling/itd.) - ZERO wartosci per-genom, ZERO listy
przebiegow (w odroznieniu od pilot_PE_distribution_W_early.json /
pilot_W_early_red_noise_world.json, ktore MIALY liste "runs")."""

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "execution_package_v0_11"))
sys.path.insert(0, str(REPO_ROOT))

from runners.w01_recovery_1_measurement import (  # noqa: E402
    SEEDS, OUTPUT_PATH, ENVIRONMENT, LESSON, INTERVAL, N_SUSTAIN,
    first_shock_tick,
)


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield (path, k, v)
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


@pytest.fixture(scope="module")
def w01_report():
    if not OUTPUT_PATH.exists():
        pytest.skip(f"W-01 jeszcze nie uruchomiony - brak {OUTPUT_PATH}")
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestMechanicalGuaranteeStricterThanWEarlyRed:
    """D-025: 'NIE raportuj wartosci per genom ani per przebieg' - scislejsze
    niz W_early_red pilotow, ktore MIALY liste per-run (bo tam bylo to
    dopuszczalne). Tutaj NIE MA zadnej listy/struktury per-genom/per-run w
    ogole - tylko skalary zbiorcze."""

    def test_no_runs_list_or_per_genome_breakdown(self, w01_report):
        forbidden_keys = {"runs", "by_genome", "genome_id", "seed_results",
                           "per_genome", "per_run", "recoveries"}
        present = forbidden_keys & set(w01_report.keys())
        assert not present, (
            f"raport zawiera klucze niosace dane per-genom/per-przebieg: {present} "
            "- D-025 wymaga WYLACZNIE zbiorczych statystyk"
        )

    def test_no_list_values_anywhere_except_seeds_used(self, w01_report):
        """Jedyna dozwolona lista w calym raporcie to seeds_used (staly,
        maly parametr z gory) - wszystko inne musi byc skalarem."""
        violations = []
        for path, key, value in _walk(w01_report):
            if isinstance(value, list) and key != "seeds_used":
                violations.append(f"'{path}.{key}' jest lista (niedozwolone poza seeds_used)")
        assert not violations, "\n".join(violations)

    def test_required_fields_present(self, w01_report):
        assert w01_report["purpose"] == "power_analysis_only"
        assert w01_report["NEVER_FOR_INFERENCE"] is True
        assert w01_report["recorded_quantity"] == "recovery_1_summary_only"
        assert w01_report["seeds_used"] == SEEDS
        assert w01_report["environment"] == ENVIRONMENT
        assert w01_report["interval"] == INTERVAL
        assert w01_report["lesson"] == LESSON
        assert w01_report["n_sustain"] == N_SUSTAIN
        for key in ("median", "q1", "q3", "max", "n_censored", "n_non_censored",
                    "censoring_rate", "n_censored_at_ceiling", "interpretation"):
            assert key in w01_report, f"brak wymaganego pola '{key}'"

    def test_censoring_counts_are_internally_consistent(self, w01_report):
        assert (w01_report["n_censored"] + w01_report["n_non_censored"]
                == w01_report["n_runs_total"])
        assert (w01_report["n_censored_at_ceiling"] + w01_report["n_censored_at_floor"]
                + w01_report["n_censored_other"] == w01_report["n_censored"])

    def test_n_runs_total_matches_23_genomes_x_3_seeds(self, w01_report):
        assert w01_report["n_runs_total"] == 23 * 3 == 69


class TestInterpretationReflectsCensoringRateNotJustMedian:
    """Znalezisko wykonawcy: interpretation MUSI byc zdominowana przez wysoki
    odsetek cenzurowania, nie tylko przez median-of-survivors (survivorship
    bias) - test negatywny odtwarzajacy dokladnie ten blad."""

    def test_interpretation_flags_infeasible_when_censoring_high(self, w01_report):
        if w01_report["censoring_rate"] is not None and w01_report["censoring_rate"] > 0.30:
            assert "NIEWYKONALNE" in w01_report["interpretation"], (
                "cenzurowanie > 30%, ale interpretation nie flaguje K3b jako "
                "niewykonalne - podejrzenie ze interpretation patrzy tylko na "
                "median-of-survivors (blad survivorship bias)"
            )
            assert "survivorship" in w01_report["interpretation"].lower() or \
                   "cenzurowania" in w01_report["interpretation"].lower() or \
                   "bias" in w01_report["interpretation"].lower(), (
                "interpretation nie tlumaczy CZEMU mediana jest myslaca przy "
                "wysokim cenzurowaniu"
            )

    def test_build_report_negative_case_median_of_survivors_alone_would_mislead(self):
        """Test NEGATYWNY (wzorzec 'implementacja ktora nie odejmuje' z W2):
        symulowany zestaw z 90% cenzurowaniem i mala mediana wsrod survivorow
        MUSI dac interpretation z 'NIEWYKONALNE', nie 'wykonalne z zapasem' -
        gdyby build_report patrzyl tylko na median, ten test by to zlapal."""
        import runners.w01_recovery_1_measurement as w01

        synthetic_records = (
            [{"value": 5.0, "censor_reason": None}] * 2
            + [{"value": None, "censor_reason": "ceiling"}] * 18
        )
        report = w01.build_report(synthetic_records)
        assert report["median"] == 5.0  # mala mediana wsrod survivorow...
        assert "NIEWYKONALNE" in report["interpretation"], (
            "przy 90% cenzurowaniu i malej mediana-wsrod-survivorow, "
            "interpretation MUSI ostrzec o niewykonalnosci, nie chwalic malej mediany"
        )


class TestFirstShockTickDerivation:
    """Krzyzowa weryfikacja: first_shock_tick() MUSI dokladnie odtwarzac
    pierwsze losowanie recurring_shock_world (clos_world/scenarios.py:60)."""

    def test_matches_scenario_offset_directly(self):
        import random
        from clos_world.scenarios import recurring_shock_world
        for seed in [1, 2, 3, 4, 5, 42, 1001]:
            expected_offset = random.Random(seed).randint(0, INTERVAL - 1)
            assert first_shock_tick(seed) == expected_offset

    def test_shock_tick_produces_shock_magnitude_range(self):
        """Empiryczna proba niezaleznosci: recurring_shock_world(t_shock_1, seed)
        MUSI byc w zakresie magnitude wstrzasu [0.6, 0.95], NIE w zakresie
        bazowym ~0.2 - dowod, ze first_shock_tick() faktycznie trafia w
        wstrzas, nie w przypadkowy inny tick."""
        from clos_world.scenarios import recurring_shock_world
        for seed in [1, 2, 3, 4, 5]:
            t = first_shock_tick(seed)
            value_at_shock = recurring_shock_world(t, seed)
            assert 0.6 <= value_at_shock <= 0.95, (
                f"seed={seed}: recurring_shock_world(t_shock_1={t}, seed)={value_at_shock} "
                f"poza zakresem magnitude wstrzasu [0.6,0.95] - first_shock_tick() "
                f"prawdopodobnie nie trafia we wlasciwy tick"
            )

    def test_tick_immediately_before_shock_is_not_shock_range(self):
        """Jesli t_shock_1 > 0, poprzedni tick powinien byc w bazowym pasmie
        (~0.2 + szum), NIE w zakresie magnitude wstrzasu - odrozniajaca kontrola."""
        from clos_world.scenarios import recurring_shock_world
        checked_any = False
        for seed in [1, 2, 3, 4, 5]:
            t = first_shock_tick(seed)
            if t > 0:
                checked_any = True
                value_before = recurring_shock_world(t - 1, seed)
                assert value_before < 0.6, (
                    f"seed={seed}: tick tuz przed domniemanym pierwszym wstrzasem "
                    f"ma wartosc {value_before} w zakresie magnitude - t_shock_1 "
                    f"moze byc zle wyznaczony (off-by-one?)"
                )
        assert checked_any, "zaden z testowanych seedow nie mial t_shock_1>0 - test nie sprawdzil niczego"


class TestRunnerSourceDoesNotPersistTrajectory:

    def test_runner_source_never_calls_save_to_file(self):
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "w01_recovery_1_measurement.py").read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        code_lines = [line for line in no_docstrings.splitlines()
                      if not line.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        assert ".save_to_file(" not in code_only

    def test_runner_reuses_existing_compute_recovery_time_not_reimplementing(self):
        """DRY-gwarancja: formula recovery_time NIE jest duplikowana - runner
        importuje compute_recovery_time z lesson_L1_2.py (juz przetestowany
        kod), nie pisze wlasnej wersji."""
        source = (REPO_ROOT / "execution_package_v0_11" / "runners"
                  / "w01_recovery_1_measurement.py").read_text(encoding="utf-8")
        assert "from clos_academy.lesson_L1_2 import" in source
        assert "compute_recovery_time" in source
