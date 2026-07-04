"""World Runtime – deterministyczny generator bodźców.

I(t) = f(t, seed, scenario)

Brak stanu. Brak pamięci. Brak znajomości Brain.
"""

from typing import Union, List
from .scenarios import get_scenario


class WorldRuntime:
    """Generator bodźców wejściowych.

    Nie zna Brain. Nie zna Kernel. Tylko generuje I(t).
    """

    @staticmethod
    def step(tick: int, seed: int, scenario: str) -> float:
        """Wygeneruj bodziec dla danego ticka.

        Args:
            tick: Numer ticka z Kernela.
            seed: Ziarno losowości.
            scenario: Nazwa scenariusza.

        Returns:
            Wartość bodźca w [0, 1].
        """
        scenario_fn = get_scenario(scenario)
        return scenario_fn(tick, seed)

    @staticmethod
    def get_available_scenarios() -> List[str]:
        """Zwraca listę dostępnych scenariuszy."""
        from .scenarios import list_scenarios
        return list_scenarios()
