"""Regression Harness – Cognitive Assertions.

Wykrywa regresję poznawczą i zatrzymuje build.
"""

from typing import Dict, List, Any, Tuple


class CognitiveAssertion:
    """Pojedyncza asercja poznawcza."""

    def __init__(
        self,
        name: str,
        description: str,
        metric: str,
        expected_min: float = None,
        expected_max: float = None,
        tolerance: float = 0.1,
        baseline_version: str = "0.1"
    ):
        self.name = name
        self.description = description
        self.metric = metric
        self.expected_min = expected_min
        self.expected_max = expected_max
        self.tolerance = tolerance
        self.baseline_version = baseline_version

    def check(self, stats: Dict[str, Any]) -> Tuple[bool, str]:
        """Sprawdza asercję na podstawie statystyk.

        Args:
            stats: Wynik validate_benchmark.

        Returns:
            (passed, message)
        """
        statistics = stats.get("statistics", {})
        if self.metric not in statistics:
            return False, f"Metric '{self.metric}' not found in statistics"

        mean_val = statistics[self.metric]["mean"]

        messages = []

        if self.expected_min is not None:
            threshold = self.expected_min - self.tolerance
            if mean_val < threshold:
                return False, (
                    f"[FAIL] {self.name}: {self.metric}={mean_val:.4f} "
                    f"below minimum {self.expected_min} (tolerance={self.tolerance})"
                )
            messages.append(f"min OK ({mean_val:.4f} >= {threshold:.4f})")

        if self.expected_max is not None:
            threshold = self.expected_max + self.tolerance
            if mean_val > threshold:
                return False, (
                    f"[FAIL] {self.name}: {self.metric}={mean_val:.4f} "
                    f"above maximum {self.expected_max} (tolerance={self.tolerance})"
                )
            messages.append(f"max OK ({mean_val:.4f} <= {threshold:.4f})")

        return True, f"[PASS] {self.name}: {'; '.join(messages)}"


class RegressionHarness:
    """Zestaw asercji poznawczych do testów regresji."""

    def __init__(self):
        self.assertions: List[CognitiveAssertion] = []

    def add_assertion(self, assertion: CognitiveAssertion):
        """Dodaj asercję."""
        self.assertions.append(assertion)

    def run_all(self, stats: Dict[str, Any]) -> Tuple[bool, str]:
        """Uruchom wszystkie asercje.

        Args:
            stats: Wynik validate_benchmark.

        Returns:
            (all_passed, report)
        """
        results = []
        all_passed = True

        for assertion in self.assertions:
            passed, message = assertion.check(stats)
            if not passed:
                all_passed = False
            results.append(message)

        report = "REGRESSION HARNESS RESULTS\n" + "=" * 50 + "\n"
        report += "\n".join(results)
        report += "\n" + "=" * 50 + "\n"
        report += f"OVERALL: {'PASS' if all_passed else 'FAIL'}\n"

        return all_passed, report


def create_default_harness() -> RegressionHarness:
    """Tworzy domyślny zestaw asercji dla v0.1."""
    harness = RegressionHarness()

    harness.add_assertion(CognitiveAssertion(
        name="StabilityAboveMinimum",
        description="Stability Index powinien być powyżej minimum",
        metric="stability_index",
        expected_min=0.5,
        tolerance=0.5,
    ))

    harness.add_assertion(CognitiveAssertion(
        name="MSEBelowMaximum",
        description="MSE powinien być poniżej maksimum",
        metric="mse",
        expected_max=0.5,
        tolerance=0.2,
    ))

    harness.add_assertion(CognitiveAssertion(
        name="EntropyVolatilityBelowMaximum",
        description="Entropy Volatility powinna być poniżej progu",
        metric="entropy_volatility",
        expected_max=0.3,
        tolerance=0.1,
    ))

    return harness
