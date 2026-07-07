"""CLI Command Router v0.8."""

from .runner import run_demo, run_compare, run_benchmark, run_dashboard, run_experiment, run_matrix, run_school, run_academy

def route_command(command: str, seed: int, ticks: int, stream: bool = False, manifest: str = "", genome: str = "default", scenario: str = "shock_world", telemetry: int = 0):
    if command == "run": run_experiment(manifest)
    elif command == "run-matrix": run_matrix(manifest)
    elif command == "school": run_school()
    elif command == "academy": run_academy()
    elif command == "demo": run_demo(seed, ticks, stream, genome, scenario, telemetry)
    elif command == "compare": run_compare(seed, ticks)
    elif command == "benchmark": run_benchmark(seed, ticks)
    elif command == "dashboard": run_dashboard(seed, ticks)
    else: raise ValueError(f"Nieznana komenda: {command}")
