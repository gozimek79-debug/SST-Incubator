"""Prediction – generowanie przewidywań na podstawie pamięci."""

import hashlib
from clos_brain.tissue import BrainTissue


def predict(brain: BrainTissue) -> BrainTissue:
    """Wygeneruj predykcję na podstawie pamięci.

    Bardzo prosta logika: uśrednianie zapamiętanych predykcji
    ważonych przez podobieństwo do aktualnego wejścia.

    Args:
        brain: Aktualny stan Brain.

    Returns:
        Zaktualizowany stan Brain z ustawionym last_prediction.
    """
    if not brain.sensory_buffer:
        brain.last_prediction = 0.5  # Neutralna predykcja
        return brain

    current_input = brain.sensory_buffer[-1]
    input_hash = _hash_stimulus(current_input)

    # Szukaj podobnych rekordów w pamięci
    matching_records = [
        r for r in brain.memory
        if abs(r.stimulus_hash - input_hash) < brain.attention_threshold * 1000
    ]

    if matching_records:
        # Średnia ważona po błędzie (im mniejszy błąd, tym większa waga)
        total_weight = 0.0
        weighted_sum = 0.0

        for record in matching_records[-brain.prediction_depth:]:
            weight = 1.0 / (1.0 + record.error)
            weighted_sum += record.prediction * weight
            total_weight += weight

        if total_weight > 0:
            brain.last_prediction = weighted_sum / total_weight
        else:
            brain.last_prediction = 0.5
    else:
        # Brak pasujących rekordów – neutralna predykcja
        if brain.sensory_buffer:
            # Użyj średniej z ostatnich wejść jako prostej heurystyki
            recent = brain.sensory_buffer[-brain.prediction_depth:]
            brain.last_prediction = sum(recent) / len(recent)
        else:
            brain.last_prediction = 0.5

    # Klamping do [0, 1]
    brain.last_prediction = max(0.0, min(1.0, brain.last_prediction))

    return brain


def _hash_stimulus(value: float, buckets: int = 100) -> int:
    """Hashuj wartość bodźca do dyskretnego bucketa.

    Args:
        value: Wartość bodźca.
        buckets: Liczba bucketów.

    Returns:
        Wartość całkowita 0 – buckets.
    """
    return int(max(0.0, min(1.0, value)) * buckets)
