"""Regresja: Snapshot Engine jako Read-Only Observer (SPRINT_v0.10.md P2).

Formalizacja dowodu usuwalnosci z docs/spec_snapshot_observer.md (P1, ad-hoc).
Test poprawnosci CTO: usuniecie obserwatora (observe=False) NIE MOZE zmienic
zadnego pola Execution Pipeline (world.step/brain_rt.step/silent_step) - tylko
pola jawnie zdefiniowane jako f(snapshots) (Observation Pipeline) wolno
zmienic, i one MUSZA sie zmienic (dowod, ze obserwator faktycznie dostarcza
dane, nie jest cichym no-opem).

JAKAKOLWIEK roznica w polach Execution = STOP wedlug SPRINT_v0.10.md P2.
"""

import json

import pytest

from clos_academy.lesson_L1_1 import run_pattern_echo
from clos_academy.lesson_L1_2 import run_shock_recovery
from clos_kernel.snapshot_engine import SnapshotEngine

L1_1_EXECUTION_FIELDS = [
    "run_id", "lesson", "genome", "seed", "scenario",
    "primary_endpoint", "mae_stimulus_phase", "mae_silence_phase",  # SPRINT_v0.11.0.md P1: bylo mse_*
    "memory_decay_rate", "final_energy", "final_entropy", "memory_size", "passed",
]
L1_1_OBSERVATION_FIELDS = ["stability_score", "adaptation_tick", "snapshot_count"]

L1_2_EXECUTION_FIELDS = [
    "run_id", "lesson", "genome", "seed", "scenario",
    "homeostasis_band", "fraction_in_band", "final_energy", "final_entropy", "memory_size",
]
L1_2_SHOCK_ONLY_EXECUTION_FIELDS = ["t_shock", "primary_endpoint", "pre_shock_in_band"]
L1_2_OBSERVATION_FIELDS = ["stability_score", "adaptation_tick", "snapshot_count"]


def _strip_telemetry(r):
    return {k: v for k, v in r.items() if k != "telemetry"}


def _subset(result, fields):
    return {k: result[k] for k in fields}


class TestL11ObserverRemovability:
    """L1.1: 40/40 (2 genomy x 2 scenariusze x 10 seedow) - macierz identyczna z publish_L1_1.py."""

    GENOMES = ["default", "highly_plastic"]
    SCENARIOS = ["noise_world", "stable_world"]
    SEEDS = list(range(1, 11))

    @classmethod
    def _run_matrix(cls, observe):
        results = []
        for genome in cls.GENOMES:
            for scenario in cls.SCENARIOS:
                for seed in cls.SEEDS:
                    r = run_pattern_echo(genome_preset=genome, seed=seed, scenario=scenario, observe=observe)
                    results.append(_strip_telemetry(r))
        return results

    @classmethod
    def setup_class(cls):
        cls.results_on = cls._run_matrix(observe=True)
        cls.results_off = cls._run_matrix(observe=False)

    def test_execution_fields_identical_40_of_40(self):
        assert len(self.results_on) == 40 and len(self.results_off) == 40
        mismatches = []
        for i, (a, b) in enumerate(zip(self.results_on, self.results_off)):
            sub_a = json.dumps(_subset(a, L1_1_EXECUTION_FIELDS), sort_keys=True, default=str)
            sub_b = json.dumps(_subset(b, L1_1_EXECUTION_FIELDS), sort_keys=True, default=str)
            if sub_a != sub_b:
                mismatches.append(a["run_id"])
        assert not mismatches, (
            f"STOP (SPRINT_v0.10.md P2): obserwator zmienil pola Execution w runach {mismatches} - "
            "to jest ingerencja w Execution Pipeline, niedozwolona przez Warunek 1/2 CTO"
        )

    def test_observation_fields_change_when_observed(self):
        """Dowod, ze obserwator faktycznie dostarcza dane (nie cichy no-op)."""
        unchanged = []
        for a, b in zip(self.results_on, self.results_off):
            sub_a = _subset(a, L1_1_OBSERVATION_FIELDS)
            sub_b = _subset(b, L1_1_OBSERVATION_FIELDS)
            if sub_a == sub_b:
                unchanged.append(a["run_id"])
        assert not unchanged, (
            f"obserwator nie zmienil observation fields w runach {unchanged} - "
            "podejrzenie ze create_snapshot() nie jest faktycznie wolane"
        )


