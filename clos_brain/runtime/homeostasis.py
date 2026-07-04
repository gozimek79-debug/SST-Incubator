"""Homeostasis – regulacja energii i entropii."""

from clos_brain.tissue import BrainTissue


def regulate(brain: BrainTissue) -> BrainTissue:
    """Reguluj homeostazę.

    - energy -= constant_decay
    - entropy += error * factor
    - jeśli entropy > threshold → stress state (energy dodatkowo spada)

    Args:
        brain: Aktualny stan Brain.

    Returns:
        Zaktualizowany stan Brain.
    """
    # Stały spadek energii (koszt życia)
    energy_decay = 0.001  # Stała utrata na tick
    brain.energy -= energy_decay

    # Wzrost entropii proporcjonalny do błędu
    if brain.prediction_error_buffer:
        recent_error = brain.prediction_error_buffer[-1]
        entropy_increase = recent_error * brain.decay_rate * 10.0
        brain.entropy += entropy_increase

    # Stress state – jeśli entropy powyżej progu
    stress_threshold = 0.7
    if brain.entropy > stress_threshold:
        brain.energy -= 0.002  # Dodatkowy koszt stresu

    # Regulacja – dążenie do homeostazy
    if brain.entropy > brain.homeostasis_target:
        # Entropia powyżej celu – powolny spadek (regulacja)
        brain.entropy -= 0.005 * brain.plasticity
    elif brain.entropy < brain.homeostasis_target * 0.5:
        # Entropia zbyt niska – lekkie podbicie
        brain.entropy += 0.001

    # Klamping wartości
    brain.energy = max(0.0, min(1.0, brain.energy))
    brain.entropy = max(0.0, min(1.0, brain.entropy))

    # Historia
    brain.entropy_history.append(brain.entropy)
    brain.energy_history.append(brain.energy)
    if len(brain.entropy_history) > 100:
        brain.entropy_history = brain.entropy_history[-100:]
    if len(brain.energy_history) > 100:
        brain.energy_history = brain.energy_history[-100:]

    return brain
