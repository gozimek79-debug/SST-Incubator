"""Evaluator konfirmacyjny PC-001 - w budowie (B4C-2, STOP CZESCIOWY, decyzje
CTO B4C-2 (06)/(07)/(08)/(09)/(15)). Ten plik NIE jest jeszcze kompletny i NIE
jest jeszcze czlonkiem CRITICAL_FILES_PC_001 - wejdzie do rejestru DOPIERO
jako plik KOMPLETNY, razem z clos_scientist/pc_001_k1_shuffle.py (regula
osiagalnosci, B4C-2 (08)), 59 -> 61. "Polowa evaluatora w rejestrze byla by
gorsza niz brak" (CTO, B4C-2 (06)) - Hard-Halt zaczalby chronic plik, o
ktorym wiadomo, ze jeszcze nie liczy tego, co ma liczyc.

"Evaluator konfirmacyjny ma byc celowo NUDNY: odczytuje zamrozona konfiguracje
i wykonuje ja dokladnie raz w jeden sposob." (CTO, B4C-2 (01) v2)

============================================================================
STOP CZESCIOWY, NADAL AKTUALNY (B4C-2 (06)/(07)/(09)/(15))
============================================================================
Ten plik jest NIEKOMPLETNY - sciezka SKLADANIA WERDYKTU KONCOWEGO (WSPARTA/
INCONCLUSIVE/NIE WSPARTA) istnieje WYLACZNIE jako compose_verdict() ponizej,
ktora ZAWSZE RZUCA VerdictCompositionBlockedError, nigdy nie zwraca werdyktu.
Powod (B4C-2 (15)): Negative-Control Inference Review ZAMKNIETY POZYTYWNIE -
szesc komorek (K1-A/B, K4-A/B, K5-A/B) przeszlo z "brak odrzucenia H0" na
formalne wnioskowanie o ROWNOWAZNOSCI PRAKTYCZNEJ (TOST, ERRATUM 3) - ale
POWER CHECK dla tej rownowaznosci (moc kazdej komorki, minimum z szesciu,
P(cala szostka przechodzi), zachowanie po korekcie BH) jest OSOBNYM,
NASTEPNYM krokiem, jeszcze nie wykonanym. Zbior zablokowanych komorek jest
WYPROWADZONY z pol "kierunek_wsparcia"=="ROWNOWAZNOSC" ORAZ braku pola
"equivalence_power_check_closed" w publications/pc_001_bh_family.json przy
KAZDYM wywolaniu compose_verdict() - NIGDY z wpisanej na sztywno listy
szesciu ID (gdyby power check zamknal sie dla jednej komorki, zbior blokady
ma zmniejszyc sie SAM, bez edycji tego pliku).

WOLNO liczyc kazda liczbe prowadzaca do werdyktu (p, pozycje BH, decyzje per
komorka) dla wszystkich 11 komorek - patrz k4_separation_cell()/
k1_equivalence_cell()/k4_equivalence_cell()/k5_equivalence_cell() ponizej
(6 z 11 juz zaimplementowanych: K4-separacja + szesc rownowaznosci; Warunek
A/B, K3a-warunek1, K6 - jeszcze nie). NIE WOLNO zlozyc jednego
obiektu-werdyktu z tych liczb.

ZNANA LUKA (zglaszana, nie domyslnie wypelniona): pola "bh_adjusted_result"
i finalne "equivalence_supported" (patrz _equivalence_result nizej) wymagaja
wspolnej korekty BH-FDR na WSZYSTKICH 11 komorkach naraz - niewykonalne, dopoki
Warunek A/B/K3a-1/K6 nie maja wlasnych funkcji-komorek w tym pliku (dzis
gotowa jest wylacznie K4-separacja z pieciu komorek ODRZUCENIE_H0 - CZTERY
wciaz brakuja, korekta CTO wobec (15): to NIE jest "evaluator bez
ostatniego kroku"). Oba pola zwracane jako PENDING_FULL_FAMILY_BH (B4C-2
(16), korekta CTO: NIE None - w tym repo None juz znaczy "nie da sie
policzyc dla tych danych", zobacz w2_endpoint.compute_w2_reduction;
uzycie go tez dla "jeszcze nie zaimplementowane" nakladaloby dwa rozne
stany na jedna reprezentacje).

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

============================================================================
SZESC KOMOREK ROWNOWAZNOSCI (ERRATUM 3, B4C-2 (15))
============================================================================
K1-A/K1-B (surogat z przetasowaniem, WYLACZNIE noise_world - B4C-05 v4 pkt 1),
K4-A/K4-B (brak efektu w czystym szumie, pure_noise_world), K5-A/K5-B
(ablacja surogatowa, WYLACZNIE noise_world) - kazda para dzieli sie na
"czesc A" (efekt=E_beta) i "czesc B" (efekt=E_red=redukcja_W2).

E_beta/E_red POLICZONE PER PRZEBIEG, DOPIERO POTEM block_means po 23
genomach (ERRATUM 3, "Kolejnosc operacji") - TA SAMA kolejnosc co juz
istniejace redukcja_w2_for_run/_reduction_by_seed. Test: STATS::tost_wilcoxon
(TOST), margines rownowaznosci CZYTANY z artefaktu per komorka
(_margin_for_cell) - NIGDY stala w kodzie.

K1: JEDNA permutacja (derive_k1_permutation) per blok seedowy, dzielona
przez wszystkie 23 genomy tego seeda - wyliczona raz per seed w
k1_equivalence_cell, NIE per-genom (B4C-1 (05), decyzja CTO). Ziarno,
identyfikator algorytmu i digest permutacji zapisane w wyniku
(k1_shuffle_by_seed).

K5: PE_ablated(t) = |K5_ABLATED_PREDICTION_CONSTANT - input(t)| - stala z
CONFIG (zweryfikowana przeciw clos_brain/runtime/prediction.py:20), NIE
literal w tym pliku.

Warunki twarde dla E_beta (per obserwacja blokowa, ERRATUM 3): beta
skonczone, siatka kompletna, W_early_red skonczone, W_early_red > 0 - brak
KTOREGOKOLWIEK -> None -> IncompleteGridError przy agregacji blokowej
(scenariusz A, B4C-2 (01) v2 - NONCOMPUTABLE -> caly PC-001 INCONCLUSIVE).
NIGDY epsilon/mediana populacji/wartosc z pilota/pominiecie bloku/zmniejszenie n.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from clos_curriculum.laboratory.statistics import (
    block_means, mann_whitney_u, linear_slope, DegenerateInputError, tost_wilcoxon,
)
from clos_scientist.pc_001_experiment_config import (
    EXPERIMENT_CONFIG,
    FROZEN_FLOOR_NOISE_WORLD,
    FROZEN_FLOOR_PURE_NOISE_WORLD,
    K5_ABLATED_PREDICTION_CONSTANT,
)
from clos_scientist.pc_001_k1_shuffle import (
    derive_k1_permutation, k1_permutation_digest, k1_shuffle_seed, K1_SHUFFLE_ALGORITHM_ID,
)
from clos_scientist.w2_endpoint import compute_pe_reducible, compute_w2_reduction

REPO_ROOT = Path(__file__).resolve().parent.parent
BH_FAMILY_PATH = REPO_ROOT / "publications" / "pc_001_bh_family.json"

# Wartosc, przy ktorej pole 'kierunek_wsparcia' (publications/pc_001_bh_family.json,
# B4C-2 (07)/(15)) blokuje skladanie werdyktu koncowego - patrz
# VerdictCompositionBlockedError. Pole "equivalence_power_check_closed" NIE
# istnieje jeszcze w artefakcie (przyszle zlecenie, power check dla
# rownowaznosci, decyzja CTO pkt 10/11 B4C-2 (15)) - .get(...) z domyslnym
# False oznacza, ze DZIS wszystkie szesc komorek ROWNOWAZNOSC sa zablokowane
# (brak pola = nie zamkniete), a gdy przyszle zlecenie dopisze to pole per
# komorka, zbior blokady zmniejszy sie SAM, bez edycji tego pliku.
_BLOCKING_KIERUNEK = "ROWNOWAZNOSC"
_POWER_CHECK_FIELD = "equivalence_power_check_closed"


class VerdictCompositionBlockedError(Exception):
    """STOP CZESCIOWY (B4C-2 (06)/(07)/(09)/(15), decyzja CTO): sciezka
    skladania werdyktu koncowego (WSPARTA/INCONCLUSIVE/NIE WSPARTA) jest
    ZABLOKOWANA do czasu zamkniecia power check dla rownowaznosci praktycznej
    (nastepny krok po tym zleceniu - moc kazdej z szesciu komorek
    ROWNOWAZNOSC, minimum z szesciu, P(cala szostka przechodzi), zachowanie
    po korekcie BH przy m=11; prog akceptacji 80% per komorka). Zbior
    zablokowanych komorek jest ZAWSZE WYPROWADZONY z pol 'kierunek_wsparcia'
    i 'equivalence_power_check_closed' w artefakcie rodziny - NIGDY z
    wpisanej na sztywno listy ID (B4C-2 (09), zakaz wprost: 'liczba 6 NIE MA
    prawa pojawic sie w kodzie evaluatora jako literal')."""


def compose_verdict(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
    """Zawsze rzuca VerdictCompositionBlockedError - patrz docstring
    wyjatku i sekcja 'STOP CZESCIOWY' w docstringu modulu. Argumenty
    przyjmowane i ignorowane celowo: sygnatura ma pozostac stabilna, gdy
    blokada zostanie zdjeta (power check), zamiast wymuszac zmiane
    wywolujacych w dwoch krokach."""
    family = json.loads(BH_FAMILY_PATH.read_text(encoding="utf-8"))
    blocked = sorted(
        cell["id"] for cell in family["cells_active"]
        if cell["kierunek_wsparcia"] == _BLOCKING_KIERUNEK
        and not cell.get(_POWER_CHECK_FIELD, False)
    )
    raise VerdictCompositionBlockedError(
        f"Skladanie werdyktu koncowego zablokowane do czasu zamkniecia power "
        f"check dla rownowaznosci (B4C-2 (15), decyzja CTO). Zablokowane "
        f"komorki (kierunek_wsparcia={_BLOCKING_KIERUNEK!r} bez "
        f"{_POWER_CHECK_FIELD!r}, {len(blocked)}/{len(family['cells_active'])}): "
        f"{blocked}."
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


# ============================================================================
# ROWNOWAZNOSC PRAKTYCZNA (ERRATUM 3, B4C-2 (15)): K1-A/K1-B, K4-A/K4-B,
# K5-A/K5-B. E_beta/E_red POLICZONE PER PRZEBIEG, DOPIERO POTEM block_means -
# ta sama kolejnosc co redukcja_w2_for_run/_reduction_by_seed powyzej
# (ERRATUM 3, sekcja "Kolejnosc operacji").
# ============================================================================

# tick_span dzisiejszego protokolu (300 tickow, 0..299) - WYPROWADZONY z
# EXPERIMENT_CONFIG, NIE literal (ERRATUM 3: "tick_span WYPROWADZAJ, NIE
# WPISUJ"). Uzywany WYLACZNIE do assercji w e_beta_for_run - jesli protokol
# kiedys zmieni dlugosc przebiegu, ta stala i sama assercja pozostana
# spojne, bo obie pochodza z tego samego zrodla.
_EXPECTED_TICK_SPAN = EXPERIMENT_CONFIG["protocol"]["ticks_total"] - 1


def e_beta_components_for_run(pe_trajectory: Dict[int, Optional[float]],
                               environment: str) -> Optional[Tuple[float, float, float]]:
    """(beta_raw, W_early_red, E_beta) POLICZONE PER PRZEBIEG (ERRATUM 3).
    beta_raw = linear_slope na PELNEJ siatce tego przebiegu; tick_span =
    max(ticks)-min(ticks) WYPROWADZONY z faktycznej siatki, NIE wpisany jako
    literal - assercja pilnuje, ze rowna sie oczekiwanej wartosci przy
    dzisiejszym protokole (pada GLOSNO, jesli siatka kiedys sie skroci,
    zamiast po cichu policzyc zly wynik). W_early_red z TEGO SAMEGO
    przebiegu (compute_w2_reduction, ta sama funkcja co redukcja_W2).
    E_beta = beta_raw * tick_span / W_early_red.

    Warunki twarde (ERRATUM 3): beta skonczone, siatka kompletna,
    W_early_red skonczone, W_early_red > 0 - brak KTOREGOKOLWIEK -> None
    (NIGDY epsilon/wartosc zastepcza). W_early_red DODATNIE nawet dla
    przebiegow FLOOR_LIMITED (asymetria zastana wobec E_red/redukcja_W2,
    patrz ERRATUM 3) - E_beta jest wiec DEFINIOWALNE czesciej niz E_red."""
    floor_result = _floor_result_for_environment(environment)
    pe_red = compute_pe_reducible(pe_trajectory, floor_result)
    w_early_red = compute_w2_reduction(pe_red)["w_early_red"]
    if w_early_red is None or w_early_red <= 0:
        return None

    ticks = sorted(t for t, v in pe_red.items() if v is not None)
    expected_ticks = set(range(EXPERIMENT_CONFIG["protocol"]["ticks_total"]))
    if set(ticks) != expected_ticks:
        return None  # siatka niekompletna - NIGDY pominiecie brakujacych tickow

    values = [pe_red[t] for t in ticks]
    try:
        beta_raw = linear_slope(ticks, values)
    except DegenerateInputError:
        return None

    tick_span = max(ticks) - min(ticks)
    # KONTROLA REDUNDANTNA, oznaczona jako taka (B4C-2 (16), korekta CTO
    # wobec wlasnego zdania z (15) "asercja padnie glosno" - nie padnie,
    # zgloszone przez wykonawce, nie przemilczane): DZIS ta asercja jest
    # NIEOSIAGALNA jako FAIL, bo gwarantuje to kontrola kompletnosci siatki
    # wyzej (set(ticks) == set(range(ticks_total)) wymusza min=0, max=
    # ticks_total-1, wiec span=ticks_total-1 ZAWSZE, gdy ten warunek
    # przechodzi). ZYWA DOPIERO, gdyby ta kontrola kompletnosci zostala
    # kiedys OSLABIONA (np. zmieniona na sprawdzenie samej dlugosci zbioru
    # zamiast jego dokladnej zawartosci) - wtedy niekompletna, ale
    # rownoliczna siatka mogla przejsc kontrole kompletnosci, a ta asercja
    # bylaby JEDYNYM zabezpieczeniem lapiacym zly tick_span. Regula ogolna
    # (B4C-2 (16)): kontrola redundantna jest dopuszczalna, gdy jest
    # oznaczona jako redundantna i gdy nazwany jest scenariusz, w ktorym
    # przestaje byc redundantna - kontrola redundantna, ktora WYGLADA na
    # zywa, jest dokladnie tym, co ten projekt tropi.
    assert tick_span == _EXPECTED_TICK_SPAN, (
        f"tick_span={tick_span} != oczekiwany {_EXPECTED_TICK_SPAN} "
        "(EXPERIMENT_CONFIG['protocol']['ticks_total']-1) - dlugosc przebiegu "
        "zmieniona bez aktualizacji tej assercji, ERRATUM 3"
    )
    e_beta = beta_raw * tick_span / w_early_red
    return beta_raw, w_early_red, e_beta


def e_beta_for_run(pe_trajectory: Dict[int, Optional[float]], environment: str) -> Optional[float]:
    """Wygoda: sama wartosc E_beta, gdy skladowe (beta_raw/W_early_red) nie
    sa potrzebne osobno - patrz e_beta_components_for_run."""
    components = e_beta_components_for_run(pe_trajectory, environment)
    return components[2] if components is not None else None


# E_red = redukcja_W2 (ERRATUM 3) - juz bezwymiarowe, TA SAMA wartosc co
# redukcja_w2_for_run. WIAZANIE NAZWY (nie nowa funkcja z wlasnym wywolaniem)
# - e_red_for_run JEST redukcja_w2_for_run (ten sam obiekt: `e_red_for_run is
# redukcja_w2_for_run` == True), wiec skan AST liczacy wywolania
# redukcja_w2_for_run() nie widzi tu drugiego miejsca - jest TYLKO jedno,
# wewnatrz _reduction_by_seed, tak jak wymaga ERRATUM 1 zadanie 5. Odrebna
# nazwa dokumentuje, ze w kontekscie rownowaznosci ta sama liczba nosi inna
# semantyke (odleglosc od zera w obie strony, nie kierunkowy dowod redukcji).
e_red_for_run = redukcja_w2_for_run


def _record_pe_trajectory(record: Dict[str, Any]) -> Dict[int, Optional[float]]:
    return {int(t): v for t, v in record["metrics"]["prediction_error_by_tick"].items()}


def _shuffled_pe_trajectory(record: Dict[str, Any], permutation: List[int]) -> Dict[int, Optional[float]]:
    """K1 (surogat z przetasowaniem, PC-001 §5 -> 'K1'): PE_shuffled(t) =
    |prediction(perm[t]) - input(t)| - JEDNA permutacja per blok seedowy,
    dzielona przez wszystkie 23 genomy (wywolujacy przekazuje TA SAMA
    `permutation`, wyliczona raz per seed - patrz k1_equivalence_cell)."""
    prediction = {int(t): v for t, v in record["metrics"]["prediction_by_tick"].items()}
    input_ = {int(t): v for t, v in record["metrics"]["input_by_tick"].items()}
    result: Dict[int, Optional[float]] = {}
    for t in prediction:
        shuffled_source = permutation[t] if t < len(permutation) else None
        p_shuffled = prediction.get(shuffled_source) if shuffled_source is not None else None
        i_t = input_.get(t)
        if p_shuffled is None or i_t is None:
            result[t] = None
        else:
            result[t] = abs(p_shuffled - i_t)
    return result


def _ablated_pe_trajectory(record: Dict[str, Any]) -> Dict[int, Optional[float]]:
    """K5 (ablacja surogatowa, PC-001 §5 -> 'K5'): PE_ablated(t) =
    |K5_ABLATED_PREDICTION_CONSTANT - input(t)| - stala z CONFIG (zweryfikowana
    wprost przeciw clos_brain/runtime/prediction.py:20, patrz komentarz przy
    stalej), NIE literal w tym pliku."""
    input_ = {int(t): v for t, v in record["metrics"]["input_by_tick"].items()}
    return {
        t: (abs(K5_ABLATED_PREDICTION_CONSTANT - v) if v is not None else None)
        for t, v in input_.items()
    }


def _effect_by_seed(records: List[Dict[str, Any]], environment: str, n_genomes_expected: int,
                     per_run_trajectory_fn, per_run_effect_fn) -> List[List[float]]:
    """Generalizacja _reduction_by_seed: `per_run_trajectory_fn(record) ->
    pe_trajectory` (surowa, przetasowana albo ablowana), `per_run_effect_fn
    (pe_trajectory, environment) -> Optional[float]` (redukcja_w2_for_run
    ALBO e_beta_for_run). Kompletnosc siatki (23 genomy x N seedow)
    egzekwowana identycznie jak w _reduction_by_seed - IncompleteGridError,
    nie ciche pominiecie."""
    by_seed: Dict[int, List[Optional[float]]] = {}
    for rec in records:
        pe_trajectory = per_run_trajectory_fn(rec)
        effect = per_run_effect_fn(pe_trajectory, environment)
        by_seed.setdefault(rec["seed"], []).append(effect)

    columns: List[List[float]] = []
    for seed in sorted(by_seed):
        values = by_seed[seed]
        if len(values) != n_genomes_expected or any(v is None for v in values):
            raise IncompleteGridError(
                f"srodowisko={environment!r} seed={seed}: oczekiwano "
                f"{n_genomes_expected} kompletnych (nie-None) wartosci efektu, "
                f"otrzymano {sum(1 for v in values if v is not None)}/{len(values)} - "
                "siatka niekompletna, blok nie da sie policzyc (scenariusz A, "
                "B4C-2 (01) v2 - propaguje sie do INCONCLUSIVE, nie pominiecia)"
            )
        columns.append(values)
    return columns


def _group_a_components_by_seed(records: List[Dict[str, Any]], environment: str, n_genomes_expected: int,
                                 per_run_trajectory_fn) -> Tuple[List[List[float]], List[List[float]], List[List[float]]]:
    """Jak _effect_by_seed, ale dla Grupy A (K1-A/K4-A/K5-A) sledzi TRZY
    kolumny naraz (beta_raw, W_early_red, E_beta) z JEDNEGO przejscia przez
    dane per przebieg - beta_raw/W_early_red raportowane w artefakcie
    werdyktu (B4C-2 (15), zadanie 4), nie tylko znormalizowane E_beta."""
    by_seed: Dict[int, List[Optional[Tuple[float, float, float]]]] = {}
    for rec in records:
        pe_trajectory = per_run_trajectory_fn(rec)
        components = e_beta_components_for_run(pe_trajectory, environment)
        by_seed.setdefault(rec["seed"], []).append(components)

    beta_columns: List[List[float]] = []
    w_early_columns: List[List[float]] = []
    e_beta_columns: List[List[float]] = []
    for seed in sorted(by_seed):
        values = by_seed[seed]
        if len(values) != n_genomes_expected or any(v is None for v in values):
            n_ok = sum(1 for v in values if v is not None)
            raise IncompleteGridError(
                f"srodowisko={environment!r} seed={seed}: oczekiwano "
                f"{n_genomes_expected} kompletnych wartosci E_beta, otrzymano "
                f"{n_ok}/{len(values)} - siatka niekompletna, blok nie da sie "
                "policzyc (scenariusz A, B4C-2 (01) v2)"
            )
        beta_columns.append([v[0] for v in values])
        w_early_columns.append([v[1] for v in values])
        e_beta_columns.append([v[2] for v in values])
    return beta_columns, w_early_columns, e_beta_columns


def _median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def _margin_for_cell(cell_id: str) -> float:
    """equivalence_margin_c CZYTANY z artefaktu rodziny per komorka - NIGDY
    ze stalej wpisanej w evaluatorze (B4C-2 (15), zadanie 4, wymog wprost).
    Brak pola -> KeyError, nie domyslna wartosc."""
    family = json.loads(BH_FAMILY_PATH.read_text(encoding="utf-8"))
    cell = next(c for c in family["cells_active"] if c["id"] == cell_id)
    return cell["equivalence_margin_c"]


# B4C-2 (16), korekta CTO: None jest w tym repo JUZ ZAJETE (w2_endpoint:
# redukcja=None znaczy "przebieg nie pozwala policzyc" - "brak wyniku, nie
# wynik zerowy", patrz docstring compute_w2_reduction). Uzycie None TAKZE
# dla "jeszcze nie zaimplementowane" nalozyloby dwa rozne stany na jedna
# reprezentacje - ktos za pol roku przeczytalby None wedlug PIERWSZEGO
# znaczenia ("nie da sie policzyc dla tych danych"), co byloby FALSZYWA
# informacja o danych (te dwie komorki SA obliczalne - brakuje wylacznie
# korekty na poziomie calej rodziny). Jawny lancuch zamiast None: z samej
# WARTOSCI widac, ze to stan IMPLEMENTACJI, nie wlasciwosc danych.
PENDING_FULL_FAMILY_BH = "PENDING_FULL_FAMILY_BH"


def _equivalence_result(cell_id: str, effect_metric: str, block_values: List[float],
                         margin: float, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Pakuje wynik TOST w komplet pol wymaganych B4C-2 (15), zadanie 4.

    ZNANA LUKA, zgloszona zamiast domyslnie wypelniona: 'bh_adjusted_result'
    i ostateczne 'equivalence_supported' (po korekcie) wymagaja WSPOLNEJ
    korekty BH-FDR na WSZYSTKICH 11 komorkach naraz (STATS::benjamini_hochberg
    na wspolnej liscie p) - dzis zaimplementowane sa wylacznie K4-separacja
    (ODRZUCENIE_H0) i tych szesc (ROWNOWAZNOSC); Warunek A/B, K3a-warunek1,
    K6 NIE MAJA jeszcze funkcji-komorki w tym pliku, wiec pelna korekta
    rodziny m=11 nie jest dzis wykonalna. Oba pola zwracane jako
    PENDING_FULL_FAMILY_BH (NIE None - patrz komentarz przy stalej powyzej) -
    wypelnienie ich wartoscia liczbowa/boolowska byloby dokladnie tym
    bledem klasy, ktorego ten projekt unika (wartosc domyslna zamiast
    jawnego braku)."""
    tost = tost_wilcoxon(block_values, margin)
    result = {
        "cell_id": cell_id,
        "effect_metric": effect_metric,
        "block_values": block_values,
        "n": len(block_values),
        "observed_effect": _median(block_values),
        "equivalence_lower": -margin,
        "equivalence_upper": margin,
        "p_lower": tost["p_lower"],
        "p_upper": tost["p_upper"],
        "p_equivalence": tost["p_equivalence"],
        "computable": tost["computable"],
        "bh_adjusted_result": PENDING_FULL_FAMILY_BH,
        "equivalence_supported": PENDING_FULL_FAMILY_BH,
    }
    if extra:
        result.update(extra)
    return result


def k1_equivalence_cell(part: str, records: List[Dict[str, Any]], n_genomes_expected: int) -> Dict[str, Any]:
    """K1-A (part='A', effect=E_beta) / K1-B (part='B', effect=E_red) -
    surogat z przetasowaniem, WYLACZNIE noise_world (B4C-05 v4 pkt 1: K1
    definiowane tylko w kontekscie Primary). JEDNA permutacja K1 per blok
    seedowy, dzielona przez wszystkie 23 genomy tego seeda (B4C-1 (05),
    decyzja CTO) - wyliczona raz per seed z derive_k1_permutation, NIE
    per-genom."""
    if part not in ("A", "B"):
        raise ValueError(f"part musi byc 'A' lub 'B', otrzymano {part!r}")
    primary = EXPERIMENT_CONFIG["environments"]["primary"]
    ticks_total = EXPERIMENT_CONFIG["protocol"]["ticks_total"]

    permutation_by_seed = {
        rec["seed"]: derive_k1_permutation(rec["seed"], ticks_total) for rec in records
    }

    def trajectory_fn(rec):
        return _shuffled_pe_trajectory(rec, permutation_by_seed[rec["seed"]])

    k1_digests = {
        seed: {
            "k1_shuffle_seed": k1_shuffle_seed(seed),
            "algorithm": K1_SHUFFLE_ALGORITHM_ID,
            "permutation_digest": k1_permutation_digest(perm),
        }
        for seed, perm in permutation_by_seed.items()
    }

    if part == "A":
        beta_cols, w_early_cols, e_beta_cols = _group_a_components_by_seed(
            records, primary, n_genomes_expected, trajectory_fn)
        block_values = block_means(e_beta_cols)
        extra = {
            "k1_shuffle_by_seed": k1_digests,
            "beta_raw": block_means(beta_cols),
            "W_early_red": block_means(w_early_cols),
            "tick_span": _EXPECTED_TICK_SPAN,
        }
        return _equivalence_result("K1-A", "E_beta", block_values, _margin_for_cell("K1-A"), extra)

    columns = _effect_by_seed(records, primary, n_genomes_expected, trajectory_fn, e_red_for_run)
    block_values = block_means(columns)
    return _equivalence_result("K1-B", "redukcja_W2", block_values, _margin_for_cell("K1-B"), {"k1_shuffle_by_seed": k1_digests})


def k4_equivalence_cell(part: str, records: List[Dict[str, Any]], n_genomes_expected: int) -> Dict[str, Any]:
    """K4-A (part='A', effect=E_beta) / K4-B (part='B', effect=E_red) -
    brak efektu w czystym szumie, pure_noise_world. Zero transformacji
    trajektorii (surowa PE, jak Warunek A/B) - roznica wobec K1/K5 jest
    WYLACZNIE srodowisko/podloga."""
    if part not in ("A", "B"):
        raise ValueError(f"part musi byc 'A' lub 'B', otrzymano {part!r}")
    k4 = EXPERIMENT_CONFIG["environments"]["K4"]

    if part == "A":
        beta_cols, w_early_cols, e_beta_cols = _group_a_components_by_seed(
            records, k4, n_genomes_expected, _record_pe_trajectory)
        block_values = block_means(e_beta_cols)
        extra = {"beta_raw": block_means(beta_cols), "W_early_red": block_means(w_early_cols),
                 "tick_span": _EXPECTED_TICK_SPAN}
        return _equivalence_result("K4-A", "E_beta", block_values, _margin_for_cell("K4-A"), extra)

    columns = _effect_by_seed(records, k4, n_genomes_expected, _record_pe_trajectory, e_red_for_run)
    block_values = block_means(columns)
    return _equivalence_result("K4-B", "redukcja_W2", block_values, _margin_for_cell("K4-B"))


def k5_equivalence_cell(part: str, records: List[Dict[str, Any]], n_genomes_expected: int) -> Dict[str, Any]:
    """K5-A (part='A', effect=E_beta) / K5-B (part='B', effect=E_red) -
    ablacja surogatowa, WYLACZNIE noise_world (B4C-05 v4 pkt 1, jak K1)."""
    if part not in ("A", "B"):
        raise ValueError(f"part musi byc 'A' lub 'B', otrzymano {part!r}")
    primary = EXPERIMENT_CONFIG["environments"]["primary"]

    if part == "A":
        beta_cols, w_early_cols, e_beta_cols = _group_a_components_by_seed(
            records, primary, n_genomes_expected, _ablated_pe_trajectory)
        block_values = block_means(e_beta_cols)
        extra = {"beta_raw": block_means(beta_cols), "W_early_red": block_means(w_early_cols),
                 "tick_span": _EXPECTED_TICK_SPAN}
        return _equivalence_result("K5-A", "E_beta", block_values, _margin_for_cell("K5-A"), extra)

    columns = _effect_by_seed(records, primary, n_genomes_expected, _ablated_pe_trajectory, e_red_for_run)
    block_values = block_means(columns)
    return _equivalence_result("K5-B", "redukcja_W2", block_values, _margin_for_cell("K5-B"))


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
