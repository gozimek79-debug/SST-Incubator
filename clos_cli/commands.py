"""CLI Command Router – bez logiki, tylko mapowanie."""

from .runner import run_demo, run_compare, run_benchmark, run_dashboard


def route_command(command: str, seed: int, ticks: int):
    """Przekierowuje komendę do odpowiedniej funkcji runnera.

    Args:
        command: Nazwa komendy (demo, compare, benchmark, dashboard).
        seed: Ziarno losowości.
        ticks: Liczba ticków.
    """
    if command == "demo":
        run_demo(seed, ticks)
    elif command == "compare":
        run_compare(seed, ticks)
    elif command == "benchmark":
        run_benchmark(seed, ticks)
    elif command == "dashboard":
        run_dashboard(seed, ticks)
    else:
        raise ValueError(f"Nieznana komenda: {command}")
