"""BrainRuntime – czysta transformacja stanu.

S(t+1) = f(S(t), sensory_input, seed, tick)
"""

import random
from enum import Enum
from typing import FrozenSet, Iterable, Optional
from clos_brain.tissue import BrainTissue
from clos_brain.runtime.perception import perceive
from clos_brain.runtime.prediction import predict
from clos_brain.runtime.precision import compute_error, compute_precision
from clos_brain.runtime.homeostasis import regulate
from clos_brain.runtime.plasticity import update_memory, apply_decay
from clos_brain.runtime.action import act


class PipelineStep(str, Enum):
    """Nazwane kroki pipeline'u step() - patrz docs/spec_partial_step.md."""

    PERCEIVE = "perceive"
    PREDICT = "predict"
    COMPUTE_ERROR = "compute_error"
    COMPUTE_PRECISION = "compute_precision"
    REGULATE = "regulate"
    UPDATE_MEMORY = "update_memory"
    APPLY_DECAY = "apply_decay"


# Jedyny krok certyfikowany jako bezpieczny do pominięcia (SPRINT_v0.9.md P2,
# docs/spec_partial_step.md §3): predict()/compute_error() już tolerują
# last_input=None bez zmian w Core. Pozostałe kroki wymagałyby osobnej,
# pisemnej analizy bezpieczeństwa przed dopisaniem tutaj.
_CERTIFIED_SKIPPABLE: FrozenSet[PipelineStep] = frozenset({PipelineStep.PERCEIVE})


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
    def partial_step(
        brain: BrainTissue,
        sensory_input: Optional[float],
        seed: int,
        tick: int,
        skip: Iterable[PipelineStep] = (),
    ) -> BrainTissue:
        """Wykonaj jeden krok przetwarzania, opcjonalnie pomijając kroki.

        Addytywne rozszerzenie step() (SPRINT_v0.9.md P2) - komponuje TE
        SAME zamrożone prymitywy w TEJ SAMEJ kolejności co step(); zero
        zmian w perceive/predict/compute_error/compute_precision/regulate/
        update_memory/apply_decay. `partial_step(skip=())` == `step()`.

        Args:
            brain: Aktualny stan Brain.
            sensory_input: Bodziec wejściowy, albo None gdy PipelineStep.PERCEIVE
                jest w `skip` (brak bodźca zewnętrznego w tym ticku).
            seed: Ziarno losowości (dla determinizmu).
            tick: Numer ticka z Kernela.
            skip: Kroki do pominięcia. Tylko PipelineStep.PERCEIVE jest
                certyfikowane jako bezpieczne — patrz docs/spec_partial_step.md.

        Returns:
            Nowy stan Brain.

        Raises:
            NotImplementedError: `skip` zawiera krok inny niż PERCEIVE
                (świadomie niecertyfikowany, nie "zła wartość").
        """
        skip_set = frozenset(skip)
        uncertified = skip_set - _CERTIFIED_SKIPPABLE
        if uncertified:
            names = sorted(s.value for s in uncertified)
            raise NotImplementedError(
                f"partial_step: pominiecie kroku(ow) {names} nie jest certyfikowane "
                "jako bezpieczne (patrz docs/spec_partial_step.md, §3). Obecnie "
                "dozwolone wyłącznie: PipelineStep.PERCEIVE."
            )

        # Ziarno liczone identycznie niezależnie od skip (ta sama pozycja co w step()).
        random.seed(seed + tick)

        if PipelineStep.PERCEIVE in skip_set:
            # Brak bodźca zewnętrznego w tym ticku - ten sam efekt co
            # dotychczasowy wzorzec clos_academy/echo_runtime.py (ustawienie
            # last_input=None przed predict()), tylko przez sankcjonowane API.
            brain.last_input = None
        else:
            brain = perceive(brain, sensory_input)

        brain = predict(brain)
        brain = compute_error(brain)
        brain = compute_precision(brain)
        brain = regulate(brain)
        brain = update_memory(brain)
        if tick % 10 == 0:
            brain = apply_decay(brain)

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
