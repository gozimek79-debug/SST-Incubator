"""Seed Manager – deterministyczna powtarzalność eksperymentów.

Jeden globalny seed. Cały system korzysta wyłącznie z niego.
"""

import random
from typing import Optional


class SeedManager:
    """Zarządca ziarna losowości.

    Każdy eksperyment musi być odtwarzalny.
    """

    def __init__(self, seed: Optional[int] = None):
        self._initial_seed: Optional[int] = seed
        self._current_seed: Optional[int] = seed
        if seed is not None:
            random.seed(seed)

    def set_seed(self, seed: int) -> None:
        """Ustaw nowe ziarno.

        Args:
            seed: Nowa wartość ziarna.
        """
        self._initial_seed = seed
        self._current_seed = seed
        random.seed(seed)

    def get_seed(self) -> Optional[int]:
        """Pobierz aktualne ziarno.

        Returns:
            Aktualna wartość ziarna.
        """
        return self._current_seed

    def generate(self) -> int:
        """Wygeneruj nowe ziarno.

        Returns:
            Nowe losowe ziarno.
        """
        import secrets
        new_seed = secrets.randbits(32)
        self.set_seed(new_seed)
        return new_seed

    def reset(self) -> None:
        """Zresetuj do początkowego ziarna."""
        if self._initial_seed is not None:
            self.set_seed(self._initial_seed)
        else:
            self._current_seed = None

    def random_float(self, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Wygeneruj losową liczbę z zakresu.

        Args:
            min_val: Dolna granica.
            max_val: Górna granica.

        Returns:
            Losowa liczba zmiennoprzecinkowa.
        """
        return random.uniform(min_val, max_val)

    def random_int(self, min_val: int, max_val: int) -> int:
        """Wygeneruj losową liczbę całkowitą.

        Args:
            min_val: Dolna granica (włącznie).
            max_val: Górna granica (włącznie).

        Returns:
            Losowa liczba całkowita.
        """
        return random.randint(min_val, max_val)
