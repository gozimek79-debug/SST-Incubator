"""B4C-2 (09), ERRATUM 1: testy komorki K4-separacja (noise_world vs
pure_noise_world, redukcja_W2 TA SAMA funkcja obu stron). Evaluator sam jest
NIEKOMPLETNY (STOP CZESCIOWY, B4C-2 (06)/(07)) - testy tutaj obejmuja
wylacznie to, co odblokowane: K4-separacja."""

import ast
import inspect
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
    _margin_for_cell,
    _reduction_by_seed,
    _beta_raw_for_run,
    _w_early_late_red_for_run,
    _paired_w_early_late_by_seed,
    _k3a_pre_post_means_for_run,
    _k3a_diff_by_seed,
    _spearman_rho_for_run,
    compose_verdict,
    e_beta_components_for_run,
    e_beta_for_run,
    e_red_for_run,
    k1_equivalence_cell,
    k4_equivalence_cell,
    k4_separation_cell,
    k5_equivalence_cell,
    redukcja_w2_for_run,
    warunek_a_cell,
    warunek_b_cell,
    k3a_warunek1_cell,
    k6_cell,
)
from clos_scientist.pc_001_experiment_config import (
    EXPERIMENT_CONFIG,
    W_EARLY_TICKS,
    W_LATE_TICKS,
    FROZEN_FLOOR_NOISE_WORLD,
    FROZEN_FLOOR_PURE_NOISE_WORLD,
    CONDITION_B_REDUCTION_THRESHOLD,
    k3a_pre_post_shock_windows,
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
        FAKTYCZNIE jest w artefakcie DZIS - nie z zapamietana lista.
        B4C-2 (15): warunek blokady to ROWNOWAZNOSC BEZ zamknietego power
        check (pole 'equivalence_power_check_closed' nieobecne/False) -
        BRAK_ODRZUCENIA_H0 juz nie istnieje jako wartosc per komorka."""
        family = json.loads(BH_FAMILY_PATH.read_text(encoding="utf-8"))
        expected_blocked = sorted(
            c["id"] for c in family["cells_active"]
            if c["kierunek_wsparcia"] == "ROWNOWAZNOSC" and not c.get("equivalence_power_check_closed", False)
        )
        assert expected_blocked != [], "test bezprzedmiotowy, jesli artefakt nie ma zadnej blokowanej komorki"
        with pytest.raises(VerdictCompositionBlockedError) as exc_info:
            compose_verdict()
        for cell_id in expected_blocked:
            assert cell_id in str(exc_info.value)

    def test_negative_guard_fails_loud_on_artifact_without_any_rownowaznosc_cell(self):
        """B4C-2 (17), znalezisko CTO: 'zero dopasowan = ciche PASS' wrocilo
        w innym miejscu - test_blocked_cells_message_matches_real_artifact_field
        wyprowadza expected_blocked z artefaktu i PETLI po nim; gdyby artefakt
        (hipotetycznie) nie mial ANI JEDNEJ komorki ROWNOWAZNOSC, ta petla
        wykonalaby sie zero razy i test przeszedlby, NIE dlatego, ze cos
        sprawdzil, tylko dlatego, ze nie mial czego sprawdzac. Ten test
        dowodzi, ze guard 'assert expected_blocked != []' FAKTYCZNIE lapie
        ten przypadek - nie jest deklaracja bez pokrycia."""
        synthetic_family_without_rownowaznosc = {
            "cells_active": [
                {"id": "Y1", "kierunek_wsparcia": "ODRZUCENIE_H0"},
                {"id": "Y2", "kierunek_wsparcia": "ODRZUCENIE_H0"},
            ]
        }
        expected_blocked = sorted(
            c["id"] for c in synthetic_family_without_rownowaznosc["cells_active"]
            if c["kierunek_wsparcia"] == "ROWNOWAZNOSC" and not c.get("equivalence_power_check_closed", False)
        )
        with pytest.raises(AssertionError, match="bezprzedmiotowy"):
            assert expected_blocked != [], "test bezprzedmiotowy, jesli artefakt nie ma zadnej blokowanej komorki"

    def test_negative_no_hardcoded_id_list_in_source(self, monkeypatch, tmp_path):
        """Dowod, ze zbior blokady FAKTYCZNIE pochodzi z pliku, nie z listy
        wpisanej na sztywno: podmieniamy BH_FAMILY_PATH na syntetyczny
        artefakt z INNYM podzialem (dwie zablokowane ROWNOWAZNOSC bez power
        check, jedna ROWNOWAZNOSC JUZ z zamknietym power check, jedna
        ODRZUCENIE_H0) i sprawdzamy, ze komunikat wyjatku podaza za NOWA
        zawartoscia - w tym poprawnie WYKLUCZA komorke z zamknietym power
        check, nie tylko dodaje nowe ID."""
        synthetic = {
            "cells_active": [
                {"id": "X1", "kierunek_wsparcia": "ROWNOWAZNOSC"},
                {"id": "X2", "kierunek_wsparcia": "ODRZUCENIE_H0"},
                {"id": "X3", "kierunek_wsparcia": "ROWNOWAZNOSC"},
                {"id": "X4", "kierunek_wsparcia": "ROWNOWAZNOSC", "equivalence_power_check_closed": True},
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
        assert "X4" not in message

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


ALLOWED_SHOCK_WORLD_FUNCTIONS = {"_k3a_pre_post_means_for_run", "k3a_warunek1_cell"}


def _shock_world_violations(source: str, allowed_functions: set) -> list:
    """Skan CALEGO modulu (poza docstringiem modulu) w poszukiwaniu literalu
    'shock_world' POZA jawnie dozwolona lista funkcji. Dla kazdej linii z
    trafieniem ustala, KTORA(-e) funkcja(-e) AST ja obejmuja (po numerze
    linii, node.lineno..node.end_lineno) - trafienie jest naruszeniem
    WYLACZNIE, gdy ZADNA obejmujaca funkcja nie jest na liscie."""
    tree = ast.parse(source)
    ranges = {
        node.name: (node.lineno, node.end_lineno)
        for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    module_docstring_match = re.match(r'^"""[\s\S]*?"""', source)
    docstring_end_line = source[:module_docstring_match.end()].count("\n") + 1 if module_docstring_match else 0

    violations = []
    for i, line in enumerate(source.splitlines(), start=1):
        if i <= docstring_end_line or "shock_world" not in line:
            continue
        containing = sorted(name for name, (start, end) in ranges.items() if start <= i <= end)
        if not any(name in allowed_functions for name in containing):
            violations.append({"line": i, "text": line.strip(), "functions": containing})
    return violations


class TestNoShockWorldLiteralOutsideAllowedFunctions:
    """ZAKAZ WPROST (ERRATUM 1, zadanie 5): zero literalu 'shock_world' w
    kodzie komorki K4-separacja - WYMUSZONY, nie tylko jego nieobecnosc dzis.

    B4C-2 (21), korekta CTO wobec (20): zawezenie do inspect.getsource(
    k4_separation_cell) usuwalo ZASIEG, nie tylko nadmiar - funkcje wolane
    PRZEZ k4_separation_cell (_reduction_by_seed, _floor_result_for_environment)
    sa POZA cialem tej funkcji, wiec literal tam wstawiony nie byl juz lapany,
    mimo ze naleza do sciezki, ktora komorka faktycznie wykonuje. Poprawka:
    skan CALEGO modulu z JAWNA, zadeklarowana lista funkcji, ktorym wolno
    nazwac shock_world (dzis wylacznie sciezka K3a-warunek1) - "zwezenie
    straznika jest dopuszczalne, gdy usuwa NADMIAR, i niedopuszczalne, gdy
    usuwa ZASIEG"."""

    def test_real_module_has_no_shock_world_outside_allowed_functions(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        violations = _shock_world_violations(source, ALLOWED_SHOCK_WORLD_FUNCTIONS)
        assert violations == [], violations

    def test_allowed_list_is_declared_not_derived_from_name_or_prefix(self):
        """Lista jest ZBIOR LITERALI wpisany wprost, nie wyprowadzony z
        prefiksu/konwencji nazewniczej - dowod: obejmuje dwie funkcje o
        ROZNYCH wzorcach nazw ('_k3a_...' z podkreslnikiem wiodacym,
        'k3a_warunek1_cell' bez) - regex/prefiks 'zaczyna sie od k3a' dalby
        TEN SAM zbior tutaj przez przypadek, wiec dowod idzie przez typ
        (zbior literali w kodzie testu), nie przez tresc."""
        assert isinstance(ALLOWED_SHOCK_WORLD_FUNCTIONS, set)
        assert ALLOWED_SHOCK_WORLD_FUNCTIONS == {"_k3a_pre_post_means_for_run", "k3a_warunek1_cell"}

    def test_negative_literal_in_floor_result_for_environment_is_caught(self):
        """Dokladnie przypadek, ktorego zawezenie z (20) NIE lapalo: literal
        w _floor_result_for_environment - wolanej PRZEZ k4_separation_cell,
        ale POZA jej cialem funkcji, i NIE na liscie dozwolonych."""
        source = MODULE_PATH.read_text(encoding="utf-8")
        marker = 'def _floor_result_for_environment(environment: str) -> Dict[str, Any]:\n    """floor_result'
        assert marker in source, "wzorzec podmiany nie pasuje do biezacego kodu - dostosuj test"
        planted = source.replace(marker, marker.replace('"""floor_result', '"""floor_result shock_world'), 1)
        violations = _shock_world_violations(planted, ALLOWED_SHOCK_WORLD_FUNCTIONS)
        assert violations != []
        assert any("_floor_result_for_environment" in v["functions"] for v in violations)

    def test_negative_new_undeclared_function_using_shock_world_is_caught(self):
        """Nowa funkcja (nieznana liscie) uzywajaca shock_world FAILuje,
        dopoki ktos swiadomie jej nie dopisze do ALLOWED_SHOCK_WORLD_FUNCTIONS -
        dowod na SYNTETYCZNYM zrodle, nie na prawdziwym pliku."""
        planted = (
            '"""Docstring modulu."""\n\n\n'
            'def nowa_funkcja_ktorej_nie_ma_na_liscie():\n'
            '    """Uzywa shock_world bez zgody."""\n'
            '    return "shock_world"\n'
        )
        violations = _shock_world_violations(planted, ALLOWED_SHOCK_WORLD_FUNCTIONS)
        assert violations != []
        assert any("nowa_funkcja_ktorej_nie_ma_na_liscie" in v["functions"] for v in violations)

    def test_negative_of_negative_allowed_function_is_not_falsely_flagged(self):
        """Sanity w druga strone: funkcja FAKTYCZNIE na liscie nie jest
        lapana - dowod, ze kontrola nie FAILuje wszystkiego na slepo."""
        planted = (
            '"""Docstring modulu."""\n\n\n'
            'def k3a_warunek1_cell():\n'
            '    """Legalnie o shock_world."""\n'
            '    return "shock_world"\n'
        )
        violations = _shock_world_violations(planted, ALLOWED_SHOCK_WORLD_FUNCTIONS)
        assert violations == []


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


TICKS_TOTAL = EXPERIMENT_CONFIG["protocol"]["ticks_total"]


def _full_grid_pe_trajectory(pe_by_tick) -> dict:
    """PE(t) na PELNEJ siatce 0..ticks_total-1, z callable pe_by_tick(t)."""
    return {t: pe_by_tick(t) for t in range(TICKS_TOTAL)}


def _full_grid_record(seed: int, pe_by_tick, prediction_by_tick=None, input_by_tick=None) -> dict:
    """Rekord ze SCHEMATEM v3 (prediction/input/prediction_error per tick) -
    domyslnie prediction=0, input=pe_by_tick(t) (PE=|0-input|=input, wygodne
    dla testow, ktore nie zaleza od K1/K5)."""
    pe = {str(t): pe_by_tick(t) for t in range(TICKS_TOTAL)}
    pred = prediction_by_tick or (lambda t: 0.0)
    inp = input_by_tick or (lambda t: pe_by_tick(t))
    return {
        "seed": seed,
        "metrics": {
            "prediction_error_by_tick": pe,
            "prediction_by_tick": {str(t): pred(t) for t in range(TICKS_TOTAL)},
            "input_by_tick": {str(t): inp(t) for t in range(TICKS_TOTAL)},
        },
    }


class TestEBetaComponentsForRun:
    """B4C-2 (15): E_beta = beta_raw * tick_span / W_early_red, POLICZONE
    PER PRZEBIEG, tick_span WYPROWADZONY z siatki (nie literal)."""

    def test_expected_tick_span_constant_is_299(self):
        """Wyprowadzone z EXPERIMENT_CONFIG, nie wpisane - ale WARTOSC przy
        dzisiejszym protokole (300 tickow) ma wynosic 299."""
        assert evaluator_module._EXPECTED_TICK_SPAN == 299
        assert evaluator_module._EXPECTED_TICK_SPAN == TICKS_TOTAL - 1

    def test_happy_path_constant_pe_gives_zero_beta(self):
        """PE(t) stale -> beta_raw=0 (var(t)!=0, ticki rozne, ale wszystkie
        y rowne) -> E_beta=0. Dowod, ze pelna siatka jest AKCEPTOWANA i
        cala rura (floor -> linear_slope -> normalizacja) dziala."""
        pe_trajectory = _full_grid_pe_trajectory(lambda t: 0.5)
        components = e_beta_components_for_run(pe_trajectory, PRIMARY)
        assert components is not None
        beta_raw, w_early_red, e_beta = components
        assert abs(beta_raw) < 1e-9
        assert abs(e_beta) < 1e-9
        assert w_early_red > 0

    def test_happy_path_linear_trend_matches_manual_computation(self):
        """PE(t) = 0.5 - 0.001*t (trend liniowy jednoznaczny) - E_beta
        policzony niezaleznie z tych samych skladowych (bez ponownego
        wywolania linear_slope - to bylaby tautologia), przez odjecie
        floor_env i policzenie sredniej W_EARLY_TICKS recznie."""
        pe_fn = lambda t: 0.5 - 0.001 * t
        pe_trajectory = _full_grid_pe_trajectory(pe_fn)
        components = e_beta_components_for_run(pe_trajectory, PRIMARY)
        assert components is not None
        beta_raw, w_early_red, e_beta = components

        floor_env = FROZEN_FLOOR_NOISE_WORLD["value"]
        pe_red_early = [max(0.0, pe_fn(t) - floor_env) for t in W_EARLY_TICKS]
        expected_w_early_red = sum(pe_red_early) / len(pe_red_early)
        assert abs(w_early_red - expected_w_early_red) < 1e-6
        assert beta_raw < 0  # trend malejacy
        assert e_beta == pytest.approx(beta_raw * 299 / w_early_red, abs=1e-9)

    def test_truncated_grid_returns_none_not_wrong_tick_span(self):
        """Weryfikacja pkt 2 (B4C-2 (15)): siatka SKROCONA (tylko pierwsze
        150 tickow) -> None, NIE policzony tick_span=149 po cichu."""
        pe_trajectory = {t: 0.5 - 0.001 * t for t in range(150)}
        assert e_beta_components_for_run(pe_trajectory, PRIMARY) is None

    def test_grid_with_gap_returns_none(self):
        """Siatka tej samej DLUGOSCI (300 wpisow) ale z DZIURA (brakuje
        ticka 150, jest za to duplikat na koncu) - dowod, ze kontrola
        patrzy na ZBIOR tickow, nie tylko na len()."""
        pe_trajectory = {t: 0.5 for t in range(TICKS_TOTAL) if t != 150}
        pe_trajectory[300] = 0.5  # zamiast 150 - ten sam rozmiar (299), zly zbior
        assert e_beta_components_for_run(pe_trajectory, PRIMARY) is None

    def test_w_early_red_zero_or_negative_returns_none(self):
        """PE(t) ponizej floor_env przez cale okno wczesne -> PE_red=0
        wszedzie w oknie wczesnym -> W_early_red=0 -> None (NIE epsilon)."""
        floor_env = FROZEN_FLOOR_NOISE_WORLD["value"]
        pe_trajectory = _full_grid_pe_trajectory(lambda t: floor_env / 2)
        assert e_beta_components_for_run(pe_trajectory, PRIMARY) is None

    def test_e_beta_for_run_matches_third_component(self):
        pe_trajectory = _full_grid_pe_trajectory(lambda t: 0.5 - 0.001 * t)
        components = e_beta_components_for_run(pe_trajectory, PRIMARY)
        assert e_beta_for_run(pe_trajectory, PRIMARY) == components[2]

    def test_e_beta_for_run_none_when_components_none(self):
        pe_trajectory = {t: 0.5 - 0.001 * t for t in range(150)}
        assert e_beta_for_run(pe_trajectory, PRIMARY) is None


class TestERedForRunIsRedukcjaW2ForRun:
    """B4C-2 (15): e_red_for_run JEST redukcja_w2_for_run (wiazanie nazwy,
    nie nowa implementacja) - ERRATUM 3: 'E_red = redukcja_W2'."""

    def test_same_object(self):
        assert e_red_for_run is redukcja_w2_for_run


class TestMarginForCell:
    """B4C-2 (15), zadanie 4: 'Granice biore sie z artefaktu, nie ze stalej
    w evaluatorze.' - _margin_for_cell CZYTA plik, nie zwraca literalu."""

    @pytest.mark.parametrize("cell_id", ["K1-A", "K1-B", "K4-A", "K4-B", "K5-A", "K5-B"])
    def test_reads_real_margin_from_artifact(self, cell_id):
        family = json.loads(BH_FAMILY_PATH.read_text(encoding="utf-8"))
        expected = next(c for c in family["cells_active"] if c["id"] == cell_id)["equivalence_margin_c"]
        assert _margin_for_cell(cell_id) == expected

    def test_no_hardcoded_margin_literal_in_module_source(self):
        """Skan zrodla: literal 0.10 (ani 0.1) nie ma prawa pojawic sie w
        wywolaniach _equivalence_result - margines ZAWSZE przez
        _margin_for_cell()."""
        source = MODULE_PATH.read_text(encoding="utf-8")
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        assert "0.10" not in no_docstrings
        assert re.search(r"(?<![\w.])0\.1(?![\w0-9])", no_docstrings) is None


class TestPendingFullFamilyBHSentinel:
    """B4C-2 (16), korekta CTO: 'bh_adjusted_result'/'equivalence_supported'
    NIE MAJA byc None - None w tym repo juz znaczy 'nie da sie policzyc dla
    tych danych' (w2_endpoint.compute_w2_reduction). Uzycie go tez dla
    'jeszcze nie zaimplementowane' nakladaloby dwa rozne stany na jedna
    reprezentacje - ktos czytajacy None przeczytalby to jako fakt o danych,
    nie o stanie implementacji. Ten test PRZYPINA jawny znacznik, zeby
    przyszla proba 'wypelnienia' tych pol przy okazji zostala zlapana."""

    def test_sentinel_is_not_none(self):
        assert evaluator_module.PENDING_FULL_FAMILY_BH is not None

    def test_sentinel_is_a_named_string_not_a_bare_bool_or_number(self):
        """Wartosc ma byc SAMOOPISUJACA - ktos czytajacy ja bez kontekstu
        (np. w zrzucie JSON artefaktu) ma zobaczyc od razu, ze to stan
        oczekiwania, nie liczba/flaga."""
        assert isinstance(evaluator_module.PENDING_FULL_FAMILY_BH, str)
        assert "PENDING" in evaluator_module.PENDING_FULL_FAMILY_BH

    @pytest.mark.parametrize("cell_fn,args,records_kind", [
        (k4_equivalence_cell, ("A",), "plain"),
        (k4_equivalence_cell, ("B",), "plain"),
        (k5_equivalence_cell, ("A",), "ablation"),
        (k5_equivalence_cell, ("B",), "ablation"),
    ])
    def test_all_equivalence_cells_use_sentinel_not_none(self, cell_fn, args, records_kind):
        if records_kind == "ablation":
            # K5 ablacja liczy |0.5-input| - input musi byc daleko od 0.5,
            # inaczej PE_ablated wypada ponizej floor_env wszedzie (patrz
            # test_k5_a_uses_ablation_not_recorded_prediction powyzej).
            records = [
                _full_grid_record(5001 + s, lambda t: 999.0, input_by_tick=lambda t: 0.9 - 0.0001 * t)
                for s in range(9)
            ]
        else:
            records = [_full_grid_record(5001 + s, lambda t: 0.5 - 0.0001 * t) for s in range(9)]
        result = cell_fn(*args, records, n_genomes_expected=1)
        assert result["bh_adjusted_result"] == evaluator_module.PENDING_FULL_FAMILY_BH
        assert result["equivalence_supported"] == evaluator_module.PENDING_FULL_FAMILY_BH
        assert result["bh_adjusted_result"] is not None
        assert result["equivalence_supported"] is not None

    def test_negative_none_would_be_indistinguishable_from_w2_endpoint_meaning(self):
        """Dokumentuje WPROST powod zakazu None: compute_w2_reduction zwraca
        redukcja=None dla przebiegu, ktorego NIE DA SIE policzyc (FLOOR_
        LIMITED/INSUFFICIENT_DATA) - 'brak wyniku, nie wynik zerowy'. Gdyby
        _equivalence_result tez zwracal None, nie dalo by sie odroznic
        'dane sie nie licza' od 'implementacja jeszcze nie gotowa' patrzac
        wylacznie na wartosc pola."""
        from clos_scientist.w2_endpoint import compute_w2_reduction
        insufficient = compute_w2_reduction({})
        assert insufficient["reduction"] is None  # "nie da sie policzyc" - prawdziwe znaczenie None tutaj
        assert evaluator_module.PENDING_FULL_FAMILY_BH is not None  # naszego stanu NIE reprezentuje None


class TestEquivalenceCellsEndToEnd:
    """Dane syntetyczne (zakaz uruchamiania na seedach 1001-1050) - siatka
    PELNA (0..299) wymagana dla czesci A (E_beta); n_genomes_expected=1 dla
    prostoty (tozsamosc agregacji z wieksza liczba genomow juz dowiedziona
    dla K4-separacja powyzej)."""

    def _records(self, n_seeds, pe_fn, seed_offset=2001):
        return [_full_grid_record(seed_offset + s, pe_fn) for s in range(n_seeds)]

    def test_k4_a_returns_required_fields(self):
        records = self._records(9, lambda t: 0.5 - 0.0001 * t)
        result = k4_equivalence_cell("A", records, n_genomes_expected=1)
        assert result["cell_id"] == "K4-A"
        assert result["effect_metric"] == "E_beta"
        for key in ("observed_effect", "equivalence_lower", "equivalence_upper",
                    "p_lower", "p_upper", "p_equivalence", "bh_adjusted_result",
                    "equivalence_supported", "beta_raw", "W_early_red", "tick_span"):
            assert key in result
        assert result["tick_span"] == 299
        assert result["equivalence_lower"] == -result["equivalence_upper"]
        # B4C-2 (16), korekta CTO: NIE None (w tym repo None juz znaczy
        # "nie da sie policzyc dla tych danych", w2_endpoint) - jawny
        # znacznik odrozniajacy stan IMPLEMENTACJI od wlasciwosci danych.
        assert result["bh_adjusted_result"] == evaluator_module.PENDING_FULL_FAMILY_BH
        assert result["equivalence_supported"] == evaluator_module.PENDING_FULL_FAMILY_BH
        assert result["bh_adjusted_result"] is not None
        assert result["equivalence_supported"] is not None

    def test_k4_b_returns_required_fields_without_group_a_extras(self):
        records = self._records(9, lambda t: 0.5 - 0.0001 * t)
        result = k4_equivalence_cell("B", records, n_genomes_expected=1)
        assert result["cell_id"] == "K4-B"
        assert result["effect_metric"] == "redukcja_W2"
        assert "beta_raw" not in result
        assert "tick_span" not in result

    def test_k5_a_uses_ablation_not_recorded_prediction(self):
        """K5 ablacja: prediction ZAPISANA w rekordzie jest IGNOROWANA -
        efekt liczony z |0.5-input|, nie z faktycznej predykcji. input(t)
        celowo DALEKO od 0.5 (0.9-0.0001t), zeby PE_ablated=|0.5-input|
        przekraczal floor_env (~0.096) - blisko 0.5 dawaloby PE_ablated
        ponizej podlogi wszedzie, W_early_red=0, i test niczego by nie
        dowodzil (fałszywie wygladalby na NONCOMPUTABLE)."""
        input_fn = lambda t: 0.9 - 0.0001 * t
        records = [
            _full_grid_record(2001 + s, lambda t: 999.0, input_by_tick=input_fn)
            for s in range(9)
        ]  # prediction_error_by_tick celowo bzdurne (999.0) - K5 go ignoruje
        result = k5_equivalence_cell("A", records, n_genomes_expected=1)
        assert result["cell_id"] == "K5-A"
        assert result["effect_metric"] == "E_beta"
        assert result["computable"] is True

    def test_k1_a_records_shuffle_provenance(self):
        records = self._records(9, lambda t: 0.5 - 0.0001 * t)
        result = k1_equivalence_cell("A", records, n_genomes_expected=1)
        assert result["cell_id"] == "K1-A"
        assert set(result["k1_shuffle_by_seed"].keys()) == {r["seed"] for r in records}
        for entry in result["k1_shuffle_by_seed"].values():
            assert entry["algorithm"] == "PC001_K1_SHUFFLE_V1"
            assert isinstance(entry["k1_shuffle_seed"], int)
            assert isinstance(entry["permutation_digest"], str)

    def test_k1_shares_one_permutation_across_genomes_in_same_seed_block(self):
        """B4C-1 (05): JEDNA permutacja per seed, dzielona przez wszystkie
        genomy tego seeda - dwa 'genomy' (dwa rekordy) tego samego seeda
        musza dostac IDENTYCZNY digest permutacji."""
        seed = 3001
        records = [_full_grid_record(seed, lambda t: 0.5 - 0.0001 * t) for _ in range(3)]
        # _effect_by_seed wymaga n_genomes_expected dopasowanego do liczby
        # rekordow per seed - tu wszystkie 3 rekordy dziela JEDEN seed.
        result = k1_equivalence_cell("A", records, n_genomes_expected=3)
        assert len(result["k1_shuffle_by_seed"]) == 1
        digest = result["k1_shuffle_by_seed"][seed]["permutation_digest"]
        # Niezalezne wywolanie z tym samym seedem musi dac ten sam digest -
        # dowod, ze permutacja NIE jest losowana per-genom.
        from clos_scientist.pc_001_k1_shuffle import derive_k1_permutation, k1_permutation_digest
        expected_digest = k1_permutation_digest(derive_k1_permutation(seed, TICKS_TOTAL))
        assert digest == expected_digest

    def test_incomplete_grid_raises_incomplete_grid_error(self):
        """NONCOMPUTABLE (ERRATUM 3): brakujacy genom w bloku -> IncompleteGridError,
        NIE ciche pominiecie - propaguje sie do INCONCLUSIVE (scenariusz A)."""
        records = self._records(9, lambda t: 0.5 - 0.0001 * t)
        with pytest.raises(IncompleteGridError):
            k4_equivalence_cell("A", records, n_genomes_expected=2)  # oczekuje 2, dostaje 1 per seed

    def test_truncated_run_grid_propagates_to_incomplete_grid_error(self):
        """Jeden przebieg z SKROCONA siatka (e_beta_components_for_run zwraca
        None) w bloku 9-seedowym -> caly blok NONCOMPUTABLE -> IncompleteGridError,
        nie pominiecie tego jednego przebiegu."""
        good = self._records(8, lambda t: 0.5 - 0.0001 * t, seed_offset=4001)
        bad_record = {
            "seed": 4009,
            "metrics": {
                "prediction_error_by_tick": {str(t): 0.5 - 0.0001 * t for t in range(150)},
                "prediction_by_tick": {str(t): 0.0 for t in range(150)},
                "input_by_tick": {str(t): 0.5 - 0.0001 * t for t in range(150)},
            },
        }
        with pytest.raises(IncompleteGridError):
            k4_equivalence_cell("A", good + [bad_record], n_genomes_expected=1)

    def test_no_literal_shock_world_in_new_cells(self):
        """Wzorem K4-separacja (ERRATUM 1) - K1/K4/K5 rownowaznosc rowniez
        nie maja powodu odwolywac sie do shock_world."""
        source = MODULE_PATH.read_text(encoding="utf-8")
        no_docstring = re.sub(r'"""[\s\S]*?"""', "", source)
        assert "shock_world" not in no_docstring


class TestBetaRawForRun:
    """B4C-2 (18)/(19)/(20): _beta_raw_for_run ROZNI SIE CELOWO od
    e_beta_components_for_run - Warunek A jest liczony TAKZE dla FLOOR_LIMITED
    (nachylenie nie ma mianownika), w odroznieniu od E_beta (ktora dzieli
    przez W_early_red i musi ja wykluczyc)."""

    def test_floor_limited_run_still_gives_beta_unlike_e_beta(self):
        """PE ponizej podlogi na CALYM oknie -> e_beta_components_for_run
        zwraca None (W_early_red<=0), ale _beta_raw_for_run NIE - to jest
        dokladnie roznica, ktora Warunek A wymaga (SPECYFIKACJA_KANONICZNA_
        PC_001.md §2.6: 'Warunek A liczony takze dla FLOOR_LIMITED')."""
        floor_env = FROZEN_FLOOR_NOISE_WORLD["value"]
        pe_trajectory = _full_grid_pe_trajectory(lambda t: floor_env / 2)
        assert e_beta_components_for_run(pe_trajectory, PRIMARY) is None
        beta = _beta_raw_for_run(pe_trajectory, PRIMARY)
        assert beta is not None
        assert abs(beta) < 1e-9  # PE_red constant (=0) -> slope=0

    def test_truncated_grid_returns_none(self):
        pe_trajectory = {t: 0.5 - 0.001 * t for t in range(150)}
        assert _beta_raw_for_run(pe_trajectory, PRIMARY) is None

    def test_grid_with_gap_returns_none(self):
        pe_trajectory = {t: 0.5 for t in range(TICKS_TOTAL) if t != 150}
        pe_trajectory[300] = 0.5
        assert _beta_raw_for_run(pe_trajectory, PRIMARY) is None

    def test_valid_run_matches_e_beta_components_beta(self):
        """Sanity: dla przebiegu VALID (W_early_red>0) obie funkcje musza
        dac TA SAMA wartosc beta - roznia sie WYLACZNIE traktowaniem
        FLOOR_LIMITED, nie formula."""
        pe_trajectory = _full_grid_pe_trajectory(lambda t: 0.5 - 0.001 * t)
        components = e_beta_components_for_run(pe_trajectory, PRIMARY)
        assert components is not None
        assert _beta_raw_for_run(pe_trajectory, PRIMARY) == components[0]


class TestLinearSlopeIdentityAcrossAllCallers:
    """(19)/(20), pkt 'test tozsamosci': wszystkie komorki wolajace
    linear_slope uzywaja TEGO SAMEGO obiektu funkcji (ta sama pulapka co
    K4-separacja/redukcja_w2_for_run, B4C-2 (04))."""

    def test_same_imported_object_in_module_globals(self):
        from clos_curriculum.laboratory.statistics import linear_slope as stats_linear_slope
        assert evaluator_module.linear_slope is stats_linear_slope
        for fn in (e_beta_components_for_run, _beta_raw_for_run):
            assert fn.__globals__["linear_slope"] is stats_linear_slope

    def test_ast_shows_exactly_two_call_sites(self):
        """Dokladnie dwa miejsca wywolania linear_slope() w calym module -
        e_beta_components_for_run (Grupa A rownowaznosci) i _beta_raw_for_run
        (Warunek A) - obie licza NA PE_red, obie przez ten sam import."""
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        call_sites = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "linear_slope"
        ]
        assert len(call_sites) == 2


class TestWarunekACellEndToEnd:

    def _records(self, n_seeds, pe_fn, seed_offset=6001):
        return [_full_grid_record(seed_offset + s, pe_fn) for s in range(n_seeds)]

    def test_returns_expected_shape(self):
        records = self._records(9, lambda t: 0.5 - 0.0001 * t)
        result = warunek_a_cell(records, n_genomes_expected=1)
        assert result["cell_id"] == "A"
        assert len(result["beta_block_means"]) == 9
        assert result["n"] == 9
        assert result["test_result"]["computable"] is True

    def test_includes_floor_limited_run_that_e_beta_would_exclude(self):
        """Dowod end-to-end (nie tylko jednostkowy) - blok z przebiegami
        FLOOR_LIMITED na calej dlugosci NIE rzuca IncompleteGridError w
        warunek_a_cell, mimo ze ten sam blok wykluczylby sie z komorek
        rownowaznosci (E_beta wymaga W_early_red>0)."""
        floor_env = FROZEN_FLOOR_NOISE_WORLD["value"]
        records = self._records(9, lambda t: floor_env / 2)
        result = warunek_a_cell(records, n_genomes_expected=1)
        assert len(result["beta_block_means"]) == 9
        assert all(abs(b) < 1e-9 for b in result["beta_block_means"])

    def test_negative_incomplete_grid_raises(self):
        records = self._records(9, lambda t: 0.5 - 0.0001 * t)
        with pytest.raises(IncompleteGridError):
            warunek_a_cell(records, n_genomes_expected=2)

    def test_vs_zero_not_vs_arbitrary_constant(self):
        """Wilcoxon jest wprost przeciw 0 - konstrukcja pary (b, 0.0), nie
        (b, jakas_inna_stala)."""
        source = inspect.getsource(warunek_a_cell)
        assert "0.0" in source


class TestWEarlyLateRedForRun:

    def test_matches_independent_w2_endpoint_call(self):
        """Zero reimplementacji formuly - porownanie z bezposrednim
        wywolaniem compute_pe_reducible+compute_w2_reduction."""
        from clos_scientist.w2_endpoint import compute_pe_reducible, compute_w2_reduction
        pe_trajectory = _synthetic_pe_trajectory(early_value=0.5, late_value=0.2)
        pair = _w_early_late_red_for_run(pe_trajectory, PRIMARY)
        assert pair is not None
        floor_result = _floor_result_for_environment(PRIMARY)
        expected = compute_w2_reduction(compute_pe_reducible(pe_trajectory, floor_result))
        assert pair == (expected["w_early_red"], expected["w_late_red"])

    def test_none_when_late_window_entirely_missing(self):
        pe_trajectory = {t: 0.5 for t in W_EARLY_TICKS}  # brak jakichkolwiek tickow W_LATE_TICKS
        assert _w_early_late_red_for_run(pe_trajectory, PRIMARY) is None

    def test_valid_even_when_floor_limited(self):
        """W odroznieniu od redukcja_w2_for_run (None dla FLOOR_LIMITED) -
        para (W_early_red, W_late_red) jest dostepna NIEZALEZNIE od
        klasyfikacji VALID/FLOOR_LIMITED (test parowy pyta o obie wielkosci
        wprost, nie o iloraz)."""
        floor_env = FROZEN_FLOOR_NOISE_WORLD["value"]
        pe_trajectory = _synthetic_pe_trajectory(early_value=floor_env * 0.5, late_value=floor_env * 0.3)
        assert redukcja_w2_for_run(pe_trajectory, PRIMARY) is None  # FLOOR_LIMITED
        pair = _w_early_late_red_for_run(pe_trajectory, PRIMARY)
        assert pair is not None
        assert pair == (0.0, 0.0)  # PE ponizej podlogi -> PE_red=0 po obu stronach


class TestWarunekBCellEndToEnd:

    def _records_with_reduction(self, n_seeds, reduction_fraction, w_early=0.5, seed_offset=7001):
        floor = FROZEN_FLOOR_NOISE_WORLD["value"]
        records = []
        for s in range(n_seeds):
            early_red = w_early + 0.001 * s
            late_red = early_red * (1 - reduction_fraction)
            early_value = floor + early_red
            late_value = floor + late_red
            records.append(_synthetic_record(seed_offset + s, early_value, late_value))
        return records

    def test_returns_expected_shape(self):
        records = self._records_with_reduction(9, reduction_fraction=0.30)
        result = warunek_b_cell(records, n_genomes_expected=1)
        assert result["cell_id"] == "B"
        for key in ("w_early_red_block_means", "w_late_red_block_means", "n", "test_result",
                    "redukcja_W2_block_means", "median_redukcja_W2", "condition_b_threshold",
                    "median_meets_threshold"):
            assert key in result
        assert result["n"] == 9

    def test_threshold_comes_from_config_not_literal(self):
        records = self._records_with_reduction(9, reduction_fraction=0.30)
        result = warunek_b_cell(records, n_genomes_expected=1)
        assert result["condition_b_threshold"] == CONDITION_B_REDUCTION_THRESHOLD

    def test_no_hardcoded_020_literal_in_warunek_b_source(self):
        """Docstringi WOLNO wyjasniac progiem w prozie (np. 'redukcja_W2>=0.20') -
        zakaz dotyczy KODU (uzycia w obliczeniach), ten sam wzorzec strip-
        docstring co TestMarginForCell.test_no_hardcoded_margin_literal_in_module_source."""
        source = inspect.getsource(warunek_b_cell) + inspect.getsource(_paired_w_early_late_by_seed)
        no_docstrings = re.sub(r'"""[\s\S]*?"""', "", source)
        assert "0.20" not in no_docstrings
        assert re.search(r"(?<![\w.])0\.2(?![\w0-9])", no_docstrings) is None

    def test_threshold_gate_independent_of_p_value(self):
        """B4C-2 (20), decyzja CTO: prog 20% jest OSOBNA bramka, NIE wchodzi
        do p ani do BH. Konstrukcja: redukcja ~5% (POD progiem) w kazdym z 9
        blokow, ale KONSEKWENTNIE dodatnia (early>late wszedzie) - test
        parowy MUSI wykryc silnie istotna roznice (p bardzo male), mimo ze
        kryterium progowe NIE jest spelnione. Gdyby prog byl wmieszany w p,
        maly p przy medianie ponizej progu bylby niespojny z samym artefaktem
        (ANEKS 1, Zmiana 4: prog i test to DWA rozne pytania)."""
        records = self._records_with_reduction(9, reduction_fraction=0.05, w_early=0.5)
        result = warunek_b_cell(records, n_genomes_expected=1)
        assert result["median_redukcja_W2"] == pytest.approx(0.05, abs=0.01)
        assert result["median_meets_threshold"] is False
        assert result["test_result"]["computable"] is True
        assert result["test_result"]["p_value"] < 0.05

    def test_median_reduction_uses_same_function_as_k4_separacja(self):
        """redukcja_W2_block_means MUSI pochodzic z _reduction_by_seed/
        redukcja_w2_for_run - TA SAMA funkcja co K4-separacja/K1-B/K4-B/K5-B,
        zero reimplementacji formuly."""
        source = inspect.getsource(warunek_b_cell)
        assert "_reduction_by_seed" in source

    def test_negative_incomplete_grid_raises(self):
        records = self._records_with_reduction(8, reduction_fraction=0.30)
        with pytest.raises(IncompleteGridError):
            warunek_b_cell(records, n_genomes_expected=2)


class TestK3aPrePostMeansForRun:

    def _record_with_shock(self, seed, shock_tick, pre_value, post_value, background=0.3):
        pe = {t: background for t in range(TICKS_TOTAL)}
        pre_window, post_window = k3a_pre_post_shock_windows(shock_tick)
        for t in pre_window:
            pe[t] = pre_value
        for t in post_window:
            pe[t] = post_value
        return {
            "seed": seed,
            "shock_tick": shock_tick,
            "metrics": {"prediction_error_by_tick": {str(t): v for t, v in pe.items()}},
        }

    def test_uses_raw_pe_not_pe_red(self):
        """Oba poziomy PONIZEJ podlogi (floor_env) - gdyby liczono na
        PE_red, obie srednie bylyby 0 i roznica by zniknela. Na surowym PE
        roznica jest ZACHOWANA."""
        floor_env = FROZEN_FLOOR_NOISE_WORLD["value"]
        record = self._record_with_shock(seed=1, shock_tick=100,
                                          pre_value=floor_env * 0.3, post_value=floor_env * 0.7)
        means = _k3a_pre_post_means_for_run(record)
        assert means is not None
        pre_mean, post_mean = means
        assert pre_mean == pytest.approx(floor_env * 0.3)
        assert post_mean == pytest.approx(floor_env * 0.7)
        assert post_mean > pre_mean  # zachowane, NIE obciete do (0, 0)

    def test_missing_shock_tick_returns_none(self):
        record = {"seed": 1, "metrics": {"prediction_error_by_tick": {str(t): 0.3 for t in range(TICKS_TOTAL)}}}
        assert _k3a_pre_post_means_for_run(record) is None

    def test_missing_tick_in_window_returns_none(self):
        """shock_tick blisko 0 -> okno pre wychodzi poza siatke (ticki
        ujemne) -> brakujace klucze -> None, nie czesciowa srednia.
        _record_with_shock() buduje slownik po range(0, TICKS_TOTAL) i
        NADPISUJE klucze pre/post window - dla shock_tick=5 to wpisaloby
        klucze ujemne wprost do dict (Python na to pozwala), wiec test
        buduje rekord RECZNIE, pomijajac ticki <0, zeby faktycznie
        zasymulowac 'nigdy nie zapisane'."""
        shock_tick = 5
        pre_window, post_window = k3a_pre_post_shock_windows(shock_tick)
        pe = {t: 0.3 for t in range(TICKS_TOTAL)}
        for t in pre_window:
            if t >= 0:
                pe[t] = 0.2
        for t in post_window:
            if t >= 0:
                pe[t] = 0.4
        record = {
            "seed": 1, "shock_tick": shock_tick,
            "metrics": {"prediction_error_by_tick": {str(t): v for t, v in pe.items()}},
        }
        assert any(t < 0 for t in pre_window)  # sanity: scenariusz faktycznie testuje brak, nie no-op
        assert _k3a_pre_post_means_for_run(record) is None


class TestK3aWarunek1CellEndToEnd:

    def _records(self, n_seeds, shock_tick, pre_value, post_value, seed_offset=8001):
        records = []
        for s in range(n_seeds):
            pe = {t: 0.3 for t in range(TICKS_TOTAL)}
            pre_window, post_window = k3a_pre_post_shock_windows(shock_tick)
            for t in pre_window:
                pe[t] = pre_value
            for t in post_window:
                pe[t] = post_value + 0.001 * s  # drobna wariacja - unika calkowitej remisowosci
            records.append({
                "seed": seed_offset + s,
                "shock_tick": shock_tick,
                "metrics": {"prediction_error_by_tick": {str(t): v for t, v in pe.items()}},
            })
        return records

    def test_returns_expected_shape_and_alternative_greater(self):
        records = self._records(9, shock_tick=100, pre_value=0.2, post_value=0.5)
        result = k3a_warunek1_cell(records, n_genomes_expected=1)
        assert result["cell_id"] == "K3a-warunek1"
        assert result["n"] == 9
        assert result["test_result"]["alternative"] == "greater"
        assert result["test_result"]["computable"] is True
        assert all(d > 0 for d in result["post_minus_pre_block_means"])

    def test_uses_raw_pe_below_floor(self):
        """K3a NIGDY nie wyznacza podlogi dla shock_world (ERRATUM 1) -
        wartosci PONIZEJ typowej podlogi noise_world sa uzyte wprost, bez
        obciecia."""
        floor_env = FROZEN_FLOOR_NOISE_WORLD["value"]
        records = self._records(9, shock_tick=150, pre_value=floor_env * 0.2, post_value=floor_env * 0.6)
        result = k3a_warunek1_cell(records, n_genomes_expected=1)
        assert all(d > 0 for d in result["post_minus_pre_block_means"])

    def test_negative_missing_shock_tick_raises_incomplete_grid_error(self):
        good = self._records(8, shock_tick=100, pre_value=0.2, post_value=0.5, seed_offset=9001)
        bad = {
            "seed": 9009,
            "metrics": {"prediction_error_by_tick": {str(t): 0.3 for t in range(TICKS_TOTAL)}},
        }  # brak shock_tick
        with pytest.raises(IncompleteGridError):
            k3a_warunek1_cell(good + [bad], n_genomes_expected=1)

    def test_no_floor_lookup_in_k3a_code_path(self):
        """ZAKAZ WPROST (18)/(19)/(20): NIE wyznaczaj podlogi dla shock_world,
        NIE licz K3a na PE_red - dowod strukturalny, nie tylko wynikowy."""
        source = (inspect.getsource(k3a_warunek1_cell)
                  + inspect.getsource(_k3a_diff_by_seed)
                  + inspect.getsource(_k3a_pre_post_means_for_run))
        assert "_floor_result_for_environment" not in source
        assert "compute_pe_reducible" not in source


class TestSpearmanRhoForRun:

    def test_perfect_positive_correlation_gives_rho_one(self):
        record = _full_grid_record(1, lambda t: 0.0, prediction_by_tick=lambda t: t, input_by_tick=lambda t: t)
        rho = _spearman_rho_for_run(record)
        assert rho == pytest.approx(1.0)

    def test_missing_tick_returns_none(self):
        record = {
            "seed": 1,
            "metrics": {
                "prediction_by_tick": {str(t): float(t) for t in range(150)},
                "input_by_tick": {str(t): float(t) for t in range(150)},
            },
        }
        assert _spearman_rho_for_run(record) is None


class TestK6CellEndToEnd:

    def _records(self, n_seeds, seed_offset=10001):
        return [
            _full_grid_record(seed_offset + s, lambda t: 0.0,
                               prediction_by_tick=lambda t: t, input_by_tick=lambda t: t)
            for s in range(n_seeds)
        ]

    def test_returns_expected_shape(self):
        records = self._records(9)
        result = k6_cell(records, n_genomes_expected=1)
        assert result["cell_id"] == "K6"
        assert result["n"] == 9
        assert all(r == pytest.approx(1.0) for r in result["rho_block_means"])

    def test_test_result_is_wilcoxon_shape_not_spearman_shape(self):
        """DO RODZINY BH WCHODZI wilcoxon na rho, NIGDY p-value ze
        spearman_rho (B4C-2 (20), zakaz wprost) - dowod strukturalny:
        test_result ma klucze wilcoxon_signed_rank ('alternative', 'w_plus'),
        ktorych spearman_rho NIGDY nie zwraca."""
        records = self._records(9)
        result = k6_cell(records, n_genomes_expected=1)
        assert "alternative" in result["test_result"]
        assert "w_plus" in result["test_result"] or result["test_result"]["computable"] is False

    def test_negative_incomplete_grid_raises(self):
        records = self._records(9)
        with pytest.raises(IncompleteGridError):
            k6_cell(records, n_genomes_expected=2)
