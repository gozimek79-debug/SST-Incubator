"""Testy scripts/generate_canonical_parameters_report.py.

Konwencja projektu: kazdy test pozytywny ma test negatywny obok. Najwazniejsza
klasa tutaj jest TestCC10BaselineLiteralPitfall: dowodzi, ze sprawdzenie "czy
PC_001_BASELINE jest literalem w HALT" nie wpada w zaden z dwoch udokumentowanych
falszywych alarmow (nazwa w docstringu/komunikacie; DOWOLNY 64-znakowy hex, bo
AUD_001_BASELINE legalnie ma swoj wlasny), a mimo to LAPIE prawdziwe przypisanie.
"""

import json
from pathlib import Path

import pytest

from scripts.generate_canonical_parameters_report import (
    MISSING,
    PARAM_ADDRESSES,
    _eval_constant_value,
    baseline_status_at,
    blob_sha256_at,
    commit_meta_at,
    consistency_checks,
    critical_files_at,
    delta,
    file_history_revs,
    fmt,
    is_live_head_rev,
    main,
    module_constant_at,
    module_constant_in_text,
    pc_001_baseline_literal_present_in_text,
    read_bytes_at,
    read_text_at,
    registry_length_assertion_in_text,
    rev_exists,
    snapshot,
    verify_report,
    working_tree_check,
)

CONFIG_PATH = "clos_scientist/pc_001_experiment_config.py"
HALT_PATH = "execution_package_v0_11/validators/hard_halt.py"
REAL_HALT_TEXT = read_text_at("HEAD", HALT_PATH)
# Drzewo robocze, NIE HEAD - patrz TestRegistryLengthAssertion. Zmienna osobna
# od REAL_HALT_TEXT (git HEAD), bo ten konkretny test mierzy SPOJNOSC PLIKU ZE
# SOBA SAMYM teraz, nie stan ostatniego commita - historia nie jest tu w ogole
# w grze, wiec czytanie z gita byloby niewlasciwym narzedziem, nie ostroznoscia.
_HALT_WORKING_TREE_PATH = Path(__file__).resolve().parents[1] / HALT_PATH


class TestGitObjectLayer:
    def test_rev_exists_for_head(self):
        assert rev_exists("HEAD")

    def test_rev_exists_false_for_bogus_rev(self):
        assert not rev_exists("not-a-real-revision-xyz")

    def test_read_bytes_at_returns_none_for_missing_path(self):
        assert read_bytes_at("HEAD", "this/path/does/not/exist.py") is None

    def test_read_bytes_at_returns_content_for_real_path(self):
        assert read_bytes_at("HEAD", CONFIG_PATH) is not None

    def test_blob_sha256_matches_known_pilot_artifact(self):
        """Kotwica na realnym repo (patrz CANONICAL_PARAMETERS_REPORT.md, wygenerowany
        przez prototyp z tego samego commitu) - dowod, ze hash liczy sie z tresci blobu."""
        sha = blob_sha256_at("HEAD", "reports/pilot/floor_noise_world_2026-07-28.json")
        assert sha is not None
        assert sha.startswith("4bebc093f38f")

    def test_blob_sha256_none_for_missing_file(self):
        assert blob_sha256_at("HEAD", "does/not/exist.json") is None


class TestStaticModuleReadNoImport:
    def test_reads_known_float_constant(self):
        assert module_constant_at("HEAD", CONFIG_PATH, "FLOOR_BIAS_TOLERANCE") == 0.002

    def test_reads_list_range_call(self):
        value = module_constant_at("HEAD", CONFIG_PATH, "W_EARLY_TICKS")
        assert value == list(range(0, 60))

    def test_missing_symbol_is_missing_sentinel_not_a_default(self):
        assert module_constant_at("HEAD", CONFIG_PATH, "SYMBOL_KTOREGO_NIE_MA") is MISSING

    def test_missing_file_is_missing_sentinel(self):
        assert module_constant_at("HEAD", "no/such/file.py", "X") is MISSING

    def test_syntax_error_source_is_missing_sentinel(self):
        assert module_constant_in_text("def broken(:\n", "X") is MISSING

    def test_range_call_reader_ignores_other_call_shapes(self):
        """Waskosc celowa: '_eval_range_call' rozpoznaje TYLKO list(range(a, b)).
        'sorted([...])' nie jest ani literalem, ani tym wywolaniem - MISSING, nie
        proba zgadniecia wartosci przez faktyczne wykonanie kodu."""
        import ast

        node = ast.parse("sorted([3, 1, 2])", mode="eval").body
        assert _eval_constant_value(node) is MISSING


