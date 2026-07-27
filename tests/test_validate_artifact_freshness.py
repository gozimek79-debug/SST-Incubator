"""Testy Validate Artifact Freshness (SPRINT v0.11.0 P2 KROK 3, CTO 2026-07-27).

Konwencja projektu (patrz P0 - alias 'comparison' dal zielony walidator,
ktory NIC nie chronil): kazdy test pozytywny (real dane -> PASS) musi miec
PAROWY test negatywny (zepsuta liczba -> FAIL), inaczej nie wiadomo, czy
walidator cokolwiek sprawdza.
"""

import json
from pathlib import Path

from scripts.validate_artifact_freshness import (
    ANALYSIS_REPORT_PATH,
    COMPETENCY_PROFILE_PATH,
    METRIC_STATUS_TABLE_PATH,
    POPULATION_PATH,
    build_source_lookup,
    check_analysis_report,
    check_competency_profile,
    check_metric_status_table,
    parse_analysis_report_rows,
    parse_metric_status_table_rows,
)


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


REAL_POPULATION = _load(POPULATION_PATH)
REAL_SOURCE = build_source_lookup(REAL_POPULATION)
REAL_TABLE_TEXT = METRIC_STATUS_TABLE_PATH.read_text(encoding="utf-8")
REAL_PROFILE = _load(COMPETENCY_PROFILE_PATH)
REAL_REPORT_TEXT = ANALYSIS_REPORT_PATH.read_text(encoding="utf-8")

# Working Memory / L1.1 / noise_world = 69/253 - zweryfikowane niezaleznie
# wielokrotnie w tym sprincie (P0, panel #6/#8) - bezpieczna kotwica do
# testu negatywnego (wiemy na pewno, ze prawdziwa wartosc to NIE 0/253).
WM_REAL_TOKEN = "Welch-pary (69/253, 27%)"
WM_BROKEN_TOKEN = "Welch-pary (0/253, 27%)"


class TestBuildSourceLookup:
    def test_known_cells_present_with_correct_values(self):
        assert REAL_SOURCE[("L1.1", "noise_world", "Working Memory (MAE@50)")] == (69, 253)
        assert REAL_SOURCE[("L1.1", "noise_world", "Pattern Recognition")] == (77, 253)
        assert REAL_SOURCE[("L1.1", "noise_world", "Pattern Retention")] == (0, 253)
        assert REAL_SOURCE[("L1.1", "noise_world", "Stability")] == (244, 253)

    def test_drift_world_absent_from_source(self):
        """Architekt potwierdzil: drift_world NIE ISTNIEJE w danych v0.11 -
        zaden klucz z tym srodowiskiem nie powinien byc w source lookup."""
        assert not any(env == "drift_world" for (_, env, _) in REAL_SOURCE)


class TestMetricStatusTableParsing:
    def test_parses_known_row_count_for_measured_axes_table(self):
        rows = parse_metric_status_table_rows(REAL_TABLE_TEXT)
        # 4b to 30 wierszy (7 osi x do 3 srodowisk, gdzie dotyczy) - patrz
        # docs/METRIC_STATUS_TABLE.md SS5. Nie zaklada dokladnej liczby (moze
        # sie zmienic), tylko ze parser znajduje WIELE wierszy, nie 0/1.
        assert len(rows) >= 25

    def test_does_not_bleed_into_not_measured_table_4a(self):
        """SS4a (Perception/Attention/...) ma INNY ksztalt kolumn (8, nie 11) -
        parser MUSI go pominac, inaczej indeksy kolumn (Test=10) czytalyby
        zle pole z zupelnie innej tabeli."""
        rows = parse_metric_status_table_rows(REAL_TABLE_TEXT)
        names = {r["metric"] for r in rows}
        assert "Perception" not in names
        assert "Attention" not in names


class TestMetricStatusTableCheckPositiveAndNegative:
    """Konwencja projektu: kazdy pozytywny test ma parowy negatywny."""

    def test_real_working_memory_row_matches_source(self):
        assert WM_REAL_TOKEN in REAL_TABLE_TEXT, "kotwica testu zniknela z tabeli - zaktualizuj token"
        violations, _ = check_metric_status_table(REAL_TABLE_TEXT, REAL_SOURCE)
        wm_violations = [v for v in violations if "noise_world/Working Memory" in v]
        assert wm_violations == []

    def test_NEGATIVE_corrupted_working_memory_number_is_caught(self):
        broken_text = REAL_TABLE_TEXT.replace(WM_REAL_TOKEN, WM_BROKEN_TOKEN)
        assert broken_text != REAL_TABLE_TEXT, "podmiana nie zadzialala - token nie znaleziony w tabeli"

        violations, _ = check_metric_status_table(broken_text, REAL_SOURCE)
        wm_violations = [v for v in violations if "noise_world/Working Memory" in v]
        assert len(wm_violations) == 1
        assert "0/253" in wm_violations[0]
        assert "69/253" in wm_violations[0]

    def test_NEGATIVE_restoring_the_number_passes_again(self):
        broken_text = REAL_TABLE_TEXT.replace(WM_REAL_TOKEN, WM_BROKEN_TOKEN)
        restored_text = broken_text.replace(WM_BROKEN_TOKEN, WM_REAL_TOKEN)
        violations, _ = check_metric_status_table(restored_text, REAL_SOURCE)
        wm_violations = [v for v in violations if "noise_world/Working Memory" in v]
        assert wm_violations == []

    def test_drift_world_rows_reported_as_info_not_violation(self):
        violations, info = check_metric_status_table(REAL_TABLE_TEXT, REAL_SOURCE)
        assert not any("drift_world" in v for v in violations), (
            "drift_world nie istnieje w population_validation - MUSI byc pominiete, nie FAIL"
        )
        assert any("drift_world" in i for i in info)

    def test_pattern_retention_zero_is_not_flagged_as_error(self):
        """UWAGA z zadania: 0/253 dla Pattern Retention/noise jest POPRAWNE -
        walidator NIE MOZE zakladac 'zero = blad'."""
        violations, _ = check_metric_status_table(REAL_TABLE_TEXT, REAL_SOURCE)
        assert not any("Pattern Retention" in v and "noise_world" in v for v in violations)


