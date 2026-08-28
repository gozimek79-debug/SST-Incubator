"""B4C-2 (09), ERRATUM 1: testy komorki K4-separacja (noise_world vs
pure_noise_world, redukcja_W2 TA SAMA funkcja obu stron). Evaluator sam jest
NIEKOMPLETNY (STOP CZESCIOWY, B4C-2 (06)/(07)) - testy tutaj obejmuja
wylacznie to, co odblokowane: K4-separacja."""

import ast
import re
from pathlib import Path

import pytest

import json

from clos_scientist import pc_001_evaluator as evaluator_module
from clos_scientist.pc_001_evaluator import (
    BH_FAMILY_PATH,
    IncompleteGridError,
    UnknownEnvironmentForFloorError,
    VerdictCompositionBlockedError,
    _floor_result_for_environment,
    _reduction_by_seed,
    compose_verdict,
    k4_separation_cell,
    redukcja_w2_for_run,
)
from clos_scientist.pc_001_experiment_config import (
    EXPERIMENT_CONFIG,
    W_EARLY_TICKS,
    W_LATE_TICKS,
    FROZEN_FLOOR_NOISE_WORLD,
    FROZEN_FLOOR_PURE_NOISE_WORLD,
)

MODULE_PATH = Path(evaluator_module.__file__)
PRIMARY = EXPERIMENT_CONFIG["environments"]["primary"]
K4 = EXPERIMENT_CONFIG["environments"]["K4"]


def _synthetic_pe_trajectory(early_value: float, late_value: float) -> dict:
    """PE(t) - stala w oknie wczesnym, stala w oknie poznym (wystarcza do
    wysycenia W_EARLY_TICKS/W_LATE_TICKS bez odwolywania sie do 0/59/240/299
    jako literali w tescie - uzywa CONFIG wprost)."""
    traj = {}
    for t in W_EARLY_TICKS:
        traj[t] = early_value
    for t in W_LATE_TICKS:
        traj[t] = late_value
    return traj


def _synthetic_record(seed: int, early_value: float, late_value: float) -> dict:
    pe = _synthetic_pe_trajectory(early_value, late_value)
    return {"seed": seed, "metrics": {"prediction_error_by_tick": {str(t): v for t, v in pe.items()}}}


class TestComposeVerdictAlwaysBlocked:
    """B4C-2 (06)/(07)/(09): sciezka skladania werdyktu koncowego RZUCA
    WYJATEK, zawsze - dopoki Negative-Control Inference Review nie zapadnie.
    Zbior zablokowanych komorek WYPROWADZONY z pola kierunek_wsparcia w
    artefakcie, NIGDY z wpisanej na sztywno listy ID."""

    def test_compose_verdict_always_raises(self):
        with pytest.raises(VerdictCompositionBlockedError):
            compose_verdict()

    def test_compose_verdict_raises_regardless_of_arguments(self):
        """Sygnatura przyjmuje i ignoruje argumenty (docstring) - sprawdzone
        wprost, nie tylko zadeklarowane."""
        with pytest.raises(VerdictCompositionBlockedError):
            compose_verdict("cokolwiek", key="wartosc")

    def test_blocked_cells_message_matches_real_artifact_field(self):
        """Zbior komorek w komunikacie wyjatku MUSI zgadzac sie z tym, co
        FAKTYCZNIE jest w artefakcie DZIS - nie z zapamietana lista."""
        family = json.loads(BH_FAMILY_PATH.read_text(encoding="utf-8"))
        expected_blocked = sorted(
            c["id"] for c in family["cells_active"] if c["kierunek_wsparcia"] == "BRAK_ODRZUCENIA_H0"
        )
        with pytest.raises(VerdictCompositionBlockedError) as exc_info:
            compose_verdict()
        for cell_id in expected_blocked:
            assert cell_id in str(exc_info.value)

    def test_negative_no_hardcoded_id_list_in_source(self, monkeypatch, tmp_path):
        """Dowod, ze zbior blokady FAKTYCZNIE pochodzi z pliku, nie z listy
        wpisanej na sztywno: podmieniamy BH_FAMILY_PATH na syntetyczny
        artefakt z INNYM podzialem (3 zablokowane, nie szesc znanych ID) i
        sprawdzamy, ze komunikat wyjatku podaza za NOWA zawartoscia."""
        synthetic = {
            "cells_active": [
                {"id": "X1", "kierunek_wsparcia": "BRAK_ODRZUCENIA_H0"},
                {"id": "X2", "kierunek_wsparcia": "ODRZUCENIE_H0"},
                {"id": "X3", "kierunek_wsparcia": "BRAK_ODRZUCENIA_H0"},
            ]
        }
        fake_path = tmp_path / "synthetic_family.json"
        fake_path.write_text(json.dumps(synthetic), encoding="utf-8")
        monkeypatch.setattr(evaluator_module, "BH_FAMILY_PATH", fake_path)

        with pytest.raises(VerdictCompositionBlockedError) as exc_info:
            evaluator_module.compose_verdict()
        message = str(exc_info.value)
        assert "X1" in message and "X3" in message
        assert "X2" not in message

    def test_no_literal_count_of_blocked_cells_in_source(self):
        """Zakaz wprost (B4C-2 (09)): liczba blokowanych komorek nie ma
        prawa pojawic sie w kodzie jako literal - skan AST funkcji
        compose_verdict i klasy wyjatku."""
        import ast
        import inspect
        source = inspect.getsource(compose_verdict)
        tree = ast.parse(source)
        int_literals = {
            node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, int)
        }
        assert 6 not in int_literals


