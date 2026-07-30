"""PC-001 Aneks 2 (2026-07-28): K7 - pomiar RAPORTOWANY, NIE warunek decyzyjny
(regula pozostaje 9-warunkowa, patrz publications/preregistration_PC_001_ANEKS_2_
2026-07-28.md). Osobny modul (nie clos_curriculum/laboratory/statistics.py) -
to NIE jest test statystyczny, tylko heurystyka diagnostyczna nad zapisanymi
trajektoriami prediction/input (Snapshot, patrz clos_kernel/snapshot_engine.py).

CO MIERZY: odsetek tickow, w ktorych clos_brain/runtime/prediction.py::predict()
najprawdopodobniej uzyl galezi awaryjnej (brak pasujacych rekordow w pamieci ->
predykcja = srednia krocząca ostatnich prediction_depth zapisanych wejsc) - przez
porownanie zapisanej prediction(t) z niezaleznie przeliczona srednia z ostatnich
prediction_depth wartosci input(t).

TRZY OGRANICZENIA (Aneks 2, zapisane PRZED wykonaniem, nie po zobaczeniu wynikow):
1. Wymaga prediction_depth PER GENOM - Snapshot go nie niesie (musi byc podany
   przez wywolujacego, ktory ma dostep do kontekstu genomu). Gdy None -> K7
   NIEOBLICZALNY dla tego przebiegu, raportowany jako taki, nie pomijany.
2. Wymaga tolerancji zmiennoprzecinkowej (dopasowanie to nie dokladna rownosc) -
   1e-9 wzgledna (math.isclose(rel_tol=...)), wartosc arbitralna zapisana z gory.
3. Jest HEURYSTYKA, nie pewnoscia - gałąź pamięciowa może przypadkowo dać
   wartosc rowna sredniej kroczacej. K7 daje OSZACOWANIE DOLNE odsetka galezi
   awaryjnej, nigdy liczbe dokladna.

Dla obecnej populacji PC-001: prediction_depth NIGDY nie jest nadpisywany przez
clos_curriculum/laboratory/population.py (LHS) ani przez tissue_kwargs w
clos_academy/lesson_L1_1.py/lesson_L1_2.py (zweryfikowane grepem) - wiec KAZDY
z 23 genomow uzywa tego samego defaultu z dataclass clos_brain/tissue.py
(BrainTissue.prediction_depth=3). default_prediction_depth() ponizej czyta ta
wartosc PRZEZ introspekcje dataclass (jedno zrodlo prawdy), nie duplikuje "3"
jako osobna stala.
"""

import math
from dataclasses import fields
from typing import Any, Dict, List, Optional


def default_prediction_depth() -> int:
    """Domyslna wartosc prediction_depth z dataclass BrainTissue - jedno
    zrodlo prawdy (nie duplikuje liczby osobno tutaj). Uzywana dla kazdego z
    23 genomow obecnej populacji PC-001 (zweryfikowane: LHS w population.py i
    tissue_kwargs w lesson_L1_1.py/lesson_L1_2.py nigdy tego pola nie
    nadpisuja)."""
    from clos_brain.tissue import BrainTissue
    for f in fields(BrainTissue):
        if f.name == "prediction_depth":
            return f.default
    raise AttributeError("BrainTissue nie ma juz pola prediction_depth - K7 wymaga aktualizacji")


def k7_fallback_branch_fraction(
    predictions: List[Optional[float]],
    inputs: List[Optional[float]],
    prediction_depth: Optional[int],
    tolerance: float = 1e-9,
) -> Dict[str, Any]:
    """Szacowany odsetek tickow w galezi awaryjnej predict().

    Args:
        predictions: trajektoria Snapshot.prediction (kolejne ticki, ten sam
            przebieg), None gdy brak (np. faza ciszy L1.1).
        inputs: trajektoria Snapshot.input, ten sam przebieg, ta sama dlugosc.
        prediction_depth: parametr genomu dla TEGO przebiegu, albo None gdy
            wywolujacy nie mogl go ustalic (K7 wtedy NIEOBLICZALNY - ograniczenie 1).
        tolerance: tolerancja wzgledna dopasowania (ograniczenie 2, domyslnie 1e-9).

    Zwraca:
        fraction: szacowany odsetek (oszacowanie DOLNE, ograniczenie 3), albo
            None gdy computable=False.
        n_evaluable: liczba tickow z pelnym oknem historii (bez None w oknie
            prediction_depth ostatnich inputow) - ticki bez pelnego okna
            (np. faza ciszy L1.1, poczatek przebiegu) sa pomijane W LICZNIKU
            I MIANOWNIKU, nie liczone jako "nie-galaz-awaryjna".
        n_total: dlugosc przekazanej trajektorii (dla przejrzystosci, ile
            tickow NIE bylo evaluable).
    """
    if prediction_depth is None:
        return {"fraction": None, "computable": False,
                "reason": "prediction_depth niedostepny dla tego genomu (ograniczenie 1, Aneks 2)"}
    if prediction_depth < 1:
        return {"fraction": None, "computable": False,
                "reason": f"prediction_depth={prediction_depth} < 1, niepoprawne"}

    n_total = len(predictions)
    if n_total != len(inputs):
        raise ValueError("predictions i inputs musza miec ta sama dlugosc (ten sam ciag tickow)")

    n_evaluable = 0
    n_fallback = 0
    for t in range(n_total):
        pred_t = predictions[t]
        if pred_t is None:
            continue
        window_start = t - prediction_depth + 1
        if window_start < 0:
            continue
        window = inputs[window_start:t + 1]
        if any(v is None for v in window):
            continue
        n_evaluable += 1
        candidate = sum(window) / len(window)
        if math.isclose(pred_t, candidate, rel_tol=tolerance):
            n_fallback += 1

    if n_evaluable == 0:
        return {"fraction": None, "computable": False,
                "reason": "zero tickow z pelnym oknem historii (przebieg za krotki albo brak danych)",
                "n_total": n_total}

    return {
        "fraction": round(n_fallback / n_evaluable, 6),
        "computable": True,
        "n_fallback": n_fallback,
        "n_evaluable": n_evaluable,
        "n_total": n_total,
        "tolerance": tolerance,
        "prediction_depth": prediction_depth,
    }


def interpret_k7_fraction(fraction: Optional[float]) -> str:
    """Progi interpretacyjne z Aneksu 2 (konwencja przyjeta z gory, jak prog
    20% w Primary Endpoint) - NIE wplywa na regule decyzyjna, wylacznie opis."""
    if fraction is None:
        return "nieobliczalny"
    if fraction < 0.20:
        return "K6 wiarygodny - predykcja pochodzi glownie z modelu pamieciowego"
    if fraction <= 0.50:
        return "strefa niejednoznaczna - wymaga jawnego omowienia w interpretacji"
    return "K6 potencjalnie mylacy - predykcja moze byc w znacznej czesci srednia kroczaca"