class TestL12ObserverRemovability:
    """L1.2: podzbior macierzy (2 genomy x 3 seedy x 2 scenariusze) - primary endpoint + reszta execution."""

    GENOMES = ["default", "highly_plastic"]
    SCENARIOS = ["shock_world", "stable_world"]
    SEEDS = [1, 2, 3]

    @classmethod
    def _run_matrix(cls, observe):
        results = []
        for genome in cls.GENOMES:
            for scenario in cls.SCENARIOS:
                for seed in cls.SEEDS:
                    r = run_shock_recovery(genome_preset=genome, seed=seed, scenario=scenario, observe=observe)
                    results.append(_strip_telemetry(r))
        return results

    @classmethod
    def setup_class(cls):
        cls.results_on = cls._run_matrix(observe=True)
        cls.results_off = cls._run_matrix(observe=False)

    def _execution_fields_for(self, result):
        fields = list(L1_2_EXECUTION_FIELDS)
        if result["scenario"] == "shock_world":
            fields += L1_2_SHOCK_ONLY_EXECUTION_FIELDS
        return fields

    def test_execution_fields_identical(self):
        mismatches = []
        for a, b in zip(self.results_on, self.results_off):
            fields = self._execution_fields_for(a)
            sub_a = json.dumps(_subset(a, fields), sort_keys=True, default=str)
            sub_b = json.dumps(_subset(b, fields), sort_keys=True, default=str)
            if sub_a != sub_b:
                mismatches.append(a["run_id"])
        assert not mismatches, (
            f"STOP (SPRINT_v0.10.md P2): obserwator zmienil pola Execution L1.2 w runach {mismatches}"
        )

    def test_primary_endpoint_identical_shock_world(self):
        """Warunek explicite z SPRINT_v0.10.md P2: 'L1.2: primary endpoint identyczny'."""
        shock_on = [r for r in self.results_on if r["scenario"] == "shock_world"]
        shock_off = [r for r in self.results_off if r["scenario"] == "shock_world"]
        assert len(shock_on) == len(shock_off) == 6
        for a, b in zip(shock_on, shock_off):
            assert a["primary_endpoint"] == b["primary_endpoint"], a["run_id"]

    def test_observation_fields_change_when_observed(self):
        unchanged = []
        for a, b in zip(self.results_on, self.results_off):
            sub_a = _subset(a, L1_2_OBSERVATION_FIELDS)
            sub_b = _subset(b, L1_2_OBSERVATION_FIELDS)
            if sub_a == sub_b:
                unchanged.append(a["run_id"])
        assert not unchanged, (
            f"obserwator nie zmienil observation fields w runach {unchanged} w L1.2"
        )


def _capture_snapshot_calls(monkeypatch):
    """Podmienia SnapshotEngine.create_snapshot na spy, ktory woLA prawdziwa
    implementacje (zachowanie bez zmian) i dodatkowo zapisuje (tick,
    prediction_error) z kazdego wywolania - do inspekcji pelnej trajektorii."""
    calls = []
    original = SnapshotEngine.create_snapshot

    def spy(self, *args, **kwargs):
        snapshot = original(self, *args, **kwargs)
        calls.append((kwargs.get("tick"), kwargs.get("prediction_error")))
        return snapshot

    monkeypatch.setattr(SnapshotEngine, "create_snapshot", spy)
    return calls


