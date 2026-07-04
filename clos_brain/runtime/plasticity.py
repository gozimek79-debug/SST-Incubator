"""Plasticity – mechanizm aktualizacji pamięci."""

from clos_brain.tissue import BrainTissue, MemoryRecord
from clos_brain.runtime.prediction import _hash_stimulus


def update_memory(brain: BrainTissue) -> BrainTissue:
    """Aktualizuj pamięć na podstawie błędu predykcji.

    - Jeśli error niski → wzmocnij ślad pamięciowy
    - Jeśli error wysoki → osłab / nadpisz
    - Usuń najstarsze rekordy przy przekroczeniu capacity

    Args:
        brain: Aktualny stan Brain.

    Returns:
        Zaktualizowany stan Brain.
    """
    if brain.last_input is None or brain.last_prediction is None:
        return brain

    error = abs(brain.last_prediction - brain.last_input)
    stimulus_hash = _hash_stimulus(brain.last_input)

    # Szukaj istniejącego rekordu dla tego bucketa
    existing_idx = None
    for i, record in enumerate(brain.memory):
        if record.stimulus_hash == stimulus_hash:
            existing_idx = i
            break

    if existing_idx is not None:
        # Aktualizuj istniejący rekord
        record = brain.memory[existing_idx]
        if error < 0.2:
            # Niski błąd – wzmocnij (zmniejsz error w rekordzie)
            record.error = record.error * 0.9
            record.prediction = record.prediction * 0.9 + brain.last_input * 0.1
        else:
            # Wysoki błąd – osłab (zwiększ error)
            record.error = record.error * 1.1 + error * brain.learning_rate
        record.timestamp_tick = brain.step_counter
    else:
        # Dodaj nowy rekord
        new_record = MemoryRecord(
            stimulus_hash=stimulus_hash,
            prediction=brain.last_input,
            error=error,
            timestamp_tick=brain.step_counter
        )
        brain.memory.append(new_record)

    # Ograniczenie pojemności pamięci
    while len(brain.memory) > brain.memory_capacity:
        # Usuń najstarszy rekord
        oldest = min(brain.memory, key=lambda r: r.timestamp_tick)
        brain.memory.remove(oldest)

    # Klamowanie error w rekordach
    for record in brain.memory:
        record.error = max(0.0, min(1.0, record.error))

    return brain


def apply_decay(brain: BrainTissue) -> BrainTissue:
    """Zastosuj zanikanie pamięci.

    Args:
        brain: Aktualny stan Brain.

    Returns:
        Zaktualizowany stan Brain.
    """
    # Zwiększ error we wszystkich rekordach (zanikanie)
    for record in brain.memory:
        record.error += brain.decay_rate

    # Usuń rekordy z bardzo wysokim errorem
    brain.memory = [r for r in brain.memory if r.error < 0.95]

    return brain
