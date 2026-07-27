"""Testy Report Composer (SPRINT v0.11.0, KROK 1 P2, CTO 2026-07-26).

Gwarancja "liczby w pliku == liczby na ekranie": panel i generator czytaja
TEN SAM population_validation_v0_11_0.json / competency_profile.json, wiec
test sprawdza, ze KAZDA liczba w raporcie da sie odtworzyc ze zrodla (echo,
zero osobnego liczenia) - oraz ze generator jest samodzielny (auto-discovery:
nowa lekcja pojawia sie bez zmiany kodu) i oznacza kontrole.
"""

import json
from pathlib import Path

from scripts.report_composer import compose_report, write_report

POP_PATH = Path("reports/population/population_validation_v0_11_0.json")
PROF_PATH = Path("publications/competency_profile.json")


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


class TestReportEchoesSourceNumbers:
    def test_fdr_pairs_match_population_exactly(self):
        pop = _load(POP_PATH)
        prof = _load(PROF_PATH)
        report = compose_report(pop, prof)
        # Kazda komorka (lekcja x srodowisko x metryka) z niepustymi parami MUSI
        # pojawic sie w raporcie DOKLADNIE jako n_fdr/n_pairs ze zrodla - to
        # jest niezmiennik "liczby w pliku == liczby na ekranie" (panel czyta
        # to samo pole, patrz renderPopulationMetricRow w panel.js).
        for lesson in pop["lessons"].values():
            for env in lesson.values():
                for entry in env.values():
                    pc = entry.get("pairwise_comparisons") or {}
                    if pc.get("n_pairs") is None:
                        continue
                    token = f"{pc['n_fdr_significant_q_0_05']}/{pc['n_pairs']}"
                    assert token in report, token

    def test_known_headline_numbers_present(self):
        """Kotwica na konkretne, wielokrotnie weryfikowane liczby (WM/PatRec/
        PatRet/Stability z L1.1/noise) - gdyby generator zaczal cokolwiek
        przeliczac, ten test zlapie rozjazd z surowym plikiem."""
        report = compose_report(_load(POP_PATH), _load(PROF_PATH))
        for token in ["69/253", "77/253", "0/253", "244/253", "204/253"]:
            assert token in report, token

    def test_metadata_echoed(self):
        pop = _load(POP_PATH)
        report = compose_report(pop, _load(PROF_PATH))
        assert pop["git_commit"] in report
        assert pop["hard_halt_baseline"] in report
        assert str(pop["n_raw_records"]) in report


class TestControlEnvironmentsMarked:
    def test_stable_world_sections_carry_control_marker(self):
        pop = _load(POP_PATH)
        report = compose_report(pop, _load(PROF_PATH))
        # Kazda lekcja majaca stable_world dostaje naglowek z markerem kontroli.
        for lesson_key, lesson in pop["lessons"].items():
            if "stable_world" in lesson:
                assert f"### {lesson_key} / stable_world [kontrola-zdegenerowane]" in report


class TestProfileSection:
    def test_minimal_validated_axes_present(self):
        prof = _load(PROF_PATH)
        report = compose_report(_load(POP_PATH), prof)
        for axis in prof["minimal_profile"]["axes"]:
            assert axis in report

    def test_all_14_concepts_listed(self):
        prof = _load(PROF_PATH)
        report = compose_report(_load(POP_PATH), prof)
        for c in prof["concepts"]:
            assert c["concept"] in report


class TestAutoDiscovery:
    def test_injected_lesson_appears_without_code_change(self):
        """Fundament pod P2: dodanie lekcji do danych pojawia sie w raporcie
        bez dotykania report_composer.py (ten sam wzorzec Object.keys co panel
        #3). Wstrzykniecie fikcyjnej L9.9 do KOPII danych (zrodlo nietkniete)."""
        pop = _load(POP_PATH)
        pop = json.loads(json.dumps(pop))
        pop["lessons"]["L9.9"] = {
            "weird_world": {
                "Totally New Metric": {
                    "status": "measured",
                    "classification": "GENOME-ROBUST",
                    "valid_rate": 1.0,
                    "n_genomes_total": 23,
                    "n_genomes_valid": 23,
                    "per_genome": {"pop_000": {"n": 5, "mean": 1.0, "ci95_low": 0.9,
                                               "ci95_high": 1.1, "n_effective": 5, "ci95_valid": True}},
                    "omnibus_anova_raw": {"computable": True, "f": 0.42},
                    "pairwise_comparisons": {"n_pairs": 253, "n_fdr_significant_q_0_05": 12,
                                             "n_raw_significant_p_lt_0_05": 20},
                }
            }
        }
        report = compose_report(pop, _load(PROF_PATH))
        assert "### L9.9 / weird_world" in report
        assert "Totally New Metric" in report
        assert "12/253" in report


class TestWrite:
    def test_write_report_creates_md(self, tmp_path):
        out = tmp_path / "report.md"
        result = write_report(POP_PATH, PROF_PATH, out)
        assert result == out
        assert out.exists()
        assert out.read_text(encoding="utf-8").startswith("# Raport re-runu konfirmacyjnego v0.11.0")