class TestFloorResultForEnvironment:
    def test_primary_uses_frozen_noise_world_floor(self):
        result = _floor_result_for_environment(PRIMARY)
        assert result["floor_env"] == FROZEN_FLOOR_NOISE_WORLD["value"]
        assert result["floor_model"] == "constant"

    def test_k4_uses_frozen_pure_noise_world_floor(self):
        result = _floor_result_for_environment(K4)
        assert result["floor_env"] == FROZEN_FLOOR_PURE_NOISE_WORLD["value"]

    def test_negative_unknown_environment_raises(self):
        with pytest.raises(UnknownEnvironmentForFloorError):
            _floor_result_for_environment("totally_unknown_environment")


class TestRedukcjaW2ForRun:
    def test_high_early_low_late_gives_positive_reduction(self):
        pe = _synthetic_pe_trajectory(early_value=0.5, late_value=0.1)
        reduction = redukcja_w2_for_run(pe, PRIMARY)
        assert reduction is not None
        assert reduction > 0

    def test_floor_limited_run_gives_none(self):
        """early_value ponizej podlogi -> PE_red~0 -> FLOOR_LIMITED -> None,
        nie zero (w2_endpoint.compute_w2_reduction)."""
        floor = FROZEN_FLOOR_NOISE_WORLD["value"]
        pe = _synthetic_pe_trajectory(early_value=floor * 0.5, late_value=floor * 0.3)
        reduction = redukcja_w2_for_run(pe, PRIMARY)
        assert reduction is None


