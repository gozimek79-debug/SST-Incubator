"""Prediction – generowanie przewidywan na podstawie pamieci.

v0.8.1: obsluga last_input=None (faza ciszy). Gdy brak biezacego
bodzca, Brain przewiduje na podstawie ostatnich wpisow w buforze.
"""

import hashlib
from clos_brain.tissue import BrainTissue


def predict(brain: BrainTissue) -> BrainTissue:
    """Wygeneruj predykcje na podstawie pamieci."""
    
    # Gdy nie ma biezacego wejscia (faza ciszy) – przewiduj z bufora
    if brain.last_input is None:
        if brain.sensory_buffer:
            recent = brain.sensory_buffer[-brain.prediction_depth:]
            brain.last_prediction = sum(recent) / len(recent)
        else:
            brain.last_prediction = 0.5
        brain.last_prediction = max(0.0, min(1.0, brain.last_prediction))
        return brain

    current_input = brain.sensory_buffer[-1] if brain.sensory_buffer else brain.last_input
    input_hash = _hash_stimulus(current_input)

    matching_records = [
        r for r in brain.memory
        if abs(r.stimulus_hash - input_hash) < brain.attention_threshold * 1000
    ]

    if matching_records:
        total_weight = 0.0
        weighted_sum = 0.0
        for record in matching_records[-brain.prediction_depth:]:
            weight = 1.0 / (1.0 + record.error)
            weighted_sum += record.prediction * weight
            total_weight += weight
        brain.last_prediction = weighted_sum / total_weight if total_weight > 0 else 0.5
    else:
        if brain.sensory_buffer:
            recent = brain.sensory_buffer[-brain.prediction_depth:]
            brain.last_prediction = sum(recent) / len(recent)
        else:
            brain.last_prediction = 0.5

    brain.last_prediction = max(0.0, min(1.0, brain.last_prediction))
    return brain


def _hash_stimulus(value: float, buckets: int = 100) -> int:
    return int(max(0.0, min(1.0, value)) * buckets)
