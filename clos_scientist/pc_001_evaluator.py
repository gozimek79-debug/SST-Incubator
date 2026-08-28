"""Evaluator konfirmacyjny PC-001 - w budowie (B4C-2, STOP CZESCIOWY, decyzje
CTO B4C-2 (06)/(07)/(08)/(09)). Ten plik NIE jest jeszcze kompletny i NIE jest
jeszcze czlonkiem CRITICAL_FILES_PC_001 - wejdzie do rejestru DOPIERO jako plik
KOMPLETNY, razem z clos_scientist/pc_001_k1_shuffle.py (regula osiagalnosci,
B4C-2 (08)), 55 -> 57. "Polowa evaluatora w rejestrze byla by gorsza niz brak"
(CTO, B4C-2 (06)) - Hard-Halt zaczalby chronic plik, o ktorym wiadomo, ze
jeszcze nie liczy tego, co ma liczyc.

"Evaluator konfirmacyjny ma byc celowo NUDNY: odczytuje zamrozona konfiguracje
i wykonuje ja dokladnie raz w jeden sposob." (CTO, B4C-2 (01) v2)

============================================================================
STOP CZESCIOWY, NADAL AKTUALNY (B4C-2 (06)/(07)/(09))
============================================================================
Ten plik jest NIEKOMPLETNY - sciezka SKLADANIA WERDYKTU KONCOWEGO (WSPARTA/
INCONCLUSIVE/NIE WSPARTA) istnieje WYLACZNIE jako compose_verdict() ponizej,
ktora ZAWSZE RZUCA VerdictCompositionBlockedError, nigdy nie zwraca werdyktu.
Powod: decyzja CTO, oczekuje na Negative-Control Inference Review (szesc z
jedenastu komorek ma kryterium wsparcia BRAK_ODRZUCENIA_H0; BH-FDR nie
kontroluje bledu dla tego kierunku - kontroluje odsetek falszywych ODRZUCEN,
nie falszywych BRAKOW odrzucenia - mocy wykrycia naruszenia nikt nie policzyl
dla zadnej z tych szesciu). Zbior zablokowanych komorek jest WYPROWADZONY z
pola "kierunek_wsparcia" w publications/pc_001_bh_family.json przy KAZDYM
wywolaniu compose_verdict() - NIGDY z wpisanej na sztywno listy szesciu ID
(gdyby Review zmienil kierunek ktorejkolwiek komorki, zbior blokady ma
przesunac sie SAM).

WOLNO liczyc kazda liczbe prowadzaca do werdyktu (p, pozycje BH, decyzje per
komorka) dla wszystkich 11 komorek - patrz np. k4_separation_cell() ponizej.
NIE WOLNO zlozyc jednego obiektu-werdyktu z tych liczb.

============================================================================
K4-SEPARACJA (ERRATUM 1, B4C-2 (09))
============================================================================
Srodowiska: noise_world (Primary) vs pure_noise_world (K4) - NIE shock_world
(ANEKS 1 -> "Zmiana 3" zawieral wewnetrzna sprzecznosc, poprawiona przez
publications/preregistration_PC_001_ERRATUM_1_2026-08-27.md - shock_world
nigdy nie mial zamrozonej podlogi, redukcja_W2 tam nigdy nie byla wykonalna).

Obie strony licza redukcja_W2 TA SAMA funkcja (redukcja_w2_for_run ponizej),
tym samym wywolaniem, z jedyna roznica w argumencie `environment` (ktora
podloga/CONFIG uzyc) - patrz test tozsamosci obiektu w
tests/test_pc_001_evaluator.py::TestK4SeparationSharedReductionFunction.
Osobna implementacja dla ktorejkolwiek strony zniszczylaby porownywalnosc -
to jest cala tresc tej komorki (ERRATUM 1, zadanie 5).

Okna: CONFIG::W_EARLY_TICKS / CONFIG::W_LATE_TICKS - te same co Warunek A/B
i K4-A/K4-B. NIE okna zakotwiczone w shock_tick (naleza wylacznie do K3a) -
uzasadnienie CTO: gdyby jedna strona uzywala okien Primary, a druga
szokowych, kontrola przestalaby byc separacja srodowisk.

ZAKAZ WPROST (ERRATUM 1, zadanie 5): zaden literal "shock_world" w kodzie
tej komorki - wymuszony test w tests/test_pc_001_evaluator.py (wzorem linii
512 z tests/test_pc_001_confirmatory_runner_guarantee.py: "0.2" not in
no_docstring).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from clos_curriculum.laboratory.statistics import block_means, mann_whitney_u
from clos_scientist.pc_001_experiment_config import (
    EXPERIMENT_CONFIG,
    FROZEN_FLOOR_NOISE_WORLD,
    FROZEN_FLOOR_PURE_NOISE_WORLD,
)
from clos_scientist.w2_endpoint import compute_pe_reducible, compute_w2_reduction

REPO_ROOT = Path(__file__).resolve().parent.parent
BH_FAMILY_PATH = REPO_ROOT / "publications" / "pc_001_bh_family.json"

# Wartosc, przy ktorej pole 'kierunek_wsparcia' (publications/pc_001_bh_family.json,
# B4C-2 (07)) blokuje skladanie werdyktu koncowego - patrz VerdictCompositionBlockedError.
_BLOCKING_KIERUNEK = "BRAK_ODRZUCENIA_H0"


class VerdictCompositionBlockedError(Exception):
    """STOP CZESCIOWY (B4C-2 (06)/(07)/(09), decyzja CTO): sciezka skladania
    werdyktu koncowego (WSPARTA/INCONCLUSIVE/NIE WSPARTA) jest ZABLOKOWANA do
    czasu wyniku Negative-Control Inference Review. Powod: dla komorek o
    kierunek_wsparcia=="BRAK_ODRZUCENIA_H0" (BH-FDR nie kontroluje bledu w
    tym kierunku - kontroluje odsetek falszywych ODRZUCEN, nie falszywych
    BRAKOW odrzucenia), moc wykrycia naruszenia nie zostala policzona.
    Zbior zablokowanych komorek jest ZAWSZE WYPROWADZONY z pola
    'kierunek_wsparcia' w artefakcie rodziny - NIGDY z wpisanej na sztywno
    listy ID (B4C-2 (09), zakaz wprost: 'liczba 6 NIE MA prawa pojawic sie
    w kodzie evaluatora jako literal')."""


def compose_verdict(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
    """Zawsze rzuca VerdictCompositionBlockedError - patrz docstring
    wyjatku i sekcja 'STOP CZESCIOWY' w docstringu modulu. Argumenty
    przyjmowane i ignorowane celowo: sygnatura ma pozostac stabilna, gdy
    blokada zostanie zdjeta (Negative-Control Inference Review), zamiast
    wymuszac zmiane wywolujacych w dwoch krokach."""
    family = json.loads(BH_FAMILY_PATH.read_text(encoding="utf-8"))
    blocked = sorted(
        cell["id"] for cell in family["cells_active"]
        if cell["kierunek_wsparcia"] == _BLOCKING_KIERUNEK
    )
    raise VerdictCompositionBlockedError(
        f"Skladanie werdyktu koncowego zablokowane do czasu Negative-Control "
        f"Inference Review (B4C-2 (06), decyzja CTO). Zablokowane komorki "
        f"(kierunek_wsparcia={_BLOCKING_KIERUNEK!r}, {len(blocked)}/"
        f"{len(family['cells_active'])}): {blocked}."
    )


class IncompleteGridError(Exception):
    """Siatka (genomy x seedy) niekompletna dla bloku seedowego - komorka nie
    da sie policzyc na tych danych. W pelnym evaluatorze (przyszle zlecenie)
    to sciezka do statusu komorki INCONCLUSIVE (scenariusz A, B4C-2 (01) v2),
    NIE cichy pomin blok/None."""


class UnknownEnvironmentForFloorError(Exception):
    """redukcja_w2_for_run() wywolane dla srodowiska bez zamrozonej podlogi w
    tym kontekscie (K4-separacja uzywa WYLACZNIE noise_world/pure_noise_world,
    ERRATUM 1) - HALT, nie domyslna wartosc podlogi."""


def _floor_result_for_environment(environment: str) -> Dict[str, Any]:
    """floor_result w ksztalcie oczekiwanym przez
    clos_scientist.w2_endpoint.compute_pe_reducible (model "constant"),
    zbudowany z JUZ ZAMROZONYCH wartosci CONFIG - evaluator NIE liczy podlogi
    na nowo (to zadanie runnera, verify_floors_before_run(), przy starcie
    eksperymentu)."""
    primary = EXPERIMENT_CONFIG["environments"]["primary"]
    k4 = EXPERIMENT_CONFIG["environments"]["K4"]
    if environment == primary:
        frozen = FROZEN_FLOOR_NOISE_WORLD
    elif environment == k4:
        frozen = FROZEN_FLOOR_PURE_NOISE_WORLD
    else:
        raise UnknownEnvironmentForFloorError(
            f"brak zamrozonej podlogi dla srodowiska {environment!r} w tym "
            f"kontekscie - oczekiwano {primary!r} lub {k4!r}"
        )
    return {"floor_model": frozen["floor_model"], "floor_env": frozen["value"]}


def redukcja_w2_for_run(pe_trajectory: Dict[int, Optional[float]], environment: str) -> Optional[float]:
    """redukcja_W2 dla JEDNEGO przebiegu (genom, seed) w danym srodowisku -
    W2-SPEC §2.3, przez clos_scientist.w2_endpoint (compute_pe_reducible +
    compute_w2_reduction) - zero wlasnej reimplementacji formuly tutaj.
    None, gdy przebieg nie jest VALID (FLOOR_LIMITED/INSUFFICIENT_DATA) -
    brak wyniku, NIE wynik zerowy (patrz w2_endpoint.compute_w2_reduction)."""
    floor_result = _floor_result_for_environment(environment)
    pe_red = compute_pe_reducible(pe_trajectory, floor_result)
    return compute_w2_reduction(pe_red)["reduction"]


def _reduction_by_seed(records: List[Dict[str, Any]], environment: str,
                        n_genomes_expected: int) -> List[List[float]]:
    """Grupuje rekordy runnera po seedzie, liczy redukcja_w2_for_run() dla
    kazdego, i zwraca macierz [ [wartosci 23 genomow dla seeda_1], ... ] -
    WEJSCIE do STATS::block_means (kontrakt: kolumna wejsciowa per blok
    seedowy). Kazdy blok musi miec DOKLADNIE n_genomes_expected wartosci
    NIE-None - niekompletna siatka (brakujacy genom, FLOOR_LIMITED/
    INSUFFICIENT_DATA przebieg w bloku) -> IncompleteGridError, nie ciche
    pominiecie brakujacej pozycji."""
    by_seed: Dict[int, List[Optional[float]]] = {}
    for rec in records:
        pe_trajectory = {int(t): v for t, v in rec["metrics"]["prediction_error_by_tick"].items()}
        reduction = redukcja_w2_for_run(pe_trajectory, environment)
        by_seed.setdefault(rec["seed"], []).append(reduction)

    columns: List[List[float]] = []
    for seed in sorted(by_seed):
        values = by_seed[seed]
        if len(values) != n_genomes_expected or any(v is None for v in values):
            raise IncompleteGridError(
                f"srodowisko={environment!r} seed={seed}: oczekiwano "
                f"{n_genomes_expected} kompletnych (nie-None) wartosci redukcja_W2, "
                f"otrzymano {sum(1 for v in values if v is not None)}/{len(values)} - "
                "siatka niekompletna, blok nie da sie policzyc"
            )
        columns.append(values)
    return columns


def k4_separation_cell(noise_world_records: List[Dict[str, Any]],
                        pure_noise_world_records: List[Dict[str, Any]],
                        n_genomes_expected: int) -> Dict[str, Any]:
    """Komorka K4-separacja (ERRATUM 1, B4C-2 (09)): noise_world vs
    pure_noise_world, redukcja_W2 (TA SAMA funkcja obu stron), agregacja
    blokowa przez STATS::block_means, STATS::mann_whitney_u.

    Zwraca surowe skladniki (p, statystyka, srednie blokowe obu stron) -
    NIE decyzje per komorka i NIE werdykt (blokada B4C-2 (06)/(07) - decyzja
    o skladaniu werdyktu czeka na Negative-Control Inference Review; ta
    komorka jest ODRZUCENIE_H0, wiec nie jest jedna z szesciu zablokowanych,
    ale werdykt jest JEDNYM obiektem i nie ma czegos jak werdykt czesciowy,
    B4C-2 (07))."""
    primary = EXPERIMENT_CONFIG["environments"]["primary"]
    k4 = EXPERIMENT_CONFIG["environments"]["K4"]

    noise_world_blocks = block_means(_reduction_by_seed(noise_world_records, primary, n_genomes_expected))
    pure_noise_world_blocks = block_means(_reduction_by_seed(pure_noise_world_records, k4, n_genomes_expected))

    if len(noise_world_blocks) != len(pure_noise_world_blocks):
        raise IncompleteGridError(
            f"liczba blokow seedowych niezgodna miedzy stronami: "
            f"noise_world={len(noise_world_blocks)}, pure_noise_world={len(pure_noise_world_blocks)} "
            "- ERRATUM 1 wymaga n_a=n_b (ten sam zestaw N_operational seedow po obu stronach, "
            "uklad skrzyzowany runnera)"
        )

    test_result = mann_whitney_u(noise_world_blocks, pure_noise_world_blocks)

    return {
        "cell_id": "K4-separacja",
        "noise_world_block_means": noise_world_blocks,
        "pure_noise_world_block_means": pure_noise_world_blocks,
        "n_a": len(noise_world_blocks),
        "n_b": len(pure_noise_world_blocks),
        "test_result": test_result,
    }
