"""N_OPERATIONAL_SEEDS zgadza sie z ZRODLEM WYKONAWCZYM (B4C-2 (12), decyzja CTO).

PRZEPIECIE (B4C-2 (12)): do tego zlecenia ten straznik wiazal CONFIG z
publications/power_analysis_PC_001.json - poprawnym zrodlem W CHWILI, gdy
rodzina BH miala m=4 (A/B/K4/K6). Rodzina zostala od tego czasu zamrozona
na m=11 (B4C-05) - power_analysis_PC_001.json PRZESTAL byc zrodlem
wykonawczym, ale straznik nadal go czytal i wciaz byl ZIELONY (CONFIG=8,
power_analysis_PC_001.json=8, zgodne ze soba - ale oba juz nieaktualne
wobec rodziny m=11, ktora wymaga n=9). Straznik nie przeoczyl rozjazdu -
POSWIADCZYL go, bo porownywal dwie rzeczy, z ktorych jedna byla juz historia.
To jest NOWA odmiana wzorca "lustro bez straznika zrodla" (patrz
tests/test_erratum_quotes_against_source.py) - tu straznik ISTNIAL, ale
wskazywal na niewlasciwe zrodlo.

ZRODLEM WYKONAWCZYM jest odtad WYLACZNIE publications/pc_001_bh_family.json
(pole N_operational) - CZLONEK CRITICAL_FILES_PC_001, chroniony hashem, i
JEDYNY plik, ktorego tresc faktycznie okresla, ile seedow potrzebuje
dzisiejsza (m=11) rodzina BH. publications/power_analysis_PC_001.json
POZOSTAJE nietkniety (wartosc 8 tam to PRAWDZIWA historia dla m=4, NIE
wartosc wykonawcza) - patrz publications/preregistration_PC_001_ERRATUM_2_
2026-08-28.md/.json.
"""

import json
from pathlib import Path

