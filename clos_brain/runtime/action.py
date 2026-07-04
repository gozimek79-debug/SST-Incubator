"""Action – minimalna warstwa wyjściowa (echo input, v0.1)."""

from clos_brain.tissue import BrainTissue


def act(brain: BrainTissue) -> float:
    """Wygeneruj akcję na podstawie stanu.

    v0.1: echo input – zwraca ostatni bodziec.

    Args:
        brain: Aktualny stan Brain.

    Returns:
        Wartość akcji (0.0 – 1.0).
    """
    if brain.last_input is not None:
        return brain.last_input
    return 0.0
