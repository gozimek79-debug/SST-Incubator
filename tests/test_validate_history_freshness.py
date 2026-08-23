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
    push_before_ref,
    effective_tolerance,
    ZERO_SHA,
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

    def test_positive_until_param_measures_to_an_earlier_point_not_just_head(self, repo):
        """B4C-05 v10: `until` pozwala mierzyc dystans do dowolnego punktu,
        nie tylko HEAD - podstawa dla effective_tolerance (dystans do
        poczatku biezacego pushu)."""
        repo_path, first = repo
        mid = _commit(repo_path, "work1.txt", "praca 1")
        _commit(repo_path, "work2.txt", "praca 2")
        assert count_real_commits_since(repo_path, first, until=mid) == 1
        assert count_real_commits_since(repo_path, first) == 2  # domyslnie HEAD


class TestPushBeforeRef:
    """B4C-05 v10 ZAKRES 2: ustalenie granicy biezacego pushu - env
    GITHUB_EVENT_BEFORE (CI) ma pierwszenstwo, potem upstream @{u} (lokalnie),
    None gdy zadne niedostepne (NIE zgadywanie)."""

    def test_positive_env_var_used_when_valid_ancestor(self, repo, monkeypatch):
        repo_path, first = repo
        monkeypatch.setenv("GITHUB_EVENT_BEFORE", first)
        assert push_before_ref(repo_path) == first

    def test_negative_zero_sha_env_var_is_ignored(self, repo, monkeypatch):
        """GitHub wysyla 40 zer przy pierwszym pushu nowej galezi - to NIE
        jest prawdziwy punkt odniesienia, musi byc jawnie odrzucone."""
        repo_path, _first = repo
        monkeypatch.setenv("GITHUB_EVENT_BEFORE", ZERO_SHA)
        assert push_before_ref(repo_path) is None

    def test_negative_nonexistent_commit_in_env_var_is_ignored(self, repo, monkeypatch):
        repo_path, _first = repo
        monkeypatch.setenv("GITHUB_EVENT_BEFORE", "f" * 40)
        assert push_before_ref(repo_path) is None

    def test_positive_upstream_branch_used_when_no_env_var(self, repo, tmp_path, monkeypatch):
        """Symulacja lokalnego dev bez CI: prawdziwy zdalny (bare) repo +
        upstream tracking, zamiast env zmiennej."""
        repo_path, first = repo
        monkeypatch.delenv("GITHUB_EVENT_BEFORE", raising=False)
        remote_path = tmp_path.parent / (tmp_path.name + "_remote.git")
        _git(repo_path, "init", "--bare", str(remote_path))
        _git(repo_path, "remote", "add", "origin", str(remote_path))
        branch = _git(repo_path, "branch", "--show-current").stdout.strip()
        _git(repo_path, "push", "-u", "origin", branch)
        assert push_before_ref(repo_path) == first

    def test_negative_no_env_and_no_upstream_returns_none(self, repo, monkeypatch):
        repo_path, _first = repo
        monkeypatch.delenv("GITHUB_EVENT_BEFORE", raising=False)
        assert push_before_ref(repo_path) is None