from clos_scientist.pc_001_experiment_config import (
    N_OPERATIONAL_SEEDS,
    CONFIRMATORY_SEEDS,
    CONFIRMATORY_SEEDS_START,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FAMILY_PATH = REPO_ROOT / "publications" / "pc_001_bh_family.json"
POWER_ANALYSIS_PATH = REPO_ROOT / "publications" / "power_analysis_PC_001.json"


def load_n_operational_from_family(family_path: Path = FAMILY_PATH) -> int:
    with open(family_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["N_operational"]


def verify_n_operational_provenance(family_value: int, expected_config_value: int):
    """Zwraca liste problemow (pusta = OK). NIGDY nie zaklada zgodnosci -
    porownuje wprost."""
    problems = []
    if family_value != expected_config_value:
        problems.append(
            f"pc_001_bh_family.json::N_operational={family_value} != "
            f"CONFIG N_OPERATIONAL_SEEDS={expected_config_value}"
        )
    return problems


REAL_FAMILY_VALUE = load_n_operational_from_family()


class TestConstantValue:
    def test_constant_is_nine(self):
        assert N_OPERATIONAL_SEEDS == 9


class TestA_ArtifactMatchesConfig:
    """(a) B4C-2 (12), weryfikacja pkt a: artefakt (pc_001_bh_family.json)
    zgadza sie z CONFIG na PRAWDZIWYCH, dzisiejszych wartosciach."""

    def test_real_family_matches_config(self):
        problems = verify_n_operational_provenance(REAL_FAMILY_VALUE, N_OPERATIONAL_SEEDS)
        assert problems == []

    def test_real_family_value_is_nine(self):
        assert REAL_FAMILY_VALUE == 9


class TestB_NegativeReproducesExactPastBug:
    """(b) OBOWIAZKOWY, wymagany przez CTO wprost: odtworz DOKLADNIE
    dzisiejszy (sprzed poprawki) blad - CONFIG=8, artefakt=9 -> FAIL/HALT.
    Nie wystarczy 'szczesliwe 9 == 9' (ktore przeszloby nawet gdyby funkcja
    weryfikujaca byla zepsuta i zawsze zwracala pusta liste) - ten test
    podstawia DOKLADNIE historyczna pare wartosci, ktora byla zielona przez
    pomylke, i dowodzi, ze PO przepieciu ta sama para jest czerwona."""

    def test_reproduces_exact_historical_mismatch(self):
        """CONFIG mowilo 8 (stara wartosc, B4B-03/m=4), artefakt mowi 9
        (dzisiejsza wartosc, m=11) - DOKLADNIE stan sprzed B4C-2 (12)."""
        historical_config_value = 8
        problems = verify_n_operational_provenance(REAL_FAMILY_VALUE, historical_config_value)
        assert problems != [], (
            "test negatywny nie wykryl historycznego niedopasowania 8 vs 9 - "
            "funkcja weryfikujaca jest zepsuta albo zawsze zwraca pusta liste"
        )
        assert "8" in problems[0] and "9" in problems[0]

    def test_wrong_artifact_value_is_caught(self):
        problems = verify_n_operational_provenance(family_value=99, expected_config_value=N_OPERATIONAL_SEEDS)
        assert problems != []
        assert "!=" in problems[0]


class TestC_HistoricalValueSupersededNotErased:
    """(c) HISTORYCZNY: ERRATUM 2 superseduje 8 (normatywnie), ale stara
    wartosc w publications/power_analysis_PC_001.json NADAL WYNOSI 8 i MA
    tam zostac. Ten test pilnuje, zeby historii nie 'naprawiono' przez
    usuniecie - power_analysis_PC_001.json jest NIETKNIETY (zakaz wprost,
    B4C-2 (12))."""

    def test_power_analysis_json_still_says_8(self):
        with open(POWER_ANALYSIS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert data["required_seeds"]["n_operational"]["value"] == 8, (
            "power_analysis_PC_001.json::required_seeds.n_operational.value zmienil sie - "
            "ten plik ma pozostac NIETKNIETY (historia B4b dla m=4), poprawka idzie "
            "przez ERRATUM 2, nie przez edycje w miejscu"
        )

    def test_power_analysis_json_not_in_registry(self):
        """Znalezisko CTO (B4C-2 (12)): power_analysis_PC_001.json POZA
        rejestrem CRITICAL_FILES_PC_001 - slusznie, nie zmienia zadnej
        liczby produkowanej przez eksperyment (to erratum, zarejestrowane,
        robi to zamiast niego)."""
        from execution_package_v0_11.validators.hard_halt import CRITICAL_FILES_PC_001
        assert "publications/power_analysis_PC_001.json" not in CRITICAL_FILES_PC_001

    def test_erratum_2_declares_the_supersession(self):
        erratum_path = REPO_ROOT / "publications" / "preregistration_PC_001_ERRATUM_2_2026-08-29.json"
        with open(erratum_path, encoding="utf-8") as f:
            erratum = json.load(f)
        assert erratum["correction"]["value_replaced"] == 8
        assert erratum["correction"]["value_replacing"] == 9
        assert erratum["amends"] == "publications/power_analysis_PC_001.json"

    def test_family_value_and_power_analysis_value_now_legitimately_differ(self):
        """Sanity: PO poprawce, dwa pliki NAROZNIE mowia rozne liczby (9 i 8)
        - to jest POPRAWNY stan (jeden wykonawczy, jeden historyczny), nie
        blad do scalenia."""
        with open(POWER_ANALYSIS_PATH, encoding="utf-8") as f:
            power_analysis_value = json.load(f)["required_seeds"]["n_operational"]["value"]
        assert REAL_FAMILY_VALUE != power_analysis_value
        assert REAL_FAMILY_VALUE == 9
        assert power_analysis_value == 8


class TestD_ConfirmatorySeedsRangeConsistency:
    """(d) Spojnosc zakresu: len(CONFIRMATORY_SEEDS) == N_OPERATIONAL_SEEDS
    == 9, min == 1001, max == 1009.

    UWAGA (decyzja CTO, B4C-2 (12), zapisana tu wprost): DZIS ten test jest
    TAUTOLOGIA ZAMIERZONA. CONFIRMATORY_SEEDS jest WYPROWADZONY z
    N_OPERATIONAL_SEEDS w CONFIG ('range(CONFIRMATORY_SEEDS_START,
    CONFIRMATORY_SEEDS_START + N_OPERATIONAL_SEEDS)') - len(CONFIRMATORY_SEEDS)
    == N_OPERATIONAL_SEEDS przechodzi z DEFINICJI, niezaleznie od tego, jaka
    wartosc ma N_OPERATIONAL_SEEDS. Ten test NIE DOWODZI dzis niczego o
    stanie biezacym (dokladnie ten sam rodzaj tautologii, co
    test_repeated_calls_are_deterministic dla linear_slope, B4C-2 (04)) -
    PILNUJE PRZYSZLOSCI, w ktorej ktos zamieni derywacje (range(...)) na
    wpisana na sztywno liste seedow, co zerwaloby ta rownosc po cichu.
    Dopuszczalny WYLACZNIE dlatego, ze jest tak opisany - test, ktory
    wyglada na kontrole, a jest tautologia, jest dokladnie tym, co ten
    projekt tropi."""

    def test_length_matches_n_operational_seeds(self):
        assert len(CONFIRMATORY_SEEDS) == N_OPERATIONAL_SEEDS

    def test_length_matches_family_value_directly(self):
        """Nie tylko wobec CONFIG (mogloby byc zle skopiowane RAZEM) -
        wobec ZRODLA (pc_001_bh_family.json) bezposrednio."""
        assert len(CONFIRMATORY_SEEDS) == REAL_FAMILY_VALUE

    def test_min_is_confirmatory_seeds_start(self):
        assert min(CONFIRMATORY_SEEDS) == CONFIRMATORY_SEEDS_START == 1001

    def test_max_is_start_plus_n_minus_one(self):
        assert max(CONFIRMATORY_SEEDS) == CONFIRMATORY_SEEDS_START + N_OPERATIONAL_SEEDS - 1 == 1009
