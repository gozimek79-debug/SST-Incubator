"""B4C-01: test GWARANCJI MECHANICZNEJ runnera konfirmacyjnego PC-001, nie
deklaracji. Wzorem tests/test_pilot_final_guarantee.py (mechanika) i
tests/test_n_operational_seeds_provenance.py (prowieniencja stalej).

Runner NIE liczy statystyk (redukcja/W_early/W_late/beta/rho) - to zadanie
evaluatora (wstrzymanego). Testy tutaj sprawdzaja WYLACZNIE orkiestracje:
adresowanie parametrow (zero literali), uklad skrzyzowany (wspolny zestaw
seedow), rozmiar rodziny specow, rozlacznosc seedow dry-run, i brak
jakiegokolwiek odwolania do wielkosci reguly decyzyjnej w zrodle.
"""

import ast
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "execution_package_v0_11"))
sys.path.insert(0, str(REPO_ROOT))

import runners.pc_001_confirmatory_runner as runner_module  # noqa: E402
from runners.pc_001_confirmatory_runner import (  # noqa: E402
    build_confirmatory_run_specs, build_dry_run_specs,
    assert_dry_run_seeds_disjoint, DOCUMENTED_SEED_RANGES_CLOSED,
    DRY_RUN_SEED_START, DRY_RUN_N_SEEDS,
    _genomes, _environments, _record,
)
from clos_scientist.pc_001_experiment_config import (  # noqa: E402
    EXPERIMENT_CONFIG, N_OPERATIONAL_SEEDS, CONFIRMATORY_SEEDS_START,
    CONFIRMATORY_SEEDS, CONFIRMATORY_SEEDS_RESERVED,
)

RUNNER_PATH = REPO_ROOT / "execution_package_v0_11" / "runners" / "pc_001_confirmatory_runner.py"

FORBIDDEN_LITERALS = {
    EXPERIMENT_CONFIG["protocol"]["ticks_total"],       # 300
    CONFIRMATORY_SEEDS_START,                            # 1001
    N_OPERATIONAL_SEEDS,                                 # 8
    *EXPERIMENT_CONFIG["environments"].values(),          # noise_world/shock_world/pure_noise_world
    EXPERIMENT_CONFIG["protocol"]["lesson"],              # L1.2
}


def _non_docstring_constants(source: str):
    """Zwraca liste wartosci stalych (ast.Constant) WYLACZNIE z kodu -
    docstringi modulu/funkcji/klas wykluczone (proza smie opisywac te same
    liczby - to jest oczekiwane i wymagane, kod ma ich NIE uzywac)."""
    tree = ast.parse(source)
    docstring_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docstring_ids.add(id(body[0].value))
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and id(node) not in docstring_ids]


