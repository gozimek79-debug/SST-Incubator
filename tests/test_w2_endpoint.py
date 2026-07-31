"""PC-001 W2 + V-C (D-018) - testy weryfikacyjne wg specyfikacja_W2_2026-07-28.md §4.

Syntetyczne env_fn i male okna/N (monkeypatch) dla szybkosci wykonania - REALNE
floor(t) dla noise_world z produkcyjnym N=100_000 na pelnym 300-tickowym oknie
jest liczone OSOBNO (execution_package_v0_11/runners/compute_noise_world_floor.py,
~9 min), nie w tym pliku, zeby kazde uruchomienie pytest nie trwalo kilkunastu minut.
Mechanizm liczacy jest identyczny (ten sam floor_at_tick/select_floor_model) -
zmieniaja sie tylko N i rozmiar okien, oba parametryzowane przez
clos_world.floor_model.DEFAULT_N i clos_scientist.w2_endpoint.*_TICKS.
"""

import inspect
import random

import pytest

from clos_scientist import w2_endpoint
from clos_world import floor_model


@pytest.fixture(autouse=True)
def _fast_mc(monkeypatch):
    """Male N (2000) i male okna (12 tickow: W_early=[0,6), W_late=[6,12)) dla
    calego pliku - ta sama formula/mechanizm co produkcja, tylko szybciej.
    Determinystyczne (seed_start jest stala), wiec zero flakiness miedzy
    uruchomieniami."""
    monkeypatch.setattr(floor_model, "DEFAULT_N", 2000)
    monkeypatch.setattr(w2_endpoint, "MEASURABLE_WINDOW_TICKS", list(range(0, 12)))
    monkeypatch.setattr(w2_endpoint, "W_EARLY_TICKS", list(range(0, 6)))
    monkeypatch.setattr(w2_endpoint, "W_LATE_TICKS", list(range(6, 12)))


def _stationary_noise(tick, seed):
    """Srodowisko stacjonarne: N(0.5, 0.01) obciete do [0,1] - srodek sygnalu NIE
    zalezy od ticka, wiec floor(t) jest (do szumu MC) staly -> bias_roznicowy
    oczekiwany ponizej tolerancji."""
    rng = random.Random(seed * 1000 + tick)
    raw = rng.gauss(0.5, 0.1)
    return max(0.0, min(1.0, raw))


def _drifting_truncation_noise(tick, seed):
    """Srodowisko NIEstacjonarne: srodek sygnalu 0.5 (brak obciecia) w oknie
    early, 0.02 (silne obciecie do [0,1]) w oknie late - konstruuje DUZY
    bias_roznicowy celowo, do testu W2-T7(b)."""
    center = 0.5 if tick < 6 else 0.02
    rng = random.Random(seed * 1000 + tick)
    raw = rng.gauss(center, 0.1)
    return max(0.0, min(1.0, raw))


class TestFloorAtTickIndependentReimplementation:
    """Test 1 (specyfikacja_W2 §4): floor policzona niezaleznie z definicji
    scenariusza, zgodnosc do 1e-6."""

    def test_independent_reimplementation_matches_to_1e6(self):
        def _reference_floor(env_fn, tick, N, seed_start):
            vals = [env_fn(tick, s) for s in range(seed_start, seed_start + N)]
            m = sum(vals) / N
            return sum(abs(v - m) for v in vals) / N

        produced = floor_model.floor_at_tick(_stationary_noise, tick=3, N=5000, seed_start=1)
        reference = _reference_floor(_stationary_noise, tick=3, N=5000, seed_start=1)
        assert abs(produced - reference) < 1e-6


class TestNegativeFloorOverstated:
    """Test 2: podloga celowo zawyzona -> wszystkie przebiegi FLOOR_LIMITED."""

    def test_overstated_floor_forces_all_floor_limited(self):
        floor_result = {"floor_model": "constant", "floor_env": 10.0}
        pe_trajectory = {t: 0.3 for t in range(12)}
        pe_red = w2_endpoint.compute_pe_reducible(pe_trajectory, floor_result)
        assert all(v == 0.0 for v in pe_red.values())
        result = w2_endpoint.compute_w2_reduction(pe_red)
        assert result["classification"] == "FLOOR_LIMITED"
        assert result["reduction"] is None


