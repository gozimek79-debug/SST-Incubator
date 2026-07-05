"""CLI Runner – pasywny przekazywacz do skryptów laboratoryjnych."""

import sys
import os

sys.path.insert(0, os.getcwd())


def run_demo(seed: int, ticks: int, stream: bool = False):
    """Uruchamia demo eksperymentu."""
    import run_demo
    run_demo.main(seed=seed, ticks=ticks, stream=stream)


def run_compare(seed: int, ticks: int):
    """Uruchamia porównanie scenariuszy."""
    import run_compare
    run_compare.main(seed=seed, ticks=ticks)


def run_benchmark(seed: int, ticks: int):
    """Uruchamia pełny benchmark."""
    import run_benchmark
    run_benchmark.main(seed=seed, ticks=ticks)


def run_dashboard(seed: int, ticks: int):
    """Uruchamia dashboard."""
    import run_dashboard
    run_dashboard.main(seed=seed, ticks=ticks)