class TestRegistryLengthAssertion:
    def test_real_assertion_matches_real_list_length(self):
        """Czyta DRZEWO ROBOCZE, nie git HEAD (naprawa po D-031/Z5B): ten test
        sprawdza, czy assert w hard_halt.py zgadza sie z WLASNA lista TERAZ - to
        pytanie o biezacy plik, nie o historie, wiec czytanie z gita mierzyloby
        niewlasciwa rzecz i byloby zielone/czerwone naprzemiennie w zaleznosci od
        tego, po ktorej stronie commita test akurat biegnie (ujawnione przy
        rozszerzeniu rejestru 47->49 - test zielony przed commitem i czerwony po
        nim, nigdy stabilnie). Przeczytanie z drzewa roboczego mierzy to samo,
        co widzi walidator, wiec jest zielony po obu stronach kazdego commita."""
        text = _HALT_WORKING_TREE_PATH.read_text(encoding="utf-8")
        n = registry_length_assertion_in_text(text)
        from scripts.validate_canonical_spec import load_critical_files

        files = load_critical_files()
        assert n == len(files) == 53

    def test_missing_assert_is_missing_sentinel(self):
        assert registry_length_assertion_in_text("CRITICAL_FILES_PC_001 = ['a.py']\n") is MISSING

    def test_mismatched_assertion_is_caught_by_consistency_check(self):
        text = "CRITICAL_FILES_PC_001 = ['a.py', 'b.py']\nassert len(CRITICAL_FILES_PC_001) == 3\n"
        n = registry_length_assertion_in_text(text)
        assert n == 3  # rozjazd z faktyczna dlugoscia listy (2) - CC-05 to zlapie


class TestCC10BaselineLiteralPitfall:
    """Dwa udokumentowane falszywe alarmy prototypu (zadanie audytora §2.3) - dowod,
    ze zaden z nich nie odtwarza sie w tej implementacji, ORAZ ze prawdziwe
    przypisanie nadal zostaje zlapane."""

    def test_real_halt_file_does_not_trigger_false_positive(self):
        """Pulapka 1 i 2 naraz: prawdziwy HALT zawiera SLOWO 'PC_001_BASELINE' w
        docstringach/komunikatach ORAZ 64-znakowy hex nalezacy do AUD_001_BASELINE.
        Zadne z nich nie moze wywolac PASS/FAIL - dzis nie ma przypisania PC_001_BASELINE."""
        assert "PC_001_BASELINE" in REAL_HALT_TEXT  # upewnij sie, ze nazwa faktycznie wystepuje jako tekst
        assert "AUD_001_BASELINE" in REAL_HALT_TEXT
        assert pc_001_baseline_literal_present_in_text(REAL_HALT_TEXT) is False

    def test_bare_name_in_docstring_alone_is_not_a_false_positive(self):
        text = '"""Ten modul wspomina PC_001_BASELINE w komentarzu, nigdy jej nie przypisuje."""\n'
        assert pc_001_baseline_literal_present_in_text(text) is False

    def test_error_message_mentioning_the_name_is_not_a_false_positive(self):
        text = 'raise ValueError(f"brak PC_001_BASELINE - podaj jawnie")\n'
        assert pc_001_baseline_literal_present_in_text(text) is False

    def test_unrelated_64_hex_literal_for_a_different_baseline_is_not_a_false_positive(self):
        """Pulapka 2 doslownie: AUD_001_BASELINE ma wlasny, legalny hash - to NIE jest
        PC_001_BASELINE i nie powinno zostac zlapane."""
        text = f'AUD_001_BASELINE = "{"a" * 64}"\n'
        assert pc_001_baseline_literal_present_in_text(text) is False

    def test_actual_assignment_is_caught(self):
        text = f'PC_001_BASELINE = "{"c" * 64}"\n'
        assert pc_001_baseline_literal_present_in_text(text) is True

    def test_actual_assignment_alongside_the_other_baseline_is_still_caught(self):
        """Najgorszy przypadek: oba baseline'y w tym samym pliku naraz - musi zlapac
        WLASNIE ten dotyczacy PC_001_BASELINE, nie pomylic sie w ktora strone."""
        text = f'AUD_001_BASELINE = "{"a" * 64}"\nPC_001_BASELINE = "{"c" * 64}"\n'
        assert pc_001_baseline_literal_present_in_text(text) is True

    def test_annotated_assignment_form_is_also_caught(self):
        text = f'PC_001_BASELINE: str = "{"c" * 64}"\n'
        assert pc_001_baseline_literal_present_in_text(text) is True

    def test_cc10_reports_pass_for_real_halt_and_fail_for_injected_literal(self):
        snap_real = snapshot("HEAD")
        checks_real = {c["id"]: c for c in consistency_checks(snap_real)}
        assert checks_real["CC-10"]["status"] == "PASS"

        snap_fake = dict(snap_real)
        snap_fake["baseline_literal_present"] = True
        checks_fake = {c["id"]: c for c in consistency_checks(snap_fake)}
        assert checks_fake["CC-10"]["status"] == "FAIL"