class TestCompetencyProfileCheckPositiveAndNegative:
    def test_real_profile_working_memory_matches_source(self):
        violations, _ = check_competency_profile(REAL_PROFILE, REAL_SOURCE)
        assert not any("Working Memory" in v for v in violations)

    def test_NEGATIVE_corrupted_profile_number_is_caught(self):
        broken = json.loads(json.dumps(REAL_PROFILE))
        for c in broken["concepts"]:
            if c["concept"] == "Working Memory" and c.get("source_lesson") == "L1.1/noise_world":
                c["genome_comparison"]["n_fdr_significant_q_0_05"] = 0
        violations, _ = check_competency_profile(broken, REAL_SOURCE)
        wm_violations = [v for v in violations if "Working Memory" in v]
        assert len(wm_violations) == 1
        assert "0/253" in wm_violations[0] and "69/253" in wm_violations[0]


class TestAnalysisReportParsingAndCheck:
    def test_parses_lesson_env_sections(self):
        rows = parse_analysis_report_rows(REAL_REPORT_TEXT)
        keys = {(r["lesson"], r["env"]) for r in rows}
        assert ("L1.1", "noise_world") in keys
        assert ("L1.2", "shock_world") in keys

    def test_real_report_working_memory_matches_source(self):
        violations, _ = check_analysis_report(REAL_REPORT_TEXT, REAL_SOURCE)
        assert not any("Working Memory" in v for v in violations)

    def test_NEGATIVE_corrupted_report_number_is_caught(self):
        broken_text = REAL_REPORT_TEXT.replace(
            "| Working Memory (MAE@50) | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 69/253 | 95 | f=0.1537 |",
            "| Working Memory (MAE@50) | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 0/253 | 95 | f=0.1537 |",
        )
        assert broken_text != REAL_REPORT_TEXT, "wzorzec linii nie znaleziony w raporcie - zaktualizuj test"
        violations, _ = check_analysis_report(broken_text, REAL_SOURCE)
        wm_violations = [v for v in violations if "Working Memory" in v]
        assert len(wm_violations) == 1
        assert "0/253" in wm_violations[0] and "69/253" in wm_violations[0]


class TestSyntheticFixtureFullMechanics:
    """Kontrolowane, syntetyczne dane (nie zywy repo) - dowod mechaniki
    niezalezny od tresci prawdziwych dokumentow, ktora moze sie zmienic."""

    def _fixture_population(self):
        return {
            "lessons": {
                "L1.1": {
                    "noise_world": {
                        "Widget (unit)": {
                            "pairwise_comparisons": {"n_fdr_significant_q_0_05": 10, "n_pairs": 253}
                        }
                    }
                }
            }
        }

    def test_matching_number_passes(self):
        source = build_source_lookup(self._fixture_population())
        table = (
            "| Lekcja | Środ. | Metryka | Definicja (skrót) | Interpretacja biologiczna | Measurement | Construct | Power | Confirm. | Test | Rekomendacja |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| L1.1 | noise_world | Widget | jw | jw | ✔ | ◐ | CONFIRMED | CONFIRMED | Welch-pary (10/253) | **VALIDATED** |\n"
        )
        violations, info = check_metric_status_table(table, source)
        assert violations == []
        assert info == []

    def test_NEGATIVE_mismatching_number_fails(self):
        source = build_source_lookup(self._fixture_population())
        table = (
            "| Lekcja | Środ. | Metryka | Definicja (skrót) | Interpretacja biologiczna | Measurement | Construct | Power | Confirm. | Test | Rekomendacja |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| L1.1 | noise_world | Widget | jw | jw | ✔ | ◐ | CONFIRMED | CONFIRMED | Welch-pary (11/253) | **VALIDATED** |\n"
        )
        violations, info = check_metric_status_table(table, source)
        assert len(violations) == 1
        assert "11/253" in violations[0] and "10/253" in violations[0]

    def test_out_of_scope_row_is_info_only(self):
        source = build_source_lookup(self._fixture_population())
        table = (
            "| Lekcja | Środ. | Metryka | Definicja (skrót) | Interpretacja biologiczna | Measurement | Construct | Power | Confirm. | Test | Rekomendacja |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| L1.1 | drift_world | Widget | jw | jw | ✔ | ◐ | PENDING | PENDING | Welch-pary (5/99) | **INSUFFICIENT_POWER** |\n"
        )
        violations, info = check_metric_status_table(table, source)
        assert violations == []
        assert len(info) == 1
