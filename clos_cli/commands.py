"""CLI Command Router."""

from .runner import run_demo, run_compare, run_benchmark, run_dashboard, run_experiment, run_matrix


def route_command(command: str, seed: int, ticks: int, stream: bool = False, manifest: str = ""):
    if command == "run":
        run_experiment(manifest)
    elif command == "run-matrix":
        run_matrix(manifest)
    elif command == "demo":
        run_demo(seed, ticks, stream)
    elif command == "compare":
        run_compare(seed, ticks)
    elif command == "benchmark":
        run_benchmark(seed, ticks)
    elif command == "dashboard":
        run_dashboard(seed, ticks)
    else:
        raise ValueError(f"Nieznana komenda: {command}")
