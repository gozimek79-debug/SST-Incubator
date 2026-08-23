"""Testy scripts/validate_history_freshness.py.

Konwencja projektu: kazdy test pozytywny ma test negatywny obok. Logika
zalezy od `git log`/`git rev-list`, wiec testy buduja WLASNE, tymczasowe
repozytorium git (pytest tmp_path) zamiast dotykac repo projektu - izolowane,
odtwarzalne, nie zostawiaja brudnego stanu.
"""

import json
import subprocess
from pathlib import Path

import pytest

from scripts.validate_history_freshness import (
    count_real_commits_since,
    newest_recorded_commit,
    offending_commits,
)


def _git(repo: Path, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True,
    )


def _commit(repo: Path, filename: str, message: str) -> str:
    (repo / filename).write_text(message, encoding="utf-8")
    _git(repo, "add", filename)
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    first = _commit(tmp_path, "seed.txt", "seed commit")
    return tmp_path, first


class TestNewestRecordedCommit:

    def test_positive_reads_first_entry_commit_field(self):
        history = {"entries": [{"commit": "abc123"}, {"commit": "older"}]}
        assert newest_recorded_commit(history) == "abc123"

    def test_negative_no_entries_raises(self):
        with pytest.raises(ValueError):
            newest_recorded_commit({"entries": []})

    def test_negative_entry_without_commit_field_raises(self):
        with pytest.raises(ValueError):
            newest_recorded_commit({"entries": [{"date": "2026-08-22"}]})


class TestCountRealCommitsSince:

    def test_positive_zero_gap_at_the_recorded_commit_itself(self, repo):
        repo_path, first = repo
        assert count_real_commits_since(repo_path, first) == 0

    def test_positive_one_real_commit_counts_as_gap_one(self, repo):
        repo_path, first = repo
        _commit(repo_path, "work.txt", "real work commit")
        assert count_real_commits_since(repo_path, first) == 1

    def test_negative_skip_ci_commit_is_excluded_from_the_gap(self, repo):
        """To jest DOKLADNIE strukturalny przypadek 'jeden commit spoznienia' -
        gdyby [skip ci] NIE bylo wykluczone, kazdy bot-commit falszywie
        podnioslby gap ponad tolerowane 1."""
        repo_path, first = repo
        _commit(repo_path, "bot.txt", "ci-status(ok): stan po udanym przebiegu [skip ci]")
        assert count_real_commits_since(repo_path, first) == 0

    def test_negative_two_real_commits_exceed_tolerance(self, repo):
        repo_path, first = repo
        _commit(repo_path, "work1.txt", "praca 1 bez wpisu w kronice")
        _commit(repo_path, "work2.txt", "praca 2 bez wpisu w kronice")
        gap = count_real_commits_since(repo_path, first)
        assert gap == 2
        assert gap > 1  # to jest dokladnie prog, ktory main() traktuje jako FAIL

    def test_negative_unknown_commit_not_an_ancestor_raises(self, repo):
        repo_path, _first = repo
        with pytest.raises(ValueError):
            count_real_commits_since(repo_path, "0" * 40)


class TestOffendingCommits:

    def test_positive_lists_real_commits_excluding_skip_ci(self, repo):
        repo_path, first = repo
        _commit(repo_path, "work.txt", "praca bez wpisu w kronice")
        _commit(repo_path, "bot.txt", "ci-status(ok): [skip ci]")
        lines = offending_commits(repo_path, first)
        assert len(lines) == 1
        assert "praca bez wpisu w kronice" in lines[0]

    def test_negative_no_real_commits_gives_empty_list(self, repo):
        repo_path, first = repo
        _commit(repo_path, "bot.txt", "ci-status(ok): [skip ci]")
        assert offending_commits(repo_path, first) == []


class TestCiYamlStepIsBlockingAndPositionedLast:
    """B5-03: krok 'Check reports/history.json freshness' MA byc blokujacy
    (bez continue-on-error, w odroznieniu od 'Check reports/status.json
    freshness' - status.json ma samonaprawe W TYM SAMYM JOBIE, history.json
    nie ma zadnej) i MA stac PO kroku 'Commit status.json and
    artifacts_index.json' (zeby porazka nie zaglodzila zapisu status.json,
    ktory rozniecilby WLASNY trip-wire przy nastepnym biegu). Sprawdzenie
    tekstowe na pliku, nie parsowanie YAML - bez nowej zaleznosci testowej."""

    CI_YAML = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"

    def _step_blocks(self):
        """Dzieli plik na bloki zaczynajace sie od '      - name: ...',
        zachowujac kolejnosc - do sprawdzenia zarowno tresci, jak pozycji."""
        text = self.CI_YAML.read_text(encoding="utf-8")
        lines = text.splitlines()
        starts = [i for i, ln in enumerate(lines) if ln.startswith("      - name:")]
        starts.append(len(lines))
        blocks = []
        for a, b in zip(starts, starts[1:]):
            name = lines[a].split("- name:", 1)[1].strip()
            blocks.append((name, "\n".join(lines[a:b])))
        return blocks

    def test_history_freshness_step_has_no_continue_on_error(self):
        blocks = dict(self._step_blocks())
        step = blocks["Check reports/history.json freshness"]
        assert "continue-on-error" not in step

    def test_negative_status_json_freshness_step_still_has_continue_on_error(self):
        """Regresja: dowod, ze powyzszy test faktycznie odroznia oba kroki,
        nie jest wiecznie-zielony przez przypadek (np. zly klucz slownika)."""
        blocks = dict(self._step_blocks())
        step = blocks["Check reports/status.json freshness"]
        assert "continue-on-error: true" in step

    def test_history_freshness_step_comes_after_commit_status_step(self):
        names = [name for name, _ in self._step_blocks()]
        commit_idx = names.index("Commit status.json and artifacts_index.json")
        history_idx = names.index("Check reports/history.json freshness")
        assert history_idx > commit_idx


class TestRealHistoryFileIsWellFormed:
    """Dowod na prawdziwych danych projektu (nie syntetycznych) - zeby ten
    plik testowy sam nie sluzyl wylacznie teorii."""

    def test_real_history_json_has_commit_field_on_every_entry(self):
        path = Path(__file__).resolve().parents[1] / "reports" / "history.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = [e["title"] for e in data["entries"] if not e.get("commit")]
        assert missing == [], f"wpisy bez pola 'commit': {missing}"
