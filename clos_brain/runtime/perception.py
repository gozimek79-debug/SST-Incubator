"""Perception – konwersja bodźca na stan wewnętrzny."""

from clos_brain.tissue import BrainTissue


def perceive(brain: BrainTissue, sensory_input: float) -> BrainTissue:
    """Przetwórz bodziec zmysłowy.

    Konwertuje sensory_input na wektor stanu i zapisuje w buforze.

    Args:
        brain: Aktualny stan Brain.
        sensory_input: Wartość bodźca (0.0 – 1.0).

    Returns:
        Zaktualizowany stan Brain.
    """
    # Normalizacja wejścia do zakresu [0, 1]
    clamped_input = max(0.0, min(1.0, sensory_input))

    # Zapis do bufora sensorycznego
    brain.sensory_buffer.append(clamped_input)

    # Ograniczenie bufora
    max_buffer = max(10, brain.prediction_depth * 3)
    if len(brain.sensory_buffer) > max_buffer:
        brain.sensory_buffer = brain.sensory_buffer[-max_buffer:]

    brain.last_input = clamped_input

    return brain
