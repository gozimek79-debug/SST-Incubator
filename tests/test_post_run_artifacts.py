"""Testy post-run (SPRINT v0.11.0 P2 KROK 2, CTO 2026-07-27).

"re-run konczy sie i laboratorium ma komplet pochodnych samo" - bez ani
jednej recznej komendy. Uzywa PRAWDZIWEGO pliku dry-run (207 mechanicznych
runow, execution_package_v0_11/results/dry_run_results.jsonl - juz na
dysku, wygenerowany BUILD-007) jako "maly zestaw" wejsciowy - NIE fixture
wymyslony na poczekaniu, i NIE re-run 12765. Wszystkie WYJSCIA przekierowane
do tmp_path - test nigdy nie dotyka prawdziwych plikow repo
(reports/population/population_validation_v0_11_0.json,
publications/competency_profile.json, reports/rerun_full_report_v0_11_0.md).
"""

import json
from pathlib import Path

import pytest

from execution_package_v0_11.runners.pipeline import (
    PostRunStageError,
    run_post_run_artifacts,
)

DRY_RUN_RESULTS = Path("execution_package_v0_11/results/dry_run_results.jsonl")


def _outputs(tmp_path):
    return {
        "population_out_path": tmp_path / "population_validation.json",
        "competency_output_dir": tmp_path / "publications",
        "report_out_path": tmp_path / "report.md",
    }


class TestEndToEndProducesAllThreeArtifacts:
    def test_all_three_files_created_from_dry_run_fixture(self, tmp_path):
        outs = _outputs(tmp_path)
        summary = run_post_run_artifacts(results_path=DRY_RUN_RESULTS, **outs)

        assert outs["population_out_path"].exists()
        assert (outs["competency_output_dir"] / "competency_profile.json").exists()
        assert (outs["competency_output_dir"] / "competency_profile.md").exists()
        assert outs["report_out_path"].exists()

        stage_names = [s["stage"] for s in summary["stages"]]
        assert stage_names == ["aggregate_results", "competency_profile", "report_composer"]

    def test_population_file_has_real_structure_from_dry_run_data(self, tmp_path):
        outs = _outputs(tmp_path)
        run_post_run_artifacts(results_path=DRY_RUN_RESULTS, **outs)

        with open(outs["population_out_path"], encoding="utf-8") as f:
            pop = json.load(f)
        assert pop["n_raw_records"] == 207
        assert "L1.1" in pop["lessons"] and "L1.2" in pop["lessons"]
        assert "noise_world" in pop["lessons"]["L1.1"]

    def test_competency_profile_reads_the_freshly_written_population_file(self, tmp_path):
        """Bez population_path override w write_competency_profile() profil
        czytalby CICHO z domyslnego (prawdziwego repo) pliku, nie z tego
        wlasnie co napisal etap 1 - dokladnie ten rodzaj rozjazdu, ktory ten
        sprint ma wyeliminowac. Test dowodzi, ze profil FAKTYCZNIE pochodzi
        z fixture (n=3 seedy/dry-run), nie z prawdziwego re-runu (n=185)."""
        outs = _outputs(tmp_path)
        run_post_run_artifacts(results_path=DRY_RUN_RESULTS, **outs)

        with open(outs["competency_output_dir"] / "competency_profile.json", encoding="utf-8") as f:
            profile = json.load(f)
        measured = [c for c in profile["concepts"] if c["status"] == "measured"]
        assert measured, "profil powinien miec zmierzone koncepty z danych dry-run"
        # n z dry-run (max 3 seedy/genom) - odrozniamy od prawdziwego re-runu (n=185).
        sample_n_values = {
            g["n"] for c in measured for g in c["genomes"].values()
        }
        assert sample_n_values, "brak wartosci n - profil nie doczytal per_genome"
        assert all(n <= 3 for n in sample_n_values), (
            f"profil ma n>3 ({sample_n_values}) - podejrzenie, ze czyta z prawdziwego "
            "repo zamiast z pliku dry-run wlasnie zapisanego przez etap 1"
        )

    def test_report_contains_dry_run_derived_numbers(self, tmp_path):
        outs = _outputs(tmp_path)
        run_post_run_artifacts(results_path=DRY_RUN_RESULTS, **outs)
        report_text = outs["report_out_path"].read_text(encoding="utf-8")
        assert "L1.1 / noise_world" in report_text
        assert "L1.2 / shock_world" in report_text
        assert "[kontrola-zdegenerowane]" in report_text