class TestPredictionErrorSnapshotCoverage:
    """PC KROK 2: Snapshot.prediction_error - pole obserwacyjne (Opcja B).

    Dowod usuwalnosci (twardy warunek CTO): observe=False nie moze wywolac
    create_snapshot ani razu (wiec prediction_error nigdzie sie nie pojawia -
    execution fields juz pokryte przez TestL11/L12ObserverRemovability
    powyzej). observe=True musi dac trajektorie PRZEZ CALY przebieg (wszystkie
    ticki, obie fazy), nie tylko ostatnie 100 - to jest dokladnie problem,
    ktory PC KROK 1 zidentyfikowal w prediction_error_buffer (precision.py:27
    obcina do 100 wpisow).
    """

    def test_l1_1_observe_false_creates_zero_snapshots(self, monkeypatch):
        calls = _capture_snapshot_calls(monkeypatch)
        run_pattern_echo(genome_preset="default", seed=1, scenario="noise_world", observe=False)
        assert calls == [], (
            "STOP: create_snapshot wywolane mimo observe=False - obserwator nie jest usuwalny"
        )

    def test_l1_1_observe_true_covers_full_trajectory_both_phases(self, monkeypatch):
        calls = _capture_snapshot_calls(monkeypatch)
        result = run_pattern_echo(
            genome_preset="default", seed=1, scenario="noise_world",
            stimulus_ticks=100, silence_ticks=100, observe=True,
        )
        total_ticks = 200
        assert len(calls) == total_ticks, (
            f"oczekiwano snapshotu na kazdy z {total_ticks} tickow, dostano {len(calls)}"
        )
        by_tick = {tick: pe for tick, pe in calls}

        # Gdyby dane pochodzily z prediction_error_buffer (Core, obciety do
        # 100), po 200 tickach przetrwalyby TYLKO ticki 100-199. Tick 50 (w
        # fazie bodzca, dawno "wypchniety" z takiego bufora) MUSI miec
        # niepusta wartosc, zeby udowodnic, ze snapshot NIE czyta bufora.
        assert by_tick.get(50) is not None, (
            "tick 50 ma prediction_error=None - trajektoria nie siega poza "
            "ostatnie 100 tickow, dokladnie problem z PC KROK 1"
        )
        assert by_tick.get(99) is not None, "ostatni tick fazy bodzca (99) bez prediction_error"

        # ZNALEZISKO (koryguje wlasna korekte do PC KROK 1): w L1.1 faza
        # ciszy idzie przez silent_step() -> partial_step(skip={PERCEIVE}),
        # ktory jawnie ustawia brain.last_input = None
        # (clos_brain/brain_runtime.py:140) - last_input NIE jest "zamrozony
        # z ostatniego widzianego bodzca", tylko wyzerowany. compute_error()
        # (precision.py:18-19) przy last_input=None robi wczesny return bez
        # zmiany brain - PE Core NAPRAWDE nie jest liczony w fazie ciszy L1.1
        # (to fakt o dzisiejszym Core, nie blad tego obserwatora). Obserwator
        # wiernie to odzwierciedla: prediction_error=None w tej fazie.
        assert by_tick.get(150) is None, (
            "tick 150 (faza ciszy L1.1) ma prediction_error != None - "
            "niespodziewane, skoro last_input jest zerowany przez partial_step(skip=PERCEIVE); "
            "sprawdz, czy zachowanie Core sie nie zmienilo"
        )
        # Sanity: |a-b| >= 0 zawsze; i nie jest to staly placeholder (dowod,
        # ze to prawdziwa trajektoria, nie no-op zwracajacy jedna wartosc).
        non_none = [pe for pe in by_tick.values() if pe is not None]
        assert non_none, "brak jakiejkolwiek niepustej wartosci prediction_error w calym przebiegu"
        assert all(pe >= 0 for pe in non_none)
        assert len(set(non_none)) > 1, (
            "prediction_error jest stala dla wszystkich tickow - podejrzenie stub/no-op"
        )

    def test_l1_2_observe_true_covers_full_trajectory(self, monkeypatch):
        calls = _capture_snapshot_calls(monkeypatch)
        run_shock_recovery(genome_preset="default", seed=1, scenario="shock_world", observe=True)
        assert len(calls) > 100, "L1.2: oczekiwano trajektorii dluzszej niz obciety bufor Core (100)"
        by_tick = {tick: pe for tick, pe in calls}
        early_ticks_with_data = [t for t in by_tick if t < 50 and by_tick[t] is not None]
        assert early_ticks_with_data, (
            "brak niepustych prediction_error we wczesnych tickach (<50) w L1.2"
        )


def _capture_raw_snapshot_fields(monkeypatch):
    """Jak _capture_snapshot_calls, ale zapisuje (tick, prediction, input) -
    PC-001 B2. Osobny helper (nie rozszerzam _capture_snapshot_calls), zeby
    nie ruszac istniejacych, juz zielonych testow PC KROK 2 powyzej."""
    calls = []
    original = SnapshotEngine.create_snapshot

    def spy(self, *args, **kwargs):
        snapshot = original(self, *args, **kwargs)
        calls.append((kwargs.get("tick"), kwargs.get("prediction"), kwargs.get("input")))
        return snapshot

    monkeypatch.setattr(SnapshotEngine, "create_snapshot", spy)
    return calls


