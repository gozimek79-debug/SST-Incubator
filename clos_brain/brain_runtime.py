"""BrainRuntime – czysta transformacja stanu.

S(t+1) = f(S(t), sensory_input, seed, tick)
"""

import random
from typing import Optional
from clos_brain.tissue import BrainTissue
from clos_brain.runtime.perception import perceive
from clos_brain.runtime.prediction import predict
from clos_brain.runtime.precision import compute_error, compute_precision
from clos_brain.runtime.homeostasis import regulate
from clos_brain.runtime.plasticity import update_memory, apply_decay
from clos_brain.runtime.action import act


class BrainRuntime:
    """Deterministyczny silnik transformacji stanu poznawczego.

    Nie trzyma stanu globalnego. Każda operacja to czysta funkcja.
    """

    @staticmethod
    def step(
        brain: BrainTissue,
        sensory_input: float,
        seed: int,
        tick: int
    ) -> BrainTissue:
        """Wykonaj jeden krok przetwarzania.

        Args:
            brain: Aktualny stan Brain.
            sensory_input: Bodziec wejściowy (0.0 – 1.0).
            seed: Ziarno losowości (dla determinizmu).
            tick: Numer ticka z Kernela.

        Returns:
            Nowy stan Brain.
        """
        # Ustaw ziarno dla determinizmu
        random.seed(seed + tick)

        # Krok 1: Percepcja
        brain = perceive(brain, sensory_input)

        # Krok 2: Predykcja
        brain = predict(brain)

        # Krok 3: Obliczenie błędu
        brain = compute_error(brain)

        # Krok 4: Precyzja (metapoznanie)
        brain = compute_precision(brain)

        # Krok 5: Homeostaza
        brain = regulate(brain)

        # Krok 6: Plastyczność – aktualizacja pamięci
        brain = update_memory(brain)

        # Krok 7: Zanikanie pamięci (co MID tick)
        if tick % 10 == 0:
            brain = apply_decay(brain)

        # Aktualizacja liczników
        brain.age += 1
        brain.step_counter += 1

        return brain

    @staticmethod
    def get_action(brain: BrainTissue) -> float:
        """Pobierz akcję z Brain.

        Args:
            brain: Aktualny stan Brain.

        Returns:
            Wartość akcji.
        """
        return act(brain)
