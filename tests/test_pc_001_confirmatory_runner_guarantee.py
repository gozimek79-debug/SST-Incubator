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
import inspect
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
    _genomes, _environments, _record, _capture_full_trajectory,
    verify_trajectory_field_consistency, verify_input_provenance,
    TrajectoryFieldConsistencyError, InputProvenanceMismatchError,
    TRAJECTORY_SCHEMA_VERSION_PRODUCED,
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
    """(3) Liczba wygenerowanych specyfikacji = 23 x N_OPERATIONAL_SEEDS x 3.

    B4C-2 (12), znalezisko CTO: ta klasa mialaby wczesniej literal
    '23 * 8 * 3 == 552' - N_OPERATIONAL_SEEDS zmienil sie juz raz (8->9);
    hardkodowanie go tutaj byloby dokladnie tym bledem klasy, ktory CTO
    znalazl w CONFIG. 23 (liczba genomow) i 3 (liczba srodowisk) SA
    stabilnymi faktami strukturalnymi (zamrozona populacja, CONFIG::
    EXPERIMENT_CONFIG.environments) - N_OPERATIONAL_SEEDS nie jest, wiec
    NIE wchodzi do iloczynu jako literal."""

    def test_confirmatory_spec_count(self):
        specs = build_confirmatory_run_specs()
        expected = len(_genomes()) * N_OPERATIONAL_SEEDS * len(_environments())
        assert len(specs) == expected
        assert len(_genomes()) == 23  # populacja zamrozona, execution_package_v0_11/genomes/population.json
        assert len(_environments()) == 3  # primary/K3/K4, CONFIG::EXPERIMENT_CONFIG


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
    tego, czy real dane akurat go cwicza. Ksztalt trajektorii (B4C-1 (02)):
    kazdy tick -> {"prediction":.., "input":.., "prediction_error":..}."""

    def test_none_tick_preserved_as_json_null_not_zero(self):
        trajectory = {
            0: {"prediction": 0.4, "input": 0.1, "prediction_error": 0.5},
            1: {"prediction": None, "input": None, "prediction_error": None},
            2: {"prediction": 0.2, "input": 0.1, "prediction_error": 0.3},
        }
        record = _record("L1.2", "noise_world", "pop_000", 50000, trajectory, shock_tick=None)
        pe_traj = record["metrics"]["prediction_error_by_tick"]
        assert pe_traj["1"] is None
        assert pe_traj["1"] != 0
        assert pe_traj["1"] != 0.0
        assert record["metrics"]["prediction_by_tick"]["1"] is None
        assert record["metrics"]["input_by_tick"]["1"] is None
        assert record["metrics"]["n_ticks_none"] == 1
        assert record["metrics"]["n_ticks_total"] == 3

    def test_none_tick_survives_json_roundtrip(self):
        trajectory = {0: {"prediction": None, "input": None, "prediction_error": None}}
        record = _record("L1.2", "noise_world", "pop_000", 50000, trajectory, shock_tick=None)
        roundtripped = json.loads(json.dumps(record, ensure_ascii=False, default=str))
        assert roundtripped["metrics"]["prediction_error_by_tick"]["0"] is None
        assert roundtripped["metrics"]["prediction_by_tick"]["0"] is None
        assert roundtripped["metrics"]["input_by_tick"]["0"] is None


class TestObservationChannelExtension:
    """B4C-1 (02), decyzja CTO: prediction/input/prediction_error zapisywane
    RAZEM per tick (nie sama prediction_error - patrz docstring modulu, K1/
    K5/K6 z publications/pc_001_bh_family.json tego potrzebuja). Cztery
    gwarancje, sprawdzone na PRAWDZIWYM przebiegu (seed dry-run, NIGDY
    konfirmacyjny - zakaz wprost B4C-1 (02))."""

    DRY_SEED = DRY_RUN_SEED_START  # 50000 - szczelina bezpieczna, nigdy konfirmacyjna
    ENV = "noise_world"

    @classmethod
    def _real_trajectory(cls):
        genome = next(g for g in _genomes() if g["genome_id"] == "default")
        trajectory, _shock_tick = _capture_full_trajectory("L1.2", cls.ENV, genome, cls.DRY_SEED)
        return trajectory

    def test_dry_seed_is_not_confirmatory(self):
        """Warunek wstepny dla calej klasy: dowod, ze DRY_SEED faktycznie
        NIE jest z bloku konfirmacyjnego (uzywanego ani zarezerwowanego) -
        zakaz B4C-1 (02) egzekwowany, nie tylko deklarowany."""
        assert self.DRY_SEED not in set(CONFIRMATORY_SEEDS)
        assert self.DRY_SEED not in set(CONFIRMATORY_SEEDS_RESERVED)

    def test_guarantees_1_and_2_hold_on_real_run(self):
        """Gwarancje 1 (pola razem/None razem) i 2 (prediction_error ==
        abs(prediction-input)) - na prawdziwym przebiegu."""
        trajectory = self._real_trajectory()
        assert len(trajectory) > 0
        verify_trajectory_field_consistency(trajectory)  # nie podnosi

    def test_guarantee_3_holds_on_real_run(self):
        """Gwarancja 3: zapisany input zgadza sie z WorldRuntime.step dla
        tego samego (tick, seed, environment) - kontrola prowieniencji."""
        trajectory = self._real_trajectory()
        verify_input_provenance(trajectory, self.ENV, self.DRY_SEED)  # nie podnosi

    def test_negative_tampered_input_fails_both_checks(self):
        """Gwarancja 4 (test negatywny obowiazkowy): podmieniony JEDEN input
        -> OBIE kontrole (spojnosc pol i prowieniencja) daja FAIL - pokazane
        osobno, oba wyniki. Tampering psuje ROWNOCZESNIE gwarancje 2
        (prediction_error przestaje zgadzac sie z |prediction-input|) i
        gwarancje 3 (input przestaje zgadzac sie z WorldRuntime.step)."""
        trajectory = self._real_trajectory()
        tick = next(iter(trajectory))
        tampered = {t: dict(v) for t, v in trajectory.items()}
        original_input = tampered[tick]["input"]
        tampered[tick]["input"] = (original_input if original_input is not None else 0.0) + 0.5

        with pytest.raises(TrajectoryFieldConsistencyError):
            verify_trajectory_field_consistency(tampered)
        with pytest.raises(InputProvenanceMismatchError):
            verify_input_provenance(tampered, self.ENV, self.DRY_SEED)

    def test_negative_tampered_prediction_fails_field_consistency_only(self):
        """Gwarancja 4, druga polowa: podmieniona JEDNA prediction -> kontrola
        spojnosci pol (gwarancja 2) daje FAIL. Kontrola prowieniencji
        (gwarancja 3, sprawdza WYLACZNIE input) poprawnie NIE reaguje -
        sprawdzone jawnie, zeby to byla udowodniona granica odpowiedzialnosci,
        nie niezauwazona luka."""
        trajectory = self._real_trajectory()
        tick = next(iter(trajectory))
        tampered = {t: dict(v) for t, v in trajectory.items()}
        original_pred = tampered[tick]["prediction"]
        tampered[tick]["prediction"] = (original_pred if original_pred is not None else 0.0) + 0.5

        with pytest.raises(TrajectoryFieldConsistencyError):
            verify_trajectory_field_consistency(tampered)
        verify_input_provenance(tampered, self.ENV, self.DRY_SEED)  # nie podnosi - poprawnie

    def test_negative_input_none_others_present_is_caught(self):
        """Gwarancja 1, przypadek 1/3 (B4C-1 (03), zadanie CTO): input=None,
        prediction i prediction_error obecne -> FAIL. Fizycznie niemozliwe
        (bez input nie da sie policzyc prediction_error), wiec MUSI byc
        zlapane jako niespojnosc, nie brak pomiaru."""
        broken = {0: {"prediction": 0.4, "input": None, "prediction_error": 0.5}}
        with pytest.raises(TrajectoryFieldConsistencyError):
            verify_trajectory_field_consistency(broken)

    def test_negative_prediction_none_others_present_is_caught(self):
        """Gwarancja 1, przypadek 2/3: prediction=None, input i
        prediction_error obecne -> FAIL. Ten sam powod fizyczny jak wyzej,
        odwrotne pole."""
        broken = {0: {"prediction": None, "input": 0.1, "prediction_error": 0.5}}
        with pytest.raises(TrajectoryFieldConsistencyError):
            verify_trajectory_field_consistency(broken)

    def test_negative_prediction_error_none_others_present_is_caught(self):
        """Gwarancja 1, przypadek 3/3: prediction_error=None, prediction i
        input obecne -> FAIL. Nawet gdy obie skladowe sa znane, brakujaca
        prediction_error jest niespojnoscia zapisu, nie brakiem pomiaru -
        powinna byc obliczalna z pozostalych dwoch."""
        broken = {0: {"prediction": 0.4, "input": 0.1, "prediction_error": None}}
        with pytest.raises(TrajectoryFieldConsistencyError):
            verify_trajectory_field_consistency(broken)

    def test_negative_of_negative_all_none_together_is_valid(self):
        """Sanity: wszystkie trzy None RAZEM (brak obserwacji) jest
        POPRAWNYM stanem, nie bledem - dowod, ze test powyzej lapie
        MIESZANKE pol, nie sama obecnosc None."""
        clean = {0: {"prediction": None, "input": None, "prediction_error": None}}
        verify_trajectory_field_consistency(clean)  # nie podnosi

    def test_negative_of_negative_matching_input_does_not_raise(self):
        """Sanity odwrotny do testu prowieniencji: NIEZMIENIONY zapisany
        input (prawdziwy przebieg) zgadza sie z WorldRuntime.step - dowod, ze
        test powyzej lapie NIEZGODNOSC, nie jest zawsze-FAIL."""
        trajectory = self._real_trajectory()
        verify_input_provenance(trajectory, self.ENV, self.DRY_SEED)


class TestTrajectorySchemaVersion:
    """B4C-1 (02): PRODUCENT deklaruje wersje, ktora produkuje - stala
    ODREBNA od przyszlej stalej KONSUMENTA (evaluator, osobne zlecenie,
    jeszcze nie istnieje). Nie konsolidowac w jedna - rozjazd miedzy nimi
    ma byc widoczny, nie ukryty wspolna stala."""

    def test_version_is_declared_and_recorded_in_output(self):
        record = _record("L1.2", "noise_world", "pop_000", 50000,
                          {0: {"prediction": 0.1, "input": 0.2, "prediction_error": 0.1}},
                          shock_tick=None)
        assert record["trajectory_schema_version"] == TRAJECTORY_SCHEMA_VERSION_PRODUCED

    def test_version_survives_json_roundtrip(self):
        record = _record("L1.2", "noise_world", "pop_000", 50000,
                          {0: {"prediction": 0.1, "input": 0.2, "prediction_error": 0.1}},
                          shock_tick=None)
        roundtripped = json.loads(json.dumps(record, ensure_ascii=False, default=str))
        assert roundtripped["trajectory_schema_version"] == TRAJECTORY_SCHEMA_VERSION_PRODUCED

    def test_version_is_not_the_string_1_leftover_from_first_format(self):
        """Sanity: wersja MUSI odzwierciedlac rozszerzony format (>=2), nie
        zostac przypadkiem na wartosci pierwszej wersji (sama
        prediction_error) po tej zmianie."""
        assert TRAJECTORY_SCHEMA_VERSION_PRODUCED != 1

    def test_version_is_not_leftover_from_second_format(self):
        """Sanity (B4C-1 (07)): wersja MUSI odzwierciedlac rozszerzenie o
        shock_tick (3), nie zostac przypadkiem na wartosci drugiej wersji
        (prediction+input+prediction_error, bez shock_tick)."""
        assert TRAJECTORY_SCHEMA_VERSION_PRODUCED != 2


class ShockTickTrajectoryMismatchError(Exception):
    """Test gwarancji (B4C-1 (07)), OSOBNY OD RUNNERA (decyzja CTO pkt 3:
    'Runner NIE rekonstruuje shock_tick') - zyje wylacznie tutaj, nie w
    kodzie produkcyjnym runnera. Podniesiony, gdy koniec stalego prefiksu
    zapisanej trajektorii input(t) nie zgadza sie z zapisanym shock_tick,
    ALBO gdy zaden koniec prefiksu nie jest wykrywalny (niezalezna
    walidacja niemozliwa) - w obu przypadkach FAIL, nigdy ciche pominiecie."""


def _detect_input_prefix_end(input_by_tick):
    """Koniec stalego prefiksu zapisanego input(t): pierwszy (chronologicznie)
    tick, ktorego wartosc rozni sie od wartosci PIERWSZEGO zarejestrowanego
    ticka - BEZ znajomosci KONKRETNEJ wartosci tego prefiksu (dziala dla
    kazdej stalej wartosci, nie tylko 0.2 shock_world - korekta CTO wobec
    pierwotnego sformulowania przez "odchylenie od wartosci przedwstrzasowej",
    ktore po cichu zakladalo znajomosc tej wartosci). Ticki None (PC-001
    §2.1: wykluczane) pomijane przy szukaniu referencji i przejscia. Brak
    wykrywalnego przejscia -> None (niezalezna walidacja niemozliwa)."""
    ticks = sorted(int(t) for t, v in input_by_tick.items() if v is not None)
    if not ticks:
        return None
    ref = input_by_tick[str(ticks[0])]
    for t in ticks[1:]:
        if input_by_tick[str(t)] != ref:
            return t
    return None


def _assert_shock_tick_matches_trajectory(record):
    """Kontrola prowieniencji shock_tick (B4C-1 (07)): koniec stalego
    prefiksu zapisanego input(t) musi zgadzac sie z zapisanym shock_tick.
    Porownuje METADANE (shock_tick) z FAKTYCZNYM zachowaniem swiata
    (zarejestrowana trajektoria) - dwa niezalezne zrodla danych z TEGO
    SAMEGO przebiegu, nie kod z kodem."""
    input_by_tick = record["metrics"]["input_by_tick"]
    recorded_shock_tick = record["shock_tick"]
    detected = _detect_input_prefix_end(input_by_tick)
    if detected is None:
        raise ShockTickTrajectoryMismatchError(
            "brak wykrywalnego przejscia w zarejestrowanym input(t) - "
            "niezalezna walidacja shock_tick niemozliwa"
        )
    if detected != recorded_shock_tick:
        raise ShockTickTrajectoryMismatchError(
            f"koniec stalego prefiksu zapisanego input(t)={detected} != "
            f"zapisany shock_tick={recorded_shock_tick!r}"
        )


class TestShockTickGuarantee:
    """B4C-1 (07): shock_tick zrodlem run_shock_recovery() (nie osobne
    wyliczenie, nie rekonstrukcja w runnerze - decyzje CTO pkt 2/3). Test
    gwarancji tutaj, OSOBNY OD RUNNERA (decyzja CTO), porownuje zapisany
    shock_tick z zarejestrowana trajektoria input(t), bez literalu
    wartosci prefiksu (decyzja CTO pkt 6)."""

    ENV_K3 = "shock_world"
    ENV_PRIMARY = "noise_world"
    DRY_SEED = DRY_RUN_SEED_START  # 50000 - szczelina bezpieczna, nigdy konfirmacyjna

    @classmethod
    def _real_record(cls, environment, genome_id="default"):
        genome = next(g for g in _genomes() if g["genome_id"] == genome_id)
        trajectory, shock_tick = _capture_full_trajectory("L1.2", environment, genome, cls.DRY_SEED)
        return _record("L1.2", environment, genome_id, cls.DRY_SEED, trajectory, shock_tick)

    def test_detection_function_has_no_literal_prefix_value(self):
        """Decyzja CTO pkt 6: detekcja NIE zna konkretnej wartosci prefiksu
        (np. 0.2 shock_world) - dowod na zrodle funkcji, nie tylko
        deklaracja w docstringu."""
        source = inspect.getsource(_detect_input_prefix_end)
        no_docstring = re.sub(r'"""[\s\S]*?"""', "", source)
        assert "0.2" not in no_docstring
        assert "0,2" not in no_docstring

    def test_shock_tick_is_recorded_for_k3(self):
        record = self._real_record(self.ENV_K3)
        assert record["shock_tick"] is not None
        assert isinstance(record["shock_tick"], int)

    def test_shock_tick_is_none_for_primary_environment(self):
        """Srodowiska bez pojedynczej perturbacji - run_shock_recovery() nie
        zwraca "t_shock" - shock_tick zapisany jako None, nie zerowany."""
        record = self._real_record(self.ENV_PRIMARY)
        assert record["shock_tick"] is None

    def test_shock_tick_matches_prefix_end_on_real_run(self):
        """Weryfikacja pkt 1-2: kontrola gwarancji na PRAWDZIWYM przebiegu
        K3 - nie podnosi wyjatku."""
        record = self._real_record(self.ENV_K3)
        _assert_shock_tick_matches_trajectory(record)  # nie podnosi

    def test_shock_tick_matches_prefix_end_across_multiple_genomes(self):
        """Ten sam sprawdzian na kilku genomach - dowod, ze zgodnosc nie
        jest przypadkiem jednego genomu (CTO zmierzyl 30/30 na 30 seedach;
        tutaj sprawdzone na kilku genomach tego samego dry-run seeda,
        jedynych realnie dostepnych w tym repo bez uruchamiania konfirmacji)."""
        genome_ids = [g["genome_id"] for g in _genomes()[:5]]
        for genome_id in genome_ids:
            record = self._real_record(self.ENV_K3, genome_id=genome_id)
            _assert_shock_tick_matches_trajectory(record)  # nie podnosi

    def test_negative_shifted_shock_tick_raises(self):
        """Weryfikacja pkt 3 (test negatywny obowiazkowy): zapisany
        shock_tick przesuniety o jeden tick -> FAIL."""
        record = self._real_record(self.ENV_K3)
        tampered = dict(record)
        tampered["shock_tick"] = record["shock_tick"] + 1
        with pytest.raises(ShockTickTrajectoryMismatchError):
            _assert_shock_tick_matches_trajectory(tampered)

    def test_negative_shifted_the_other_direction_also_raises(self):
        record = self._real_record(self.ENV_K3)
        tampered = dict(record)
        tampered["shock_tick"] = record["shock_tick"] - 1
        with pytest.raises(ShockTickTrajectoryMismatchError):
            _assert_shock_tick_matches_trajectory(tampered)

    def test_no_detectable_transition_raises_not_silently_skips(self):
        """Weryfikacja pkt 4: brak przejscia w trajektorii -> FAIL, nie
        pominiecie testu ani ciche True."""
        constant_input = {str(t): 0.5 for t in range(10)}
        fake_record = {
            "metrics": {"input_by_tick": constant_input},
            "shock_tick": 5,
        }
        with pytest.raises(ShockTickTrajectoryMismatchError, match="niezalezna walidacja"):
            _assert_shock_tick_matches_trajectory(fake_record)

    def test_detect_prefix_end_ignores_none_ticks(self):
        input_by_tick = {"0": None, "1": 0.7, "2": 0.7, "3": 0.9}
        assert _detect_input_prefix_end(input_by_tick) == 3

    def test_detect_prefix_end_returns_none_when_all_constant(self):
        input_by_tick = {"0": 0.5, "1": 0.5, "2": 0.5}
        assert _detect_input_prefix_end(input_by_tick) is None

    def test_detect_prefix_end_returns_none_when_all_none(self):
        input_by_tick = {"0": None, "1": None}
        assert _detect_input_prefix_end(input_by_tick) is None

    def test_detect_prefix_end_works_for_arbitrary_constant_value(self):
        """Dowod, ze detekcja dziala dla DOWOLNEJ stalej wartosci prefiksu,
        nie tylko 0.2 - zero wiedzy o konkretnej liczbie (decyzja CTO pkt 6)."""
        for ref_value in (-3.7, 0.0, 1.0, 42.123456):
            input_by_tick = {"0": ref_value, "1": ref_value, "2": ref_value + 0.001}
            assert _detect_input_prefix_end(input_by_tick) == 2