class TestNoForbiddenLiteralsInCode:
    """(1) Runner nie zawiera zadnego literalu parametru z listy adresow."""

    def test_forbidden_values_absent_from_non_docstring_code(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        literals = _non_docstring_constants(source)
        hits = [v for v in literals if v in FORBIDDEN_LITERALS]
        assert hits == [], (
            f"literaly zakazane z listy adresow znalezione w kodzie (poza "
            f"docstringami): {hits}"
        )

    def test_scanner_actually_detects_a_planted_literal(self):
        """Test negatywny scanera samego - dowod, ze wykrywa, nie ze zawsze
        przechodzi pusto."""
        planted = "def f():\n    ticks_total = 300\n    return ticks_total\n"
        literals = _non_docstring_constants(planted)
        assert 300 in literals

    def test_scanner_ignores_docstrings(self):
        planted = '"""Modul opisuje 300 tickow i seed 1001."""\ndef f():\n    return 1\n'
        literals = _non_docstring_constants(planted)
        assert 300 not in literals
        assert 1001 not in literals


class TestCrossedDesignSameSeedsEverywhere:
    """(2) Zestaw seedow identyczny dla wszystkich genomow i srodowisk."""

    def test_confirmatory_specs_use_one_shared_seed_set(self):
        specs = build_confirmatory_run_specs()
        by_env_genome = {}
        for lesson, environment, genome_id, seed in specs:
            by_env_genome.setdefault((environment, genome_id), set()).add(seed)
        seed_sets = list(by_env_genome.values())
        assert len(seed_sets) == len(_environments()) * len(_genomes())
        first = seed_sets[0]
        assert all(s == first for s in seed_sets), (
            "nie wszystkie (srodowisko, genom) maja identyczny zestaw seedow - "
            "uklad skrzyzowany zlamany"
        )
        assert first == set(range(CONFIRMATORY_SEEDS_START, CONFIRMATORY_SEEDS_START + N_OPERATIONAL_SEEDS))


class TestSpecCount:
    """(3) Liczba wygenerowanych specyfikacji = 23 x N_OPERATIONAL_SEEDS x 3."""

    def test_confirmatory_spec_count(self):
        specs = build_confirmatory_run_specs()
        expected = len(_genomes()) * N_OPERATIONAL_SEEDS * len(_environments())
        assert expected == 23 * 8 * 3 == 552
        assert len(specs) == expected


class TestSeedsStartFromConfirmatoryConstant:
    """(4) Seedy startuja od stalej konfirmacyjnej, nie od 1."""

    def test_min_seed_is_confirmatory_start_not_one(self):
        specs = build_confirmatory_run_specs()
        seeds_used = set(s[3] for s in specs)
        assert min(seeds_used) == CONFIRMATORY_SEEDS_START
        assert min(seeds_used) != 1
        assert max(seeds_used) == CONFIRMATORY_SEEDS_START + N_OPERATIONAL_SEEDS - 1


class TestThreeEnvironmentsMatchConfig:
    """(5) Trzy srodowiska zgadzaja sie z CONFIG::EXPERIMENT_CONFIG.environments."""

    def test_environments_match_config_values(self):
        specs = build_confirmatory_run_specs()
        envs_used = set(s[1] for s in specs)
        assert envs_used == set(EXPERIMENT_CONFIG["environments"].values())

    def test_pure_noise_world_present(self):
        assert "pure_noise_world" in set(EXPERIMENT_CONFIG["environments"].values())
        specs = build_confirmatory_run_specs()
        assert "pure_noise_world" in set(s[1] for s in specs)


class TestNoDecisionRuleStatisticsInSource:
    """(6) Runner nie odwoluje sie do W_late/redukcji/trendu/bety - test na
    zrodle, wzorem test_pilot_final_guarantee.py."""

    FORBIDDEN_PATTERNS = [
        re.compile(r"w_late", re.IGNORECASE),
        re.compile(r"redukcj", re.IGNORECASE),
        re.compile(r"reduction", re.IGNORECASE),
        re.compile(r"\btrend\b", re.IGNORECASE),
        re.compile(r"\bbeta\b", re.IGNORECASE),
        re.compile(r"\brho\b", re.IGNORECASE),
        re.compile(r"spearman", re.IGNORECASE),
        re.compile(r"wilcoxon", re.IGNORECASE),
        re.compile(r"mann_whitney", re.IGNORECASE),
    ]

    def test_no_statistical_terms_in_code(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        code_lines = [line for line in no_docstrings.splitlines()
                      if not line.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        violations = [p.pattern for p in self.FORBIDDEN_PATTERNS if p.search(code_only)]
        assert violations == [], f"kod odwoluje sie do wielkosci reguly decyzyjnej: {violations}"

    def test_no_statistics_module_import(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        assert "clos_curriculum.laboratory.statistics" not in no_docstrings
        assert "clos_curriculum\\laboratory\\statistics" not in no_docstrings


class TestDryRunSeedDisjointness:
    """(7) Rozlacznosc zakresu dry-run od wszystkich udokumentowanych zakresow
    - B4C-03/04: przeciwko BLOKOWI ZAREZERWOWANEMU (CONFIRMATORY_SEEDS_RESERVED),
    nie dzisiejszemu waskiemu zuzywanemu zakresowi (N=8) - patrz uzasadnienie
    w docstringu runnera. Wszystkie zakresy w DOCUMENTED_SEED_RANGES_CLOSED sa
    dzis ZAMKNIETE (audytor 700000-720000 podany przez CTO w B4C-03)."""

    def test_disjoint_check_passes_for_real_configuration(self):
        assert_dry_run_seeds_disjoint()  # nie podnosi wyjatku

    def test_dry_run_seeds_not_in_any_closed_range(self):
        dry_run_seeds = set(range(DRY_RUN_SEED_START, DRY_RUN_SEED_START + DRY_RUN_N_SEEDS))
        for name, rng in DOCUMENTED_SEED_RANGES_CLOSED.items():
            assert not (dry_run_seeds & set(rng)), f"nachodzi na '{name}'"

    def test_confirmatory_check_uses_reserved_block_not_narrow_used_range(self):
        """Rozroznienie BLOK ZAREZERWOWANY (50 seedow) vs zbior UZYWANY dzis
        (8 seedow) MUSI byc widoczne w samej strukturze sprawdzanych zakresow -
        w przeciwnym razie przyszly wzrost N_OPERATIONAL_SEEDS moglby cicho
        pozwolic na kolizje, ktorej ten test mial zapobiec."""
        checked = DOCUMENTED_SEED_RANGES_CLOSED["confirmatory_reserved_block"]
        assert checked == CONFIRMATORY_SEEDS_RESERVED
        assert len(checked) > len(CONFIRMATORY_SEEDS), (
            "blok zarezerwowany musi byc WIEKSZY niz dzisiejszy zuzywany zakres, "
            "inaczej nie daje zapasu na wzrost N_operational"
        )

    def test_negative_overlapping_range_is_caught(self):
        """Test negatywny scanera rozlacznosci (na strukturze danych) -
        podstawiony zakres nakladajacy sie na blok zarezerwowany MUSI zostac
        wykryty (dowod, ze funkcja faktycznie porownuje zbiory, nie tylko
        zawsze zwraca sukces)."""
        fake_seeds = set(range(CONFIRMATORY_SEEDS_START, CONFIRMATORY_SEEDS_START + 2))
        overlap = fake_seeds & set(DOCUMENTED_SEED_RANGES_CLOSED["confirmatory_reserved_block"])
        assert overlap, "test negatywny sam w sobie zle skonstruowany - brak nakladania"

    def test_negative_dry_run_start_inside_reserved_block_raises(self, monkeypatch):
        """Test negatywny NA PRAWDZIWEJ FUNKCJI (B4C-03 pkt 5, weryfikacja
        #3): DRY_RUN_SEED_START podstawiony na wartosc WEWNATRZ bloku
        zarezerwowanego MUSI podniesc AssertionError - nie ciche powodzenie."""
        monkeypatch.setattr(runner_module, "DRY_RUN_SEED_START", CONFIRMATORY_SEEDS_START + 1)
        with pytest.raises(AssertionError, match="confirmatory_reserved_block"):
            runner_module.assert_dry_run_seeds_disjoint()


class TestConfirmatorySeedsStartProvenance:
    """(8) Prowieniencja stalej seeda poczatkowego + test negatywny."""

    NOTATKA_B4_PATH = REPO_ROOT / "publications" / "NOTATKA_B4_ANALIZA_MOCY_2026-07-28.md"
    ANCHOR_RE = re.compile(r"konfirmac\w*", re.IGNORECASE)
    NUMBER_RE = re.compile(r"\b1001\b")
    _WINDOW = 80

    @classmethod
    def find_confirmatory_1001_mentions(cls, text):
        found = []
        for m in cls.NUMBER_RE.finditer(text):
            window = text[max(0, m.start() - cls._WINDOW): m.start()]
            if cls.ANCHOR_RE.search(window):
                found.append(m.start())
        return found

    def test_constant_value(self):
        assert CONFIRMATORY_SEEDS_START == 1001

    def test_notatka_b4_confirms_1001_near_confirmatory_anchor(self):
        text = self.NOTATKA_B4_PATH.read_text(encoding="utf-8")
        hits = self.find_confirmatory_1001_mentions(text)
        assert len(hits) >= 1, (
            "NOTATKA_B4 nie zawiera '1001' w poblizu kotwicy 'konfirmac*' - "
            "prowieniencja stalej nie potwierdzona w zrodle"
        )

    def test_negative_stripped_anchor_fails_not_passes(self):
        """(a) tekst bez kotwicy -> FAIL wykrycia, nie ciche PASS."""
        text = self.NOTATKA_B4_PATH.read_text(encoding="utf-8")
        redacted = re.sub(r"konfirmac\w*", "XXXXX", text, flags=re.IGNORECASE)
        assert self.find_confirmatory_1001_mentions(redacted) == []

    def test_negative_wrong_number_not_matched(self):
        """(b) podmieniona liczba (np. 1002) -> wzorzec numeryczny jej nie lapie."""
        text = self.NOTATKA_B4_PATH.read_text(encoding="utf-8")
        tampered = text.replace("seeda 1001", "seeda 1002").replace("od 1001", "od 1002")
        assert tampered != text, "podmiana nie zaszla - dopasuj literalny tekst"
        assert self.find_confirmatory_1001_mentions(tampered) == []


class TestNoneTicksPreservedNotZeroed:
    """PC-001 §2.1: ticki bez wartosci wykluczane, NIE zerowane. Dry-run
    empiryczny (207 przebiegow) nie wyprodukowal ani jednego None ticka (brak
    okazji do sprawdzenia na prawdziwych danych) - test bezposredni na
    _record() z syntetyczna trajektoria dowodzi mechanizmu niezaleznie od
    tego, czy real dane akurat go cwicza."""

    def test_none_tick_preserved_as_json_null_not_zero(self):
        record = _record("L1.2", "noise_world", "pop_000", 50000, {0: 0.5, 1: None, 2: 0.3})
        traj = record["metrics"]["prediction_error_by_tick"]
        assert traj["1"] is None
        assert traj["1"] != 0
        assert traj["1"] != 0.0
        assert record["metrics"]["n_ticks_none"] == 1
        assert record["metrics"]["n_ticks_total"] == 3

    def test_none_tick_survives_json_roundtrip(self):
        record = _record("L1.2", "noise_world", "pop_000", 50000, {0: None})
        roundtripped = json.loads(json.dumps(record, ensure_ascii=False, default=str))
        assert roundtripped["metrics"]["prediction_error_by_tick"]["0"] is None