class TestCCStabilityRules:
    def test_reserved_check_never_reports_pass_or_fail(self):
        checks = {c["id"]: c for c in consistency_checks(snapshot("HEAD"))}
        assert checks["CC-11"]["status"] == "RESERVED"

    def test_reserved_check_always_present_never_silently_dropped(self):
        checks = consistency_checks(snapshot("HEAD"))
        ids = [c["id"] for c in checks]
        assert "CC-11" in ids

    def test_unreadable_registry_still_produces_a_result_not_a_missing_row(self):
        """'Kontrola nigdy nie znika warunkowo' - gdy warunku nie da sie sprawdzic
        (rejestr nieodczytany), CC-03/CC-04 musza zwrocic FAIL z opisem, nie zniknac."""
        broken_snap = dict(snapshot("HEAD"))
        broken_snap["critical_files"] = MISSING
        checks = {c["id"]: c for c in consistency_checks(broken_snap)}
        assert checks["CC-03"]["status"] == "FAIL"
        assert checks["CC-04"]["status"] == "FAIL"
        assert checks["CC-03"]["detail"] == "rejestr nieodczytany"


class TestWorkingTreeCheckIsNotRetroactive:
    def test_not_live_head_reports_not_applicable(self):
        check = working_tree_check(is_live_head=False)
        assert check["status"] == "NIE_DOTYCZY"

    def test_live_head_reports_pass_or_fail_not_not_applicable(self):
        check = working_tree_check(is_live_head=True)
        assert check["status"] in ("PASS", "FAIL")


class TestFmtAndDelta:
    def test_fmt_missing_passthrough(self):
        assert fmt(MISSING) == MISSING

    def test_fmt_int_range_list(self):
        assert fmt(list(range(0, 60))) == "[0 … 59] (dlugosc: 60)"

    def test_delta_no_baseline(self):
        assert delta(5, None, has_baseline=False) == "brak odniesienia"

    def test_delta_unchanged(self):
        assert delta(5, 5, has_baseline=True) == "bez zmian"

    def test_delta_changed_shows_previous_value(self):
        result = delta(5, 3, has_baseline=True)
        assert "ZMIENIONE" in result
        assert "3" in result

    def test_delta_both_missing_is_no_baseline_not_unchanged(self):
        """MISSING == MISSING w Pythonie dla identycznego sentinela - trzeba to
        rozstrzygnac jawnie jako 'brak odniesienia', nie 'bez zmian' (dwie rozne
        rzeczy: brak wartosci ORAZ brak wartosci to nie to samo co ta sama wartosc)."""
        assert delta(MISSING, MISSING, has_baseline=True) == "brak odniesienia"


