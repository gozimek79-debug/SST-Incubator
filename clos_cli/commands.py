"""CLI Command Router – bez logiki, tylko mapowanie."""

from .runner import run_demo, run_compare, run_benchmark, run_dashboard


def route_command(command: str, seed: int, ticks: int, stream: bool = False):
    """Przekierowuje komendę do odpowiedniej funkcji runnera."""
    if command == "demo":
        run_demo(seed, ticks, stream)
    elif command == "compare":
        run_compare(seed, ticks)
    elif command == "benchmark":
        run_benchmark(seed, ticks)
    elif command == "dashboard":
        run_dashboard(seed, ticks)
    else:
        raise ValueError(f"Nieznana komenda: {command}")