class TestK4SeparationSharedReductionFunction:
    """Zadanie 5 (B4C-2 (09)): obie strony licza redukcja_W2 TYM SAMYM
    obiektem funkcji - test tozsamosci, nie zgodnosc wynikow (ta sama pulapka
    co przy linear_slope, B4C-2 (04))."""

    def test_ast_shows_single_call_site_to_redukcja_w2_for_run(self):
        """Skan AST calego modulu - redukcja_w2_for_run() wywolane z
        DOKLADNIE JEDNEGO miejsca (wewnatrz _reduction_by_seed), nie z
        dwoch osobnych miejsc dla noise_world/pure_noise_world."""
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        call_sites = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "redukcja_w2_for_run"
        ]
        assert len(call_sites) == 1, (
            f"redukcja_w2_for_run wywolane z {len(call_sites)} miejsc w kodzie, "
            "oczekiwano dokladnie 1 (obie strony K4-separacja musza przechodzic "
            "przez TO SAMO miejsce wywolania)"
        )

    def test_object_identity_across_both_sides(self, monkeypatch):
        """Podmienia redukcja_w2_for_run NA POZIOMIE MODULU (ten sam obiekt,
        ktory _reduction_by_seed() wyszukuje w globalnej przestrzeni nazw
        modulu przy KAZDYM wywolaniu, nie przy imporcie) na wrapper
        zapisujacy id() wywolujacego obiektu i srodowisko - uruchamia
        PRAWDZIWA sciezke k4_separation_cell()/_reduction_by_seed(), nie
        zaslepke. Dowod, ze obie strony (noise_world i pure_noise_world)
        wywoluja TEN SAM obiekt funkcji, nie dwie kopie."""
        calls = []
        original = evaluator_module.redukcja_w2_for_run

        def wrapper(pe_trajectory, environment):
            calls.append((id(wrapper), environment))
            return original(pe_trajectory, environment)

        monkeypatch.setattr(evaluator_module, "redukcja_w2_for_run", wrapper)

        noise = [_synthetic_record(seed=1, early_value=0.5, late_value=0.1)]
        pure = [_synthetic_record(seed=1, early_value=0.5, late_value=0.1)]
        evaluator_module.k4_separation_cell(noise, pure, n_genomes_expected=1)

        assert len(calls) == 2
        object_ids = {c[0] for c in calls}
        environments_seen = {c[1] for c in calls}
        assert len(object_ids) == 1, "obie strony NIE wywolaly tego samego obiektu funkcji"
        assert environments_seen == {PRIMARY, K4}

    def test_negative_of_negative_duplicated_implementation_would_be_caught(self):
        """Dowod, ze test tozsamosci powyzej NIE jest tautologiczny: symuluje
        wprost sytuacje 'dwie oddzielne implementacje, jedna per srodowisko'
        (dokladnie ten blad, ktoremu ma zapobiegac) i pokazuje, ze taka
        struktura DAJE 2 rozne id(), nie 1 - czyli prawdziwy test powyzej
        (asercja len(object_ids)==1) faktycznie moglby to zlapac, gdyby
        kod k4_separation_cell kiedykolwiek zostal tak przepisany."""
        def redukcja_dla_noise_world(pe_trajectory, environment):
            return redukcja_w2_for_run(pe_trajectory, environment)

        def redukcja_dla_pure_noise_world(pe_trajectory, environment):
            return redukcja_w2_for_run(pe_trajectory, environment)

        object_ids_if_duplicated = {id(redukcja_dla_noise_world), id(redukcja_dla_pure_noise_world)}
        assert len(object_ids_if_duplicated) == 2, (
            "sanity: dwie oddzielne funkcje (nawet o identycznym ciele) MAJA rozne id() - "
            "to jest dokladnie sytuacja, ktora test_object_identity_across_both_sides wykrylby"
        )