class TestNegativeFloorZeroed:
    """Test 3 (KLUCZOWY): podloga celowo wyzerowana -> W2 redukuje sie do W1
    (surowe PE). Lapie implementacje, ktora POBIERA floor_env ale jej NIE
    ODEJMUJE (wzorzec aliasu 'comparison' z P0)."""

    def test_zero_floor_makes_w2_identical_to_raw_pe(self):
        floor_result = {"floor_model": "constant", "floor_env": 0.0}
        pe_trajectory = {}
        pe_trajectory.update({t: 0.5 for t in range(6)})
        pe_trajectory.update({t: 0.3 for t in range(6, 12)})

        pe_red = w2_endpoint.compute_pe_reducible(pe_trajectory, floor_result)
        assert pe_red == pe_trajectory, "PE_red powinno byc IDENTYCZNE z PE, gdy floor=0"

        w2_result = w2_endpoint.compute_w2_reduction(pe_red)
        w1_reduction = (0.5 - 0.3) / 0.5
        assert abs(w2_result["reduction"] - w1_reduction) < 1e-9

    def test_nonzero_floor_actually_reduces_values_not_just_fetched(self):
        """Uzupelnienie testu 3 - domyka luke, ktorej sam test z floor=0 NIE
        wykrywa (kod, ktory w ogole nie odejmuje floor, tez przeszedlby test
        powyzej, bo max(0,PE-0)==PE niezaleznie od tego, czy odejmowanie
        faktycznie sie odbywa). Z floor>0 PE_red MUSI byc SCISLE mniejsze."""
        floor_result = {"floor_model": "constant", "floor_env": 0.2}
        pe_trajectory = {t: 0.5 for t in range(12)}
        pe_red = w2_endpoint.compute_pe_reducible(pe_trajectory, floor_result)
        assert all(pe_red[t] < pe_trajectory[t] for t in pe_trajectory)
        assert all(abs(pe_red[t] - 0.3) < 1e-9 for t in pe_red)


class TestSimulatedIdealPredictor:
    """Test 4: predyktor idealny (PE(t) == floor(t) dokladnie) -> PE_red~0 ->
    FLOOR_LIMITED."""

    def test_ideal_predictor_gives_floor_limited(self):
        floor_result = {"floor_model": "constant", "floor_env": 0.178}
        pe_trajectory = {t: 0.178 for t in range(12)}
        pe_red = w2_endpoint.compute_pe_reducible(pe_trajectory, floor_result)
        assert all(v == 0.0 for v in pe_red.values())
        result = w2_endpoint.compute_w2_reduction(pe_red)
        assert result["w_early_red"] == 0.0
        assert result["classification"] == "FLOOR_LIMITED"
        assert result["reduction"] is None


class TestSimulatedConstantPredictor:
    """Test 5: predyktor staly (0.5, PE stale w czasie) -> brak redukcji."""

    def test_constant_predictor_gives_zero_reduction(self):
        floor_result = {"floor_model": "constant", "floor_env": 0.1}
        pe_trajectory = {t: 0.3 for t in range(12)}
        pe_red = w2_endpoint.compute_pe_reducible(pe_trajectory, floor_result)
        result = w2_endpoint.compute_w2_reduction(pe_red)
        assert result["classification"] == "VALID"
        assert abs(result["reduction"]) < 1e-9


class TestBoundaryZeroDenominator:
    """Test 6: przypadek brzegowy - W_early_red = 0 dokladnie, wszystkie PE(t)
    < floor_env. Brak dzielenia przez zero, brak wyjatku."""

    def test_all_pe_below_floor_no_division_by_zero(self):
        floor_result = {"floor_model": "constant", "floor_env": 0.5}
        pe_trajectory = {t: 0.1 for t in range(12)}
        pe_red = w2_endpoint.compute_pe_reducible(pe_trajectory, floor_result)
        result = w2_endpoint.compute_w2_reduction(pe_red)
        assert result["w_early_red"] == 0.0
        assert result["classification"] == "FLOOR_LIMITED"
        assert result["reduction"] is None


class TestFloorLimitedCellSafeguard:
    """specyfikacja_W2 §3.3: >30% FLOOR_LIMITED w komorce -> INCONCLUSIVE."""

    def test_cell_over_30_percent_floor_limited_is_inconclusive(self):
        classifications = ["FLOOR_LIMITED"] * 4 + ["VALID"] * 6
        assert w2_endpoint.classify_cell(classifications) == "INCONCLUSIVE"

    def test_cell_under_30_percent_floor_limited_is_ok(self):
        classifications = ["FLOOR_LIMITED"] * 2 + ["VALID"] * 8
        assert w2_endpoint.classify_cell(classifications) == "OK"

    def test_cell_exactly_30_percent_is_ok_not_inconclusive(self):
        """Regula uzywa SCISLEJ nierownosci (>30%) - dokladnie 30% NIE wywoluje
        INCONCLUSIVE."""
        classifications = ["FLOOR_LIMITED"] * 3 + ["VALID"] * 7
        assert w2_endpoint.classify_cell(classifications) == "OK"

    def test_empty_cell_is_insufficient_data(self):
        assert w2_endpoint.classify_cell([]) == "INSUFFICIENT_DATA"


