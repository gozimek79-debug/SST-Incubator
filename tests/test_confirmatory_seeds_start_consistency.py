"""B4C-04 (Wariant C, decyzja CTO): spojnosc trzech HISTORYCZNYCH literalow
CONFIRMATORY_SEEDS_START (1001) z jedynym zrodlem NORMATYWNYM od teraz -
clos_scientist.pc_001_experiment_config.CONFIRMATORY_SEEDS_START.

DLACZEGO TEST SPOJNOSCI, NIE KONSOLIDACJA: kazdy z trzech runnerow pilota
(pilot_final.py, pilot_power_analysis.py, pilot_power_analysis_w2.py)
wyprodukowal ZAMROZONY artefakt danych, ktory PC-001 nadal uzywa (parametry
uciazliwe dla B4b). Edycja ktoregokolwiek pliku (nawet zmiana zachowaniowo
obojetna - import zamiast literalu) sprawia, ze plik w repo przestaje byc
DOKLADNIE tym plikiem, ktory wyprodukowal zapisane liczby - a prowieniencja
jest tu cala stawka. Zamiast konsolidacji: CONFIG jest jedynym zrodlem
normatywnym dla WSZYSTKIEGO, co powstaje OD TERAZ (m.in. runner
konfirmacyjny); trzy runnery pilota zostaja NIETKNIETE, a ten test daje TA
SAMA gwarancje niemozliwosci cichego rozjazdu, bez dotykania ani jednego
pliku historycznego - ten sam wzorzec co testy prowieniencji dla progu
Warunku B i N_operational (import z kazdego zrodla osobno, nie parsowanie
tekstu, nie monkeypatch).

ZERO edycji pilot_final.py / pilot_power_analysis.py / pilot_power_analysis_w2.py
w tym pliku ani gdziekolwiek indziej w tym zleceniu.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "execution_package_v0_11"))
sys.path.insert(0, str(REPO_ROOT))

from clos_scientist.pc_001_experiment_config import CONFIRMATORY_SEEDS_START  # noqa: E402
from runners.pilot_final import CONFIRMATORY_SEEDS_START as PILOT_FINAL_VALUE  # noqa: E402
from runners.pilot_power_analysis import CONFIRMATORY_SEEDS_START as PILOT_POWER_ANALYSIS_VALUE  # noqa: E402
from runners.pilot_power_analysis_w2 import CONFIRMATORY_SEEDS_START as PILOT_POWER_ANALYSIS_W2_VALUE  # noqa: E402


def verify_confirmatory_seeds_start_consistency(config_value, sources: dict):
    """sources: {nazwa_runnera: wartosc_zaimportowana}. Zwraca liste
    problemow (pusta = OK) - kazde zrodlo niezgodne z CONFIG jest zgloszone
    osobno, zeby test negatywny mogl dowiesc wykrycia POJEDYNCZEGO rozjazdu
    bez gubienia go w zbiorczym komunikacie."""
    problems = []
    for name, value in sources.items():
        if value != config_value:
            problems.append(
                f"{name}: CONFIRMATORY_SEEDS_START={value} != CONFIG={config_value}"
            )
    return problems


REAL_SOURCES = {
    "pilot_final.py": PILOT_FINAL_VALUE,
    "pilot_power_analysis.py": PILOT_POWER_ANALYSIS_VALUE,
    "pilot_power_analysis_w2.py": PILOT_POWER_ANALYSIS_W2_VALUE,
}


class TestConfigIsNormativeSource:
    def test_config_value_is_1001(self):
        assert CONFIRMATORY_SEEDS_START == 1001


class TestThreeHistoricalRunnersUntouched:
    """Dowod negatywny (spis tresci zlecenia): zaden z trzech plikow pilota
    nie zostal dotkniety - literal 1001 nadal ISTNIEJE lokalnie w kazdym
    (gdyby ktos go usunal/zaimportowal, ten test przestalby miec sens -
    import powyzej rzucilby ImportError zamiast dac int)."""

    def test_all_three_still_export_a_plain_int_literal(self):
        for name, value in REAL_SOURCES.items():
            assert isinstance(value, int), f"{name}: oczekiwano int (literal), jest {type(value)}"


class TestEndToEndConsistency:
    def test_all_three_pilot_literals_match_config(self):
        problems = verify_confirmatory_seeds_start_consistency(CONFIRMATORY_SEEDS_START, REAL_SOURCES)
        assert problems == []


class TestNegativeDivergedSource:
    """Test negatywny (B4C-04, weryfikacja #1): podstawiona bledna wartosc
    dla JEDNEGO zrodla MUSI zostac wykryta - dowod, ze funkcja faktycznie
    porownuje, nie tylko deklaruje sukces."""

    def test_single_diverged_source_is_caught(self):
        tampered = dict(REAL_SOURCES)
        tampered["pilot_power_analysis_w2.py"] = 999  # symulacja rozjazdu
        problems = verify_confirmatory_seeds_start_consistency(CONFIRMATORY_SEEDS_START, tampered)
        assert len(problems) == 1
        assert "pilot_power_analysis_w2.py" in problems[0]
        assert "999" in problems[0]

    def test_all_three_diverged_are_each_reported_separately(self):
        tampered = {name: 999 for name in REAL_SOURCES}
        problems = verify_confirmatory_seeds_start_consistency(CONFIRMATORY_SEEDS_START, tampered)
        assert len(problems) == 3

    def test_diverged_config_itself_is_also_caught(self):
        """Rozjazd moze isc w KAZDA strone - podstawiona bledna wartosc CONFIG
        (nie tylko zrodla) tez musi zostac wykryta."""
        problems = verify_confirmatory_seeds_start_consistency(2000, REAL_SOURCES)
        assert len(problems) == 3