class TestNoShockWorldLiteralInModule:
    """ZAKAZ WPROST (ERRATUM 1, zadanie 5): zero literalu 'shock_world' w
    kodzie komorki K4-separacja. Wzorem linii 512
    (tests/test_pc_001_confirmatory_runner_guarantee.py: '0.2' not in
    no_docstring) - WYMUSZONY brak literalu, nie tylko jego nieobecnosc dzis."""

    def test_no_shock_world_in_code_outside_module_docstring(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        # Usun WYLACZNIE docstring modulu (pierwszy blok potrojnych cudzyslowow) -
        # docstring smie wyjasniac, dlaczego shock_world jest wykluczony (patrz
        # tresc tego pliku); kod (w tym docstringi funkcji/komentarze) - nie.
        module_docstring_match = re.match(r'^"""[\s\S]*?"""', source)
        assert module_docstring_match, "modul musi miec docstring do odciecia"
        code_without_module_docstring = source[module_docstring_match.end():]
        assert "shock_world" not in code_without_module_docstring

    def test_scanner_actually_detects_a_planted_literal(self):
        """Test negatywny scanera samego - dowod, ze wykrywa, nie ze zawsze
        przechodzi pusto (ta sama dyscyplina co przy innych skanerach w tym
        projekcie)."""
        planted = '"""Docstring modulu."""\ndef f():\n    x = "shock_world"\n    return x\n'
        module_docstring_match = re.match(r'^"""[\s\S]*?"""', planted)
        code_without_module_docstring = planted[module_docstring_match.end():]
        assert "shock_world" in code_without_module_docstring


class TestReductionBySeedGridCompleteness:
    def test_complete_grid_returns_one_column_per_seed(self):
        records = [
            _synthetic_record(seed=1, early_value=0.5, late_value=0.1),
            _synthetic_record(seed=1, early_value=0.4, late_value=0.1),
            _synthetic_record(seed=2, early_value=0.5, late_value=0.2),
            _synthetic_record(seed=2, early_value=0.6, late_value=0.2),
        ]
        columns = _reduction_by_seed(records, PRIMARY, n_genomes_expected=2)
        assert len(columns) == 2
        assert all(len(col) == 2 for col in columns)

    def test_negative_missing_genome_in_one_seed_raises(self):
        """Siatka niekompletna (jeden seed ma tylko 1 z oczekiwanych 2
        genomow) -> IncompleteGridError, nie ciche pominiecie."""
        records = [
            _synthetic_record(seed=1, early_value=0.5, late_value=0.1),
            _synthetic_record(seed=1, early_value=0.4, late_value=0.1),
            _synthetic_record(seed=2, early_value=0.5, late_value=0.2),
        ]
        with pytest.raises(IncompleteGridError):
            _reduction_by_seed(records, PRIMARY, n_genomes_expected=2)

    def test_negative_floor_limited_run_in_block_raises(self):
        """Jeden None (FLOOR_LIMITED) w bloku, mimo poprawnej liczby
        genomow -> IncompleteGridError (siatka WARTOSCI, nie tylko LICZBY
        rekordow, musi byc kompletna)."""
        floor = FROZEN_FLOOR_NOISE_WORLD["value"]
        records = [
            _synthetic_record(seed=1, early_value=0.5, late_value=0.1),
            _synthetic_record(seed=1, early_value=floor * 0.5, late_value=floor * 0.3),
        ]
        with pytest.raises(IncompleteGridError):
            _reduction_by_seed(records, PRIMARY, n_genomes_expected=2)


class TestK4SeparationCellEndToEnd:
    """Dane syntetyczne (zakaz uruchamiania na seedach 1001-1050, B4C-2 (01))
    - 9 blokow seedowych po obu stronach, separacja wyraznie wieksza w
    noise_world (n_genomes_expected=1 dla prostoty - test tozsamosci powyzej
    juz dowodzi, ze agregacja dziala tak samo dla wiekszej liczby genomow)."""

    def _records(self, n_seeds, early, late, seed_offset=0):
        return [
            _synthetic_record(seed=seed_offset + s, early_value=early, late_value=late)
            for s in range(n_seeds)
        ]

    def test_returns_expected_shape(self):
        noise = self._records(9, early=0.5, late=0.05, seed_offset=1)
        pure = self._records(9, early=0.5, late=0.45, seed_offset=1)
        result = k4_separation_cell(noise, pure, n_genomes_expected=1)
        assert result["cell_id"] == "K4-separacja"
        assert result["n_a"] == 9
        assert result["n_b"] == 9
        assert len(result["noise_world_block_means"]) == 9
        assert len(result["pure_noise_world_block_means"]) == 9
        assert result["test_result"]["computable"] is True

    def test_negative_incomplete_grid_propagates(self):
        noise = self._records(9, early=0.5, late=0.05, seed_offset=1)
        pure = self._records(8, early=0.5, late=0.45, seed_offset=1)  # brakuje 1 seeda
        with pytest.raises(IncompleteGridError):
            k4_separation_cell(noise, pure, n_genomes_expected=1)