class TestFrozenFloorEnvReproducibilityControl:
    """D-018: floor_env jako wartosc PREREJESTROWANA (nie liczona od nowa przy
    kazdym starcie) + kontrola zgodnosci z niezalezna probka MC. Ta sama zasada
    co PC_001_BASELINE - rozjazd MUSI halowac, nie cicho przejsc na nowa
    wartosc."""

    def test_matching_frozen_value_passes(self):
        """Wartosc 'zamrozona' ustawiona na prawdziwy wynik (policzony osobno,
        inna probka MC) - kontrola MUSI przejsc w rozsadnej tolerancji."""
        true_value = sum(
            floor_model.floor_at_tick(_stationary_noise, t, N=2000, seed_start=1)
            for t in range(12)
        ) / 12
        frozen = {
            "environment": "test_stationary", "value": round(true_value, 6),
            "date_computed": "2026-07-28", "N": 2000, "seed_start": 1,
        }
        recomputed = w2_endpoint.verify_frozen_floor_env(
            _stationary_noise, frozen, tolerance=0.01, verification_seed_start=9999
        )
        assert abs(recomputed - frozen["value"]) < 0.01

    def test_artificially_altered_frozen_value_raises(self):
        """TEST NEGATYWNY (wymagany): sztucznie zmieniona zamrozona wartosc
        (+10, absurdalnie odlegla) - kontrola MUSI wykryc rozjazd i podniesc
        FrozenFloorMismatchError, nie cicho zaakceptowac nowa wartosc."""
        frozen = {
            "environment": "test_stationary", "value": 10.0,  # celowo absurdalne
            "date_computed": "2026-07-28", "N": 2000, "seed_start": 1,
        }
        with pytest.raises(w2_endpoint.FrozenFloorMismatchError, match="HALT"):
            w2_endpoint.verify_frozen_floor_env(
                _stationary_noise, frozen, tolerance=0.01, verification_seed_start=9999
            )

    def test_verification_uses_different_seed_pool_than_frozen_value(self):
        """Regresja: weryfikacja MUSI uzywac INNEGO seed_start niz ten
        zamrozony - identyczny seed_start dawalby bit-identyczny wynik
        (deterministyczny env_fn), co testowaloby wylacznie 'czy kod sie nie
        zmienil' (juz pokryte hashem), nie prawdziwa zgodnosc statystyczna."""
        sig = inspect.signature(w2_endpoint.verify_frozen_floor_env)
        default_verification_seed = sig.parameters["verification_seed_start"].default
        frozen_seed_default = 500_000  # FROZEN_FLOOR_NOISE_WORLD["seed_start"]
        assert default_verification_seed != frozen_seed_default

    def test_frozen_noise_world_config_has_required_metadata(self):
        """FROZEN_FLOOR_NOISE_WORLD niesie wszystkie metadane wymagane przez
        D-018 pkt 3: data, N, seed(y), bias_roznicowy, model."""
        from clos_scientist.pc_001_experiment_config import FROZEN_FLOOR_NOISE_WORLD as frozen
        for key in ("environment", "value", "date_computed", "N", "seed_start",
                    "bias_roznicowy", "floor_model"):
            assert key in frozen, f"brak wymaganego pola '{key}' w FROZEN_FLOOR_NOISE_WORLD"
        assert frozen["floor_model"] == "constant"
        assert frozen["value"] == 0.09589


class TestW2T7ValidationMechanism:
    """W2-T7 (D-018 pkt 6, specyfikacja_W2 §4): test mechanizmu V-C."""

    def test_a_bias_below_tolerance_selects_constant(self):
        result = w2_endpoint.select_floor_model(_stationary_noise)
        assert result["bias_roznicowy"] < w2_endpoint.FLOOR_BIAS_TOLERANCE, (
            f"bias_roznicowy={result['bias_roznicowy']} - srodowisko testowe nie "
            "daje oczekiwanego niskiego obciazenia roznicowego, dostosuj fixture"
        )
        assert result["floor_model"] == "constant"
        assert result["warning"] is None
        assert result["floor_profile"] is None

    def test_b_bias_above_tolerance_automatically_switches_to_per_tick(self):
        result = w2_endpoint.select_floor_model(_drifting_truncation_noise)
        assert result["bias_roznicowy"] >= w2_endpoint.FLOOR_BIAS_TOLERANCE, (
            f"bias_roznicowy={result['bias_roznicowy']} - srodowisko testowe nie "
            "daje oczekiwanego wysokiego obciazenia roznicowego, dostosuj fixture"
        )
        assert result["floor_model"] == "per_tick"
        assert result["warning"] == "bias exceeds tolerance"
        assert result["floor_profile"] is not None
        assert len(result["floor_profile"]) == len(w2_endpoint.MEASURABLE_WINDOW_TICKS)

    def test_c_no_operator_controllable_path_exists(self):
        """DOWOD: select_floor_model przyjmuje WYLACZNIE env_fn - zaden
        parametr (model=, force=, N= czy inny) nie pozwala operatorowi wymusic
        wyniku. Regresja na D-018 pkt 6 / W2-T7(c)."""
        sig = inspect.signature(w2_endpoint.select_floor_model)
        params = list(sig.parameters.keys())
        assert params == ["env_fn"], (
            f"select_floor_model ma dodatkowe parametry {params} poza env_fn - "
            "to otwiera sciezke, ktora operator moglby uzyc do wymuszenia modelu "
            "podlogi, unicestwiajac mechanicznosc V-C (D-018 pkt 6, W2-T7c)"
        )