class TestEffectiveTolerance:
    """B4C-05 v10 ZAKRES 2: tolerancja = 1 + rozmiar biezacego pushu, TYLKO
    jesli kronika byla juz aktualna (gap<=1) na poczatku tego pushu."""

    def test_positive_no_push_boundary_falls_back_to_1(self, repo, monkeypatch):
        repo_path, first = repo
        monkeypatch.delenv("GITHUB_EVENT_BEFORE", raising=False)
        assert effective_tolerance(repo_path, first) == 1

    def test_positive_fresh_chronicle_gets_tolerance_matching_push_size(self, repo, monkeypatch):
        """Kronika aktualna PRZED pushem (recorded_commit == before), push
        wprowadza 3 realne commity -> tolerancja = 1 + 3 = 4, NIE 1."""
        repo_path, first = repo
        # 'before' pushu to WLASNIE punkt, w ktorym kronika byla aktualna
        monkeypatch.setenv("GITHUB_EVENT_BEFORE", first)
        _commit(repo_path, "work1.txt", "commit 1 z trzech")
        _commit(repo_path, "work2.txt", "commit 2 z trzech")
        _commit(repo_path, "work3.txt", "commit 3 z trzech")
        assert effective_tolerance(repo_path, first) == 4
        # i test pozytywny na koncu: gap (3) mieisci sie w tak wyliczonej tolerancji
        assert count_real_commits_since(repo_path, first) == 3

    def test_negative_stale_chronicle_before_push_does_not_get_extended_tolerance(self, repo, monkeypatch):
        """Kronika BYLA juz w tyle o wiecej niz 1 PRZED biezacym pushem
        (dwa realne commity, old1+old2, wydarzyly sie PRZED poczatkiem
        pushu - 'before' to koniec old2) - tolerancja NIE rozszerza sie do
        rozmiaru pushu (nie ukrywa dlugu sprzed pushu pod plaszczykiem
        'to jeden push')."""
        repo_path, first = repo
        _commit(repo_path, "old1.txt", "stara praca 1, juz bez wpisu")
        before = _commit(repo_path, "old2.txt", "stara praca 2, juz bez wpisu")  # gap_before_push = 2 > 1
        monkeypatch.setenv("GITHUB_EVENT_BEFORE", before)
        _commit(repo_path, "new.txt", "nowy commit w biezacym pushu")
        assert effective_tolerance(repo_path, first) == 1

    def test_negative_of_negative_exactly_at_boundary_still_extends(self, repo, monkeypatch):
        """Odwrotny sanity-check: gdy gap_before_push jest DOKLADNIE 1
        (strukturalnie tolerowane), rozszerzenie WCIAZ dziala - warunek
        odcinajacy to '> 1', nie '> 0'."""
        repo_path, first = repo
        before = _commit(repo_path, "lag.txt", "jeden commit spoznienia (tolerowany)")
        monkeypatch.setenv("GITHUB_EVENT_BEFORE", before)
        _commit(repo_path, "work.txt", "praca w biezacym pushu")
        assert effective_tolerance(repo_path, first) == 2  # 1 (spoznienie) + 1 (rozmiar pushu)


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


