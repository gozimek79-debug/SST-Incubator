"""Perception – konwersja bodzca na stan wewnetrzny.

v0.8.1: obsluga stimulus=-1.0 jako brak bodzca (faza ciszy).
W takim przypadku bufor sensoryczny NIE jest aktualizowany,
a Brain musi polegac na pamieci.
"""

from clos_brain.tissue import BrainTissue


def perceive(brain: BrainTissue, sensory_input: float) -> BrainTissue:
    """Przetworz bodziec zmyslowy.

    Args:
        brain: Aktualny stan Brain.
        sensory_input: Wartosc bodzca (0.0-1.0) lub -1.0 dla braku bodzca.

    Returns:
        Zaktualizowany stan Brain.
    """
    # -1.0 = brak bodzca (faza ciszy w Pattern Echo)
    if sensory_input < 0.0:
        brain.last_input = None  # Nie aktualizuj bufora
        return brain

    # Normalna obsluga bodzca
    clamped_input = max(0.0, min(1.0, sensory_input))
    brain.sensory_buffer.append(clamped_input)

    max_buffer = max(10, brain.prediction_depth * 3)
    if len(brain.sensory_buffer) > max_buffer:
        brain.sensory_buffer = brain.sensory_buffer[-max_buffer:]

    brain.last_input = clamped_input
    return brain