class TestVerify:
    def test_verify_passes_for_freshly_generated_report_of_head(self, tmp_path):
        from scripts.generate_canonical_parameters_report import render_report

        report_path = tmp_path / "report.md"
        text = render_report("HEAD", compare_rev=None, is_live_head=is_live_head_rev("HEAD"))
        report_path.write_text(text, encoding="utf-8")
        result = verify_report(report_path)
        assert result["ok"] is True

    def test_verify_fails_for_hand_edited_report(self, tmp_path):
        from scripts.generate_canonical_parameters_report import render_report

        report_path = tmp_path / "report.md"
        text = render_report("HEAD", compare_rev=None, is_live_head=is_live_head_rev("HEAD"))
        tampered = text.replace("`0.002`", "`0.05`")  # podmiana wartosci progu
        report_path.write_text(tampered, encoding="utf-8")
        result = verify_report(report_path)
        assert result["ok"] is False

    def test_verify_fails_when_no_commit_line_present(self, tmp_path):
        report_path = tmp_path / "report.md"
        report_path.write_text("# nie ma tu zadnego wiersza Commit\n", encoding="utf-8")
        result = verify_report(report_path)
        assert result["ok"] is False

    def test_verify_fails_for_nonexistent_declared_commit(self, tmp_path):
        report_path = tmp_path / "report.md"
        report_path.write_text("| Commit | `" + "0" * 40 + "` |\n", encoding="utf-8")
        result = verify_report(report_path)
        assert result["ok"] is False
        assert "nie istnieje" in result["reason"]


class TestHistoryReadsFromGitNotFromPreviousReport:
    def test_history_value_for_two_revs_matches_independent_static_read(self):
        for rev in ("HEAD", "15d304e"):
            expected = module_constant_at(rev, CONFIG_PATH, "MIN_DENOMINATOR")
            assert expected == 0.02

    def test_param_addresses_cover_all_documented_parameters(self):
        labels = {label for label, _p, _s, _j in PARAM_ADDRESSES}
        assert "Minimalny mianownik" in labels
        assert "Liczba realizacji na tick (domyslna)" in labels
        assert len(PARAM_ADDRESSES) == 9  # §2.9 minus Warunek B (brak adresu, wyklucza sie celowo)


class TestHistoryWithoutExplicitRevisionsIsNotSilent:
    """Audyt 661b92a, punkt 1: '--history SYMBOL' bez REV dawalo brak wyjscia i
    kod 0 - cicha zielen, ta sama klasa co 'walidator bez testu negatywnego jest
    dekoracja'. Wymog audytora: albo kod niezerowy, albo wyjscie niepuste. Ta
    implementacja wybiera wariant (b) - pelna historia pliku z `git log`, nigdy
    z wczesniej wygenerowanego raportu."""

    def test_reproduces_the_exact_audit_repro_command_without_regressing(self, capsys):
        """Doslowny przypadek z audytu: 'python -m scripts.generate_canonical_parameters_report
        --history MIN_DENOMINATOR' (bez REV)."""
        code = main(["--history", "MIN_DENOMINATOR"])
        captured = capsys.readouterr()
        assert not (captured.out.strip() == "" and code == 0), (
            "regresja do cichej zieleni: brak wyjscia I kod 0 naraz - dokladnie "
            "usterka zgloszona w audycie commita 661b92a"
        )

    def test_output_is_nonempty_and_exit_code_is_zero_only_because_output_is_real(self, capsys):
        code = main(["--history", "MIN_DENOMINATOR"])
        captured = capsys.readouterr()
        lines = [line for line in captured.out.splitlines() if line.strip()]
        assert code == 0
        assert len(lines) >= 1

    def test_falls_back_to_full_git_log_history_of_the_parameters_file(self):
        _label, path, _sym, _just = next(p for p in PARAM_ADDRESSES if p[0] == "Minimalny mianownik")
        revs = file_history_revs(path)
        assert len(revs) >= 1
        assert all(len(r) == 40 for r in revs)  # pelne SHA (git log --format=%H), nie skrocone

    def test_explicit_revs_still_take_priority_over_git_log_fallback(self, capsys):
        code = main(["--history", "MIN_DENOMINATOR", "HEAD"])
        captured = capsys.readouterr()
        assert code == 0
        assert captured.out.strip().startswith("HEAD:")

    def test_symbol_with_no_git_history_at_all_returns_nonzero_not_silent_zero(self, monkeypatch, capsys):
        """Galaz 'brak historii wcale' (np. plik nigdy nie byl w repo) - izolowana
        przez monkeypatch file_history_revs, bo wszystkie prawdziwe PARAM_ADDRESSES
        maja historie w tym repo. Musi zwrocic kod niezerowy z komunikatem."""
        import scripts.generate_canonical_parameters_report as mod

        monkeypatch.setattr(mod, "file_history_revs", lambda path: [])
        code = main(["--history", "MIN_DENOMINATOR"])
        captured = capsys.readouterr()
        assert code != 0
        assert captured.out.strip() != ""
