"""Precision – obliczanie błędu predykcji i precyzji (metapoznanie v0.1)."""

import statistics
from clos_brain.tissue import BrainTissue


def compute_error(brain: BrainTissue) -> BrainTissue:
    """Oblicz błąd predykcji.

    error = |prediction - input|

    Args:
        brain: Aktualny stan Brain.

    Returns:
        Zaktualizowany stan Brain.
    """
    if brain.last_prediction is None or brain.last_input is None:
        return brain

    error = abs(brain.last_prediction - brain.last_input)

    # Zapis do bufora błędów
    brain.prediction_error_buffer.append(error)

    # Ograniczenie bufora
    if len(brain.prediction_error_buffer) > 100:
        brain.prediction_error_buffer = brain.prediction_error_buffer[-100:]

    return brain


def compute_precision(brain: BrainTissue) -> BrainTissue:
    """Oblicz precyzję (metapoznanie).

    precision = 1 / (1 + variance(error_last_n))

    Niski szum → wysoka precyzja.
    Wysoki szum → niska precyzja.

    Args:
        brain: Aktualny stan Brain.

    Returns:
        Zaktualizowany stan Brain.
    """
    errors = brain.prediction_error_buffer

    if len(errors) < 2:
        brain.precision = 0.5  # Neutralna przy braku danych
        return brain

    # Oblicz wariancję
    variance = statistics.variance(errors) if len(errors) >= 2 else 0.0

    # Formuła precyzji
    brain.precision = 1.0 / (1.0 + variance * brain.meta_cognition_sensitivity)

    # Klamping
    brain.precision = max(0.01, min(1.0, brain.precision))

    # Historia
    brain.precision_history.append(brain.precision)
    if len(brain.precision_history) > 100:
        brain.precision_history = brain.precision_history[-100:]

    return brain