class TestIdempotency:
    def test_two_runs_produce_identical_output_except_timestamps(self, tmp_path):
        outs1 = _outputs(tmp_path / "run1")
        outs2 = _outputs(tmp_path / "run2")
        run_post_run_artifacts(results_path=DRY_RUN_RESULTS, **outs1)
        run_post_run_artifacts(results_path=DRY_RUN_RESULTS, **outs2)

        pop1 = json.loads(outs1["population_out_path"].read_text(encoding="utf-8"))
        pop2 = json.loads(outs2["population_out_path"].read_text(encoding="utf-8"))
        assert pop1 == pop2, "population_validation nie niesie zadnego pola czasowego - musi byc bajtowo identyczny"

        prof1 = json.loads((outs1["competency_output_dir"] / "competency_profile.json").read_text(encoding="utf-8"))
        prof2 = json.loads((outs2["competency_output_dir"] / "competency_profile.json").read_text(encoding="utf-8"))
        prof1.pop("generated_at", None)
        prof2.pop("generated_at", None)
        assert prof1 == prof2, "profil poza 'generated_at' musi byc identyczny na tych samych danych"

        # Dwie linie niosa czas generacji: naglowek raportu ("Wygenerowany...")
        # i echo profilu w tabeli metadanych ("profil.generated_at | ...") -
        # odfiltrowane PO TRESCI (nie po sztywnym indeksie linii), reszta
        # raportu (wszystkie tabele/liczby z population+profil) musi byc identyczna.
        def _stable_lines(text):
            return [
                line for line in text.splitlines()
                if "Wygenerowany" not in line and "generated_at" not in line
            ]

        report1 = outs1["report_out_path"].read_text(encoding="utf-8")
        report2 = outs2["report_out_path"].read_text(encoding="utf-8")
        assert _stable_lines(report1) == _stable_lines(report2)


class TestOrderEnforcedAndFailureIsExplicit:
    def test_missing_results_file_blocks_stage_2_and_3(self, tmp_path):
        outs = _outputs(tmp_path)
        missing = tmp_path / "does_not_exist.jsonl"

        with pytest.raises(PostRunStageError) as exc_info:
            run_post_run_artifacts(results_path=missing, **outs)

        assert "ETAP 1/3" in str(exc_info.value)
        assert "aggregate_results" in str(exc_info.value)
        # Etapy 2/3 NIE mialy prawa odpalic sie na (nieistniejacych) starych danych.
        assert not outs["population_out_path"].exists()
        assert not (outs["competency_output_dir"] / "competency_profile.json").exists()
        assert not outs["report_out_path"].exists()

    def test_stage_error_is_not_silently_swallowed(self, tmp_path):
        """RuntimeError/PostRunStageError musi PROPAGOWAC, nie byc zlapany i
        zignorowany gdzies wewnatrz run_post_run_artifacts."""
        outs = _outputs(tmp_path)
        with pytest.raises(PostRunStageError):
            run_post_run_artifacts(results_path=tmp_path / "nope.jsonl", **outs)


class TestExploratoryArchiveGuardStillFiresInPostRun:
    """CTO 2026-07-27: 'guardy w competency_profile juz to pilnuja - sprawdz,
    ze dzialaja w tym trybie' - NIE zakladac, sprawdzic empirycznie ze
    archive_exploratory_profile() (wolane wewnatrz write_competency_profile,
    wolane wewnatrz run_post_run_artifacts) faktycznie odpala sie i
    zachowuje stara zawartosc, gdy post-run trafia na 'pierwsze przejscie'
    Exploratory->Confirmatory w danym katalogu wyjsciowym."""

    def test_pre_existing_exploratory_profile_gets_archived_not_overwritten_in_place(self, tmp_path):
        outs = _outputs(tmp_path)
        competency_dir = outs["competency_output_dir"]
        competency_dir.mkdir(parents=True)

        exploratory_json = {
            "dataset_status": "Exploratory Dataset v0.10 (n=10, 2 genomy) - stan sprzed re-runu",
            "generated_at": "2020-01-01T00:00:00",
            "marker": "TO_JEST_STARA_TRESC_EXPLORATORY",
        }
        (competency_dir / "competency_profile.json").write_text(
            json.dumps(exploratory_json), encoding="utf-8"
        )
        (competency_dir / "competency_profile.md").write_text(
            "# stara wersja exploratory\n", encoding="utf-8"
        )

        run_post_run_artifacts(results_path=DRY_RUN_RESULTS, **outs)

        archive_json_path = competency_dir / "competency_profile_v0_10_1_exploratory.json"
        assert archive_json_path.exists(), "archiwum nie powstalo - guard nie odpalil sie w tym trybie"
        archived = json.loads(archive_json_path.read_text(encoding="utf-8"))
        assert archived["marker"] == "TO_JEST_STARA_TRESC_EXPLORATORY"

        live = json.loads((competency_dir / "competency_profile.json").read_text(encoding="utf-8"))
        assert live["dataset_status"].startswith("CONFIRMATORY"), (
            "zywy plik powinien zostac nadpisany danymi konfirmacyjnymi z tego re-runu"
        )
        assert "marker" not in live


class TestEachStageIndependentlyCallable:
    """post-run to DODATKOWY wyzwalacz - kazdy generator zostaje uzywalny z
    wlasnego CLI (python -m ...) dokladnie jak przed tym krokiem."""

    def test_aggregate_results_write_report_still_directly_callable(self, tmp_path):
        from execution_package_v0_11.runners.aggregate_results import write_report as aggregate_write_report

        out = tmp_path / "direct_population.json"
        result = aggregate_write_report(results_path=DRY_RUN_RESULTS, out_path=out)
        assert result == out and out.exists()

    def test_write_competency_profile_still_directly_callable_with_default_population(self, tmp_path):
        from clos_scientist.competency_profile import write_competency_profile

        paths = write_competency_profile(output_dir=tmp_path)
        assert paths["json"].exists() and paths["md"].exists()

    def test_report_composer_write_report_still_directly_callable(self, tmp_path):
        from scripts.report_composer import write_report as compose_write_report

        out = compose_write_report(out_path=tmp_path / "direct_report.md")
        assert out.exists()