class TestCiYamlStepIsBlockingAndPositionedBeforeStatusWrite:
    """B4C-05 v10 (POPRAWKA B5-03): krok 'Check reports/history.json
    freshness' MA byc blokujacy (bez continue-on-error, w odroznieniu od
    'Check reports/status.json freshness' - status.json ma samonaprawe W
    TYM SAMYM JOBIE, history.json nie ma zadnej) i MA stac PRZED krokiem
    'Write reports/status.json'.

    ZNALEZISKO (audyt CTO, v10): przy poprzednim umiejscowieniu (PO 'Commit
    status.json...', B5-03) bot zapisywal "ci-status(ok)" DLA PRZEBIEGU,
    KTORY FAKTYCZNIE PADL na tym wlasnie kroku - job.status widziany przez
    JOB_STATUS w "Write reports/status.json"/"Commit status.json..." byl
    jeszcze "success", bo kontrola kroniki jeszcze sie nie wykonala.
    Uzasadnienie B5-03 za koncem joba (rzekome "zaglodzenie" samonaprawy
    status.json) bylo BEZPODSTAWNE - "Write reports/status.json" i "Commit
    status.json..." juz maja if: always(), wiec wykonuja sie niezaleznie od
    tego, czy wczesniejszy krok (ten wlacznie) padnie. Sprawdzenie tekstowe
    na pliku, nie parsowanie YAML - bez nowej zaleznosci testowej."""

    CI_YAML = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"

    def _step_blocks(self):
        """Dzieli plik na bloki zaczynajace sie od '      - name: ...',
        zachowujac kolejnosc. Kazdy blok konczy sie na PIERWSZEJ pustej linii
        LUB na kolejnym '- name:', co nastapi pierwsze - w tym pliku komentarz
        opisujacy krok X zawsze stoi NAD krokiem X (nigdy pod), oddzielony od
        WLASNEJ akcji poprzedniego kroku pusta linia; bez tego odciecia blok
        kroku X zgarnialby tez caly komentarz opisujacy krok X+1 (falszywe
        trafienia typu 'continue-on-error' wspominane w prozie cudzego
        komentarza, nie we wlasnym YAML-u kroku)."""
        text = self.CI_YAML.read_text(encoding="utf-8")
        lines = text.splitlines()
        starts = [i for i, ln in enumerate(lines) if ln.startswith("      - name:")]
        starts.append(len(lines))
        blocks = []
        for a, b in zip(starts, starts[1:]):
            name = lines[a].split("- name:", 1)[1].strip()
            end = a
            while end < b and lines[end].strip() != "":
                end += 1
            blocks.append((name, "\n".join(lines[a:end])))
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

    def test_history_freshness_step_comes_before_write_status_step(self):
        names = [name for name, _ in self._step_blocks()]
        write_idx = names.index("Write reports/status.json")
        history_idx = names.index("Check reports/history.json freshness")
        assert history_idx < write_idx

    def test_history_freshness_step_comes_before_commit_status_step(self):
        names = [name for name, _ in self._step_blocks()]
        commit_idx = names.index("Commit status.json and artifacts_index.json")
        history_idx = names.index("Check reports/history.json freshness")
        assert history_idx < commit_idx

    def test_write_status_and_commit_steps_still_have_if_always(self):
        """B4C-05 v10 zakaz wprost: NIE zmieniaj if: always() na zadnym
        kroku - dowod, ze nikt (w tym ten commit) tego nie zrobil. Ich
        obecnosc jest WLASNIE tym, co czyni przesuniecie kroku kroniki
        bezpiecznym (samonaprawa nie jest glodzona)."""
        blocks = dict(self._step_blocks())
        assert "if: always()" in blocks["Write reports/status.json"]
        assert "if: always()" in blocks["Commit status.json and artifacts_index.json"]

    def test_negative_reversed_order_on_real_file_content_is_caught(self, tmp_path, monkeypatch):
        """B4C-05 v10 pkt: 'przestaw kolejnosc w kopii -> FAIL', na
        PRAWDZIWEJ tresci pliku (nie na syntetycznej liscie nazw) - wytnij
        blok 'Check reports/history.json freshness' z jego biezacej (poprawnej)
        pozycji i wklej go z powrotem PO 'Commit status.json...', odtwarzajac
        dokladnie ukladu z B5-03, ktory spowodowal falszywa zielen."""
        blocks = self._step_blocks()
        by_name = dict(blocks)
        history_block = by_name["Check reports/history.json freshness"]

        text = self.CI_YAML.read_text(encoding="utf-8")
        # usun blok z biezacej (poprawnej) pozycji
        without_history = text.replace(history_block + "\n\n", "", 1)
        assert without_history != text, "nie udalo sie wyciac bloku - test niemiarodajny"
        # doklej na koniec pliku, odtwarzajac stara (bledna) pozycje z B5-03
        reversed_copy = without_history.rstrip("\n") + "\n\n" + history_block + "\n"

        copy_path = tmp_path / "ci_reversed.yml"
        copy_path.write_text(reversed_copy, encoding="utf-8")
        monkeypatch.setattr(self, "CI_YAML", copy_path)

        names = [name for name, _ in self._step_blocks()]
        write_idx = names.index("Write reports/status.json")
        history_idx = names.index("Check reports/history.json freshness")
        assert not (history_idx < write_idx), (
            "test pozytywny (test_history_freshness_step_comes_before_write_status_step) "
            "NIE wykrylby tej odwroconej kolejnosci - regresja"
        )


class TestRealHistoryFileIsWellFormed:
    """Dowod na prawdziwych danych projektu (nie syntetycznych) - zeby ten
    plik testowy sam nie sluzyl wylacznie teorii."""

    def test_real_history_json_has_commit_field_on_every_entry(self):
        path = Path(__file__).resolve().parents[1] / "reports" / "history.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = [e["title"] for e in data["entries"] if not e.get("commit")]
        assert missing == [], f"wpisy bez pola 'commit': {missing}"