class TestRawPredictionInputSnapshotCoverage:
    """PC-001 B2: Snapshot.prediction / Snapshot.input - surowe dane
    obserwacyjne (D-005 pkt 5, zasada O-001), wymagane dla K5 (ablacja
    surogatowa) i K6 (korelacja Spearmana prediction/input) z Aneksu 1.

    Test usuwalnosci (twardy warunek): observe=False -> zero wywolan
    create_snapshot (execution fields juz pokryte przez
    TestL11/L12ObserverRemovability - te testy tylko dowodza, ze NOWE pola
    tez nie przeciekaja gdy obserwator wylaczony). observe=True -> prediction
    i input obecne przez cale mierzalne okno (nie tylko L1.2, gdzie PERCEIVE
    nigdy nie jest pomijane - to jest silniejszy przypadek niz L1.1's faza
    ciszy, patrz TestPredictionErrorSnapshotCoverage powyzej)."""

    def test_l1_1_observe_false_no_raw_fields_leak(self, monkeypatch):
        calls = _capture_raw_snapshot_fields(monkeypatch)
        run_pattern_echo(genome_preset="default", seed=1, scenario="noise_world", observe=False)
        assert calls == [], (
            "STOP: create_snapshot wywolane mimo observe=False - "
            "prediction/input nie sa usuwalne"
        )

    def test_l1_1_observe_true_prediction_and_input_present_in_stimulus_phase(self, monkeypatch):
        calls = _capture_raw_snapshot_fields(monkeypatch)
        run_pattern_echo(
            genome_preset="default", seed=1, scenario="noise_world",
            stimulus_ticks=100, silence_ticks=100, observe=True,
        )
        by_tick = {tick: (pred, inp) for tick, pred, inp in calls}

        for t in [1, 50, 99]:
            pred, inp = by_tick[t]
            assert pred is not None, f"tick {t}: Snapshot.prediction jest None w fazie bodzca"
            assert inp is not None, f"tick {t}: Snapshot.input jest None w fazie bodzca"

        # Faza ciszy (last_input=None przez partial_step(skip=PERCEIVE), patrz
        # CURRENT_SCIENTIFIC_LIMITS §8) - input MUSI byc None, spojnie z tym,
        # ze prediction_error tez jest None tam (juz udowodnione wyzej).
        pred_silence, inp_silence = by_tick[150]
        assert inp_silence is None, (
            "tick 150 (faza ciszy L1.1): Snapshot.input != None - "
            "niespodziewane, last_input powinien byc zerowany"
        )

    def test_l1_2_observe_true_prediction_and_input_present_full_window(self, monkeypatch):
        """L1.2 nigdy nie pomija PERCEIVE - silniejszy dowod niz L1.1: brak
        wyjatkow, prediction/input obecne na KAZDYM ticku calego przebiegu."""
        calls = _capture_raw_snapshot_fields(monkeypatch)
        run_shock_recovery(genome_preset="default", seed=1, scenario="shock_world", observe=True)
        assert len(calls) > 100
        missing_pred = [t for t, pred, inp in calls if pred is None]
        missing_input = [t for t, pred, inp in calls if inp is None]
        assert not missing_pred, f"prediction=None na tickach {missing_pred[:5]}... w L1.2"
        assert not missing_input, f"input=None na tickach {missing_input[:5]}... w L1.2"

    def test_prediction_error_consistent_with_raw_prediction_and_input(self, monkeypatch):
        """Zero przeliczania: Snapshot.prediction/input MUSZA byc dokladnie
        tissue.last_prediction/last_input (nie zaokraglone, nie pochodna
        wielkosc) - dowod posredni: |prediction-input| == prediction_error
        (juz liczone niezaleznie w call-site) na tym samym ticku, wszedzie
        gdzie oba sa nie-None. Jeden spy, oba zestawy pol naraz - z tego
        samego przebiegu, zeby porownanie mialo sens."""
        """Wlasciwy test spojnosci (jeden spy, oba zestawy pol naraz)."""
        calls = []
        original = SnapshotEngine.create_snapshot

        def spy(self, *args, **kwargs):
            snapshot = original(self, *args, **kwargs)
            calls.append((
                kwargs.get("tick"),
                kwargs.get("prediction_error"),
                kwargs.get("prediction"),
                kwargs.get("input"),
            ))
            return snapshot

        monkeypatch.setattr(SnapshotEngine, "create_snapshot", spy)
        run_shock_recovery(genome_preset="default", seed=3, scenario="shock_world", observe=True)

        checked = 0
        for tick, pred_err, pred, inp in calls:
            if pred_err is None:
                continue
            assert pred is not None and inp is not None, (
                f"tick {tick}: prediction_error obecny, ale prediction/input None"
            )
            assert abs(abs(pred - inp) - pred_err) < 1e-9, (
                f"tick {tick}: |prediction-input|={abs(pred - inp)} != "
                f"prediction_error={pred_err} - niespojnosc miedzy polami"
            )
            checked += 1
        assert checked > 100, "za malo tickow ze skompletowanymi polami do sensownej weryfikacji"
