"""B4C-01: Runner Eksperymentu Konfirmacyjnego PC-001 - WYLACZNIE orkiestracja
i zapis surowych danych. Zero analizy statystycznej (redukcja/W_early/W_late/
beta/rho) - to zadanie EVALUATORA, wstrzymanego do decyzji CTO o definicji
komorki (rozmiar rodziny BH). Runner NIE zalezy od tej decyzji: produkuje
surowe dane, rodzina BH dotyczy wylacznie ich agregacji.

pipeline.py (runner v0.11) POZOSTAJE NIETKNIETY - ten plik jest CELOWYM
powieleniem jego mechaniki (checkpoint/resume/schemat BUILD-006), nie
refaktoryzacja. Powielenie jest tansze niz splatanie dwoch protokolow.

============================================================================
UKLAD SKRZYZOWANY - TO SAMO ZALOZENIE CO W B4b (power_analysis_b4b.py)
============================================================================
Jeden wspolny zestaw N_OPERATIONAL_SEEDS UNIKALNYCH seedow, TEN SAM dla
wszystkich 23 genomow i wszystkich trzech srodowisk. To NIE jest wygoda
implementacyjna - B4b policzyl wymagana liczbe seedow WLASNIE dla tej
struktury (seed jako blok/czynnik losowy dzielony przez genomy). Runner
losujacy inne seedy per genom uniewazniby analize mocy.

============================================================================
PARAMETRY - WYLACZNIE Z ADRESOW (zero literali w kodzie ponizej)
============================================================================
  lekcja                 EXPERIMENT_CONFIG["protocol"]["lesson"]
  liczba tickow           EXPERIMENT_CONFIG["protocol"]["ticks_total"]
  PERCEIVE zawsze on      EXPERIMENT_CONFIG["protocol"]["perceive_always_on"]
                          (WERYFIKOWANE jako precondition - run_shock_recovery
                          nie ma parametru "perceive_always_on": PERCEIVE-
                          zawsze-wlaczony jest WLASCIWOSCIA implementacji L1.2
                          (obserwacja odpalana w kazdym ticku petli, patrz
                          lesson_L1_2.py), nie przelacznikiem runtime. Ten
                          runner ASSERTuje, ze CONFIG nadal deklaruje True,
                          zamiast przekazywac nieistniejacy argument.)
  trzy srodowiska         EXPERIMENT_CONFIG["environments"] (primary/K3/K4)
  liczba seedow           N_OPERATIONAL_SEEDS
  seed poczatkowy         CONFIRMATORY_SEEDS_START
  genomy                  execution_package_v0_11/genomes/population.json

GENOMY - WYJASNIENIE ADRESU: zadanie wskazuje "genome/presets.py" jako
zrodlo. Ten plik zawiera WYLACZNIE trzy fabryki presetow (create_default_
genome/create_minimal_genome/create_highly_plastic_genome) - NIE 23 genomy.
Populacja 23 genomow powstaje przez clos_curriculum.laboratory.population.
generate_population() (LHS, seed=20101), ktory czyta granice genow WLASNIE
z genome/presets.py (population.py:26, komentarz "zrodlo granic: genome/
presets.py") - i jest ZAMROZONA w execution_package_v0_11/genomes/
population.json. WSZYSCY istniejacy runnerzy PC-001 (pilot_final.py,
pilot_power_analysis_w2.py) i v0.11 (pipeline.py) czytaja TEN plik, nie
wywoluja generate_population() na zywo. Ten runner robi to samo - jedyny
sposob, by ZAGWARANTOWAC bitowo identyczny zestaw 23 genomow co w pilocie
(ponowne wywolanie generate_population() nie dodaje nic ponad to, co plik
juz zamraza, i wprowadza zbedne ryzyko rozjazdu).

============================================================================
CO RUNNER ZAPISUJE
============================================================================
Dla kazdego przebiegu (srodowisko, genom, seed): PELNA trajektoria
prediction_error po WSZYSTKICH tickach (nie tylko oknie wczesnym jak pilot -
ten runner mierzy CALY protokol, bo produkuje dane WEJSCIOWE dla wszystkich
czterech testow reguly decyzyjnej, nie tylko parametry uciazliwe). Ticki bez
wartosci zapisane jako None (PC-001 §2.1: wykluczane, nie zerowane) - ten
sam mechanizm przechwytywania w pamieci (monkeypatch SnapshotEngine.
create_snapshot) co execution_package_v0_11/runners/pilot_final.py, ale BEZ
filtra "tick < W_EARLY_TICKS".

Runner NIE liczy: W_early_red, W_late_red, redukcji, bety trendu, rho
Spearmana pelnego okna, ani zadnej innej wielkosci reguly decyzyjnej -
zero importu funkcji analizy statystycznej (clos_curriculum.laboratory.
statistics) w tym pliku.

============================================================================
WERYFIKACJA PODLOGI PRZED URUCHOMIENIEM
============================================================================
verify_floors_before_run() iteruje PO WSZYSTKICH atrybutach CONFIG
zaczynajacych sie od "FROZEN_FLOOR_" (introspekcja - zero wpisanej na
sztywno listy srodowisk) i woła w2_endpoint.verify_frozen_floor_env() dla
kazdego. Dzis: noise_world i pure_noise_world maja zamrozona podloge;
shock_world (K3) NIE MA (W2/floor dotyczy Primary Endpoint i K4 - K3 idzie
inna sciezka, patrz specyfikacja_W2) - POMIJANY, nie brakujacy. Niezgodnosc
-> FrozenFloorMismatchError, HALT.

HARD-HALT (Core hash, enforce_hard_halt_v2): CELOWO NIE WPIETY w tym pliku.
execution_package_v0_11/hashes/pc_001_baseline_hash.txt: "STATUS: TBD...
enforce_hard_halt_v2() NIE MA wartosci domyslnej... wiec nic nie moze
przypadkiem polegac na tej niepoliczonej jeszcze wartosci." Ten runner
respektuje to samo ograniczenie - wpiecie Hard-Halt nastapi, gdy B5 policzy
PC_001_BASELINE (poza zakresem tego zlecenia, ktore explicite zakazuje
liczenia baseline'u).

============================================================================
DRY-RUN: ZAKRES SEEDOW ROZLACZNY ZE WSZYSTKIMI UDOKUMENTOWANYMI
============================================================================
Sprawdzone PROGRAMOWO (patrz assert_dry_run_seeds_disjoint) przeciw:
  pilot (rzeczywisty, D-042)                1-15               [zamkniety]
  v0.11 produkcyjny (environments/*.json)   1-185              [zamkniety]
  konfirmacja - BLOK ZAREZERWOWANY (CONFIRMATORY_SEEDS_RESERVED
    w CONFIG, NIE dzisiejszy zuzywany zakres 1001-1008 - patrz
    B4C-03/04: "1001+" odczytane jako otwarte bez znanej gornej
    granicy falszowalo zdanie o rozlacznosci w W2_completion_
    report; sprawdzanie przeciw waskiemu N=8 powtorzyloby ten
    sam blad tutaj)                          1001-1050          [zamkniety]
  wyznaczanie podlog (Monte Carlo)          500000-599999      [zamkniety]
  weryfikacja podlog (verify_frozen_floor_
    env domyslny seed_start)                600000-699999      [zamkniety]
  kontrola audytora (zgloszona w zleceniu B4C-03: 700000-720000 -
    zakres zamkniety podany przez CTO, nie znaleziony w kodzie,
    respektowany mimo braku potwierdzenia w repo)                700000-720000  [zamkniety]

DRY_RUN_SEED_START = 50_000 (3 seedy, 50000-50002) - w bezpiecznej
"szczelinie" miedzy malymi zakresami (<=1008) a duzymi (>=500000);
CALKOWICIE ponizej jedynego zakresu otwartego (700000+), wiec nie wymaga
zgadywania jego gornej granicy.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PACKAGE_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

from clos_academy.lesson_L1_2 import run_shock_recovery
from clos_kernel.snapshot_engine import SnapshotEngine
from clos_world.scenarios import get_scenario
from clos_scientist import pc_001_experiment_config as config
from clos_scientist.pc_001_experiment_config import (
    EXPERIMENT_CONFIG, N_OPERATIONAL_SEEDS, CONFIRMATORY_SEEDS_START,
    CONFIRMATORY_SEEDS, CONFIRMATORY_SEEDS_RESERVED,
)
from clos_scientist.w2_endpoint import verify_frozen_floor_env

GENOMES_PATH = REPO_ROOT / "execution_package_v0_11" / "genomes" / "population.json"

# Harmonogram checkpointow dla 552 przebiegow (23 x 8 x 3) - analogicznie do
# CHECKPOINT_INTERVALS w pipeline.py (skalowany dol dla mniejszego N_total).
CHECKPOINT_INTERVALS = [50, 150, 275, 425, 552]
DRY_RUN_CHECKPOINT_INTERVALS = [5]  # jedyny osiagalny checkpoint w 9 runach (3x1x3)

# Rozlacznosc udokumentowana w docstringu modulu (sekcja DRY-RUN powyzej).
# 50_000: bezpieczna "szczelina" miedzy malymi zakresami produkcyjnymi/
# pilotowymi/konfirmacyjnymi (blok zarezerwowany konczy sie na 1050) a duzymi
# zakresami Monte Carlo/audytu (>=500_000).
DRY_RUN_SEED_START = 50_000
DRY_RUN_N_SEEDS = 3

# ZAMKNIETE zakresy (znana gorna granica) - sprawdzane jako zbior. "confirmatory"
# uzywa BLOKU ZAREZERWOWANEGO (CONFIRMATORY_SEEDS_RESERVED), NIE dzisiejszego
# zuzywanego zakresu (CONFIRMATORY_SEEDS, 8 seedow) - B4C-03/04: odczyt "1001+"
# jako otwartego (bez znanej gornej granicy nigdzie w repo) unaczynial zdanie
# W2_completion_report o rozlacznosci z podlogami (500000-599999) FALSZYWYM;
# sprawdzanie przeciw wasko zdefiniowanemu N=8 powtorzyloby ten sam blad w tym
# pliku. Blok zarezerwowany (margines do 50, uzasadnienie w CONFIG) jest
# WLASCIWA jednostka rozlacznosci.
DOCUMENTED_SEED_RANGES_CLOSED = {
    "pilot_final_d042": range(1, 16),
    "v0_11_production": range(1, 186),
    "confirmatory_reserved_block": CONFIRMATORY_SEEDS_RESERVED,
    "floor_computation_mc": range(500_000, 600_000),
    "floor_verification_default": range(600_000, 700_000),
    "audytor_reserved": range(700_000, 720_001),
}


def assert_dry_run_seeds_disjoint() -> None:
    dry_run_seeds = set(range(DRY_RUN_SEED_START, DRY_RUN_SEED_START + DRY_RUN_N_SEEDS))
    for name, rng in DOCUMENTED_SEED_RANGES_CLOSED.items():
        overlap = dry_run_seeds & set(rng)
        if overlap:
            raise AssertionError(
                f"DRY_RUN_SEED_START zakres nachodzi na udokumentowany zamkniety "
                f"zakres '{name}': {sorted(overlap)}"
            )


def _genomes() -> List[Dict[str, Any]]:
    with open(GENOMES_PATH, encoding="utf-8") as f:
        return json.load(f)["genomes"]


def _genome_lookup() -> Dict[str, Dict[str, Any]]:
    return {g["genome_id"]: g for g in _genomes()}


def _environments() -> List[str]:
    """EXPERIMENT_CONFIG["environments"] jest {"primary":.., "K3":.., "K4":..}
    - wartosci (nazwy srodowisk), nie klucze, sa tym, czego runner uzywa."""
    return list(EXPERIMENT_CONFIG["environments"].values())


def _lesson() -> str:
    return EXPERIMENT_CONFIG["protocol"]["lesson"]


def _ticks_total() -> int:
    return EXPERIMENT_CONFIG["protocol"]["ticks_total"]


def _assert_perceive_always_on() -> None:
    """run_shock_recovery nie ma parametru "perceive_always_on" - PERCEIVE
    zawsze wlaczony jest WLASCIWOSCIA implementacji L1.2 (patrz docstring
    modulu). Ten runner WERYFIKUJE zamiast przekazywac nieistniejacy
    argument - jesli CONFIG kiedykolwiek zadeklarowalby False, runner ma sie
    zatrzymac, nie cicho kontynuowac z zalozeniem, ktore juz nie jest prawda."""
    if EXPERIMENT_CONFIG["protocol"]["perceive_always_on"] is not True:
        raise AssertionError(
            "EXPERIMENT_CONFIG['protocol']['perceive_always_on'] != True - "
            "ten runner zaklada PERCEIVE zawsze wlaczony (wlasciwosc L1.2, "
            "nie parametr run_shock_recovery). Konfig sie rozjechal z "
            "zalozeniem runnera - STOP, nie kontynuuj."
        )


def build_confirmatory_specs(seed_start: int, n_seeds: int) -> List[Tuple[str, str, str, int]]:
    """(lesson, environment, genome_id, seed) - JEDEN wspolny zestaw seedow
    dla WSZYSTKICH genomow i WSZYSTKICH srodowisk (uklad skrzyzowany, patrz
    docstring modulu)."""
    lesson = _lesson()
    genome_ids = [g["genome_id"] for g in _genomes()]
    seeds = list(range(seed_start, seed_start + n_seeds))
    specs: List[Tuple[str, str, str, int]] = []
    for environment in _environments():
        for genome_id in genome_ids:
            for seed in seeds:
                specs.append((lesson, environment, genome_id, seed))
    return specs


def build_confirmatory_run_specs() -> List[Tuple[str, str, str, int]]:
    return build_confirmatory_specs(CONFIRMATORY_SEEDS_START, N_OPERATIONAL_SEEDS)


def build_dry_run_specs() -> List[Tuple[str, str, str, int]]:
    assert_dry_run_seeds_disjoint()
    return build_confirmatory_specs(DRY_RUN_SEED_START, DRY_RUN_N_SEEDS)


def verify_floors_before_run() -> Dict[str, Any]:
    """Weryfikuje KAZDA zamrozona podloge (CONFIG::FROZEN_FLOOR_*, odkryte
    introspekcja - zero wpisanej na sztywno listy srodowisk) przed startem.
    Niezgodnosc -> FrozenFloorMismatchError (podniesiony przez
    verify_frozen_floor_env), HALT - nie ostrzezenie, nie kontynuacja."""
    results: Dict[str, Any] = {}
    for name in dir(config):
        if not name.startswith("FROZEN_FLOOR_"):
            continue
        frozen = getattr(config, name)
        environment = frozen["environment"]
        env_fn = get_scenario(environment)
        recomputed = verify_frozen_floor_env(env_fn, frozen)
        results[environment] = {
            "config_constant": name, "frozen_value": frozen["value"],
            "recomputed_value": recomputed, "status": "OK",
        }
    return results


def _capture_full_trajectory(lesson: str, environment: str, genome: Dict[str, Any],
                              seed: int) -> Dict[int, Optional[float]]:
    """Przechwytuje prediction_error z KAZDEGO ticka (wszystkie ticki okna,
    nie tylko wczesne) - ten sam wzorzec monkeypatch co pilot_final.py, bez
    filtra tick<W_EARLY_TICKS. None gdzie brak wartosci (NIE zero) -
    porzucona trajektoria typu prediction/input (runner nie liczy Spearmana -
    zadanie evaluatora).

    Zero literalu nazwy lekcji: porownanie WYLACZNIE przeciw CONFIG (_lesson()),
    nie przeciw wpisanej na sztywno wartosci - ten runner strukturalnie zna
    tylko run_shock_recovery (L1.2), wiec sprawdza zgodnosc z tym, co CONFIG
    DZIS deklaruje, zamiast zakladac, ze zawsze bedzie to ta sama litera."""
    if lesson != _lesson():
        raise ValueError(
            f"lesson={lesson!r} != EXPERIMENT_CONFIG['protocol']['lesson']={_lesson()!r} "
            "- ten runner wywoluje wylacznie run_shock_recovery i nie ma jak "
            "obsluzyc innej lekcji"
        )

    trajectory: Dict[int, Optional[float]] = {}
    original = SnapshotEngine.create_snapshot

    def spy(self, *args, **kwargs):
        snapshot = original(self, *args, **kwargs)
        tick = kwargs.get("tick")
        if tick is not None:
            trajectory[tick] = kwargs.get("prediction_error")
        return snapshot

    SnapshotEngine.create_snapshot = spy
    try:
        run_shock_recovery(
            genome_preset=genome["genome_preset"], seed=seed, scenario=environment,
            ticks_total=_ticks_total(), genome_params=genome["genome_params"],
            genome_label=genome["genome_id"], observe=True,
        )
    finally:
        SnapshotEngine.create_snapshot = original
    return trajectory


def _record(lesson: str, environment: str, genome_id: str, seed: int,
            trajectory: Dict[int, Optional[float]]) -> Dict[str, Any]:
    """Schemat wzorowany na BUILD-006 (pipeline.py::_record): run_id/genome/
    environment/lesson/seed/timestamp/metrics/output_hash. metrics = PELNA
    trajektoria prediction_error per tick (klucze jako string - wymog JSON),
    None gdzie brak - nie zerowane."""
    metrics = {
        "prediction_error_by_tick": {str(t): v for t, v in sorted(trajectory.items())},
        "n_ticks_total": len(trajectory),
        "n_ticks_none": sum(1 for v in trajectory.values() if v is None),
    }
    metrics_json = json.dumps(metrics, sort_keys=True, default=str)
    return {
        "run_id": f"{lesson}_{genome_id}_{environment}_s{seed}",
        "genome": genome_id,
        "environment": environment,
        "lesson": lesson,
        "seed": seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "output_hash": hashlib.sha256(metrics_json.encode("utf-8")).hexdigest(),
    }


def write_checkpoint(logs_dir: Path, completed: int, total: int, results_path: Path) -> Path:
    """Powielone z pipeline.py (BUILD-004) - CELOWO, nie importowane
    (pipeline.py pozostaje nietkniety, patrz docstring modulu)."""
    ckpt = {
        "completed": completed, "total": total,
        "fraction": round(completed / total, 6),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results_path": str(results_path),
    }
    ckpt_path = logs_dir / f"checkpoint_{completed}.json"
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, indent=2, ensure_ascii=False)
    latest_path = logs_dir / "checkpoint_latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, indent=2, ensure_ascii=False)
    return ckpt_path


def resume_from_checkpoint(logs_dir: Path) -> int:
    latest_path = logs_dir / "checkpoint_latest.json"
    if not latest_path.exists():
        return 0
    with open(latest_path, encoding="utf-8") as f:
        ckpt = json.load(f)
    return ckpt["completed"]


def run_confirmatory_pipeline(specs: List[Tuple[str, str, str, int]], results_path: Path,
                               logs_dir: Path, checkpoint_intervals: List[int],
                               resume: bool = True, verify_floors: bool = True) -> Dict[str, Any]:
    logs_dir.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    _assert_perceive_always_on()
    floor_verification = verify_floors_before_run() if verify_floors else None

    start_index = resume_from_checkpoint(logs_dir) if resume else 0
    genomes_by_id = _genome_lookup()

    mode = "a" if start_index > 0 else "w"
    total = len(specs)
    completed = start_index

    with open(results_path, mode, encoding="utf-8") as out:
        for i, (lesson, environment, genome_id, seed) in enumerate(specs[start_index:], start=start_index):
            genome = genomes_by_id[genome_id]
            trajectory = _capture_full_trajectory(lesson, environment, genome, seed)
            record = _record(lesson, environment, genome_id, seed, trajectory)
            out.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            completed = i + 1

            if completed in checkpoint_intervals or completed == total:
                out.flush()
                write_checkpoint(logs_dir, completed, total, results_path)

    return {
        "total": total, "completed": completed, "results_path": str(results_path),
        "resumed_from": start_index, "floor_verification": floor_verification,
    }


def run_dry_run() -> Dict[str, Any]:
    """Mechanika (czy sie wykonuje, czy zapisuje schemat, czy wznawia z
    checkpointu) - NIE eksperyment, NIE zadna wielkosc inferencyjna. Seedy
    rozlaczne ze wszystkimi udokumentowanymi zakresami (patrz docstring
    modulu, assert_dry_run_seeds_disjoint)."""
    specs = build_dry_run_specs()
    expected = len(_genomes()) * DRY_RUN_N_SEEDS * len(_environments())
    assert len(specs) == expected, f"DRY RUN oczekuje {expected} specow, otrzymano {len(specs)}"
    results_path = PACKAGE_ROOT / "results" / "pc_001_confirmatory_dry_run_results.jsonl"
    logs_dir = PACKAGE_ROOT / "logs" / "pc_001_confirmatory_dry_run"
    return run_confirmatory_pipeline(
        specs, results_path, logs_dir,
        checkpoint_intervals=DRY_RUN_CHECKPOINT_INTERVALS,
        resume=False, verify_floors=True,
    )


def run_confirmatory_experiment() -> Dict[str, Any]:
    """PELNY Eksperyment Konfirmacyjny PC-001 (552 przebiegi). NIE WOLANE
    przez ten modul ani przez jego testy - zakaz jawny w zleceniu B4C-01.
    Eksperyment startuje dopiero po B5 (PC_001_BASELINE) i B6 (Bramka
    wejscia). Funkcja istnieje dla tamtego kroku, nie dla tego zlecenia."""
    specs = build_confirmatory_run_specs()
    expected = len(_genomes()) * N_OPERATIONAL_SEEDS * len(_environments())
    assert len(specs) == expected, f"Konfirmacja oczekuje {expected} specow, otrzymano {len(specs)}"
    results_path = PACKAGE_ROOT / "results" / "pc_001_confirmatory_results.jsonl"
    logs_dir = PACKAGE_ROOT / "logs" / "pc_001_confirmatory"
    return run_confirmatory_pipeline(
        specs, results_path, logs_dir,
        checkpoint_intervals=CHECKPOINT_INTERVALS,
        resume=True, verify_floors=True,
    )


if __name__ == "__main__":
    summary = run_dry_run()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
