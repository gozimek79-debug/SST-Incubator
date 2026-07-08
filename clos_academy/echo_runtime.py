"""Echo Runtime — warstwa Academy dla fazy ciszy (v0.8.2, opcja B).

Cel: obsłużyć fazę ciszy lekcji Pattern Echo BEZ modyfikacji Brain Runtime.
Zamiast wprowadzać do Core sentinel `-1.0`/`None` (co ruszało zamrożony rdzeń),
eksperyment sam decyduje, że w danym ticku NIE ma bodźca zewnętrznego, i
uruchamia ISTNIEJĄCE, zamrożone prymitywy Core — pomijając jedynie `perceive`.

Dzięki temu:
- bufor sensoryczny nie jest aktualizowany (Brain musi polegać na pamięci),
- `predict()` (zamrożony) liczy predykcję z bufora/pamięci,
- `compute_error()` (zamrożony) sam pomija tick, bo last_input=None,
- Brain Runtime pozostaje bajtowo identyczny z baseline (Core frozen).

To NIE jest kod poznawczy — to orkiestracja eksperymentu warstwy badawczej.
"""

import random

from clos_brain.tissue import BrainTissue
# Wyłącznie ZAMROŻONE prymitywy Core — importowane, nie modyfikowane:
from clos_brain.runtime.prediction import predict
from clos_brain.runtime.precision import compute_error, compute_precision
from clos_brain.runtime.homeostasis import regulate
from clos_brain.runtime.plasticity import update_memory, apply_decay


def silent_step(brain: BrainTissue, seed: int, tick: int) -> BrainTissue:
    """Jeden krok fazy ciszy — pipeline Core BEZ percepcji.

    Odwzorowuje efektywne zachowanie z v0.8.1 (perceive był no-opem w ciszy),
    ale nie dotyka Brain Runtime. Kolejność kroków identyczna jak w
    BrainRuntime.step, pominięty jest wyłącznie krok 1 (perceive).
    """
    random.seed(seed + tick)

    # Eksperyment deklaruje brak bodźca zewnętrznego w tym ticku.
    # (Ustawienie stanu wejścia to rola eksperymentu, nie kod poznawczy Core.)
    brain.last_input = None

    brain = predict(brain)             # zamrożony: predykcja z bufora/pamięci
    brain = compute_error(brain)       # zamrożony: pomija tick (last_input=None)
    brain = compute_precision(brain)   # zamrożony
    brain = regulate(brain)            # zamrożony: homeostaza
    brain = update_memory(brain)       # zamrożony: plastyczność
    if tick % 10 == 0:
        brain = apply_decay(brain)     # zamrożony: zanikanie pamięci

    brain.age += 1
    brain.step_counter += 1
    return brain
