"""CLI Runner – z obsługą --genome."""

import sys, os
sys.path.insert(0, os.getcwd())

def run_school():
    from clos_curriculum.runner import run_default_school
    run_default_school()

def run_matrix(manifest_path: str):
    from clos_studio.execution.matrix_runner import MatrixRunner
    runner = MatrixRunner()
    try: runner.run(manifest_path)
    finally: runner.close()

def run_experiment(manifest_path: str):
    from clos_studio.cli.commands import run_experiment_from_manifest
    run_experiment_from_manifest(manifest_path)

def run_demo(seed: int, ticks: int, stream: bool = False, genome: str = "default"):
    import run_demo
    run_demo.main(seed=seed, ticks=ticks, stream=stream, genome_preset=genome)

def run_compare(seed: int, ticks: int):
    import run_compare
    run_compare.main(seed=seed, ticks=ticks)

def run_benchmark(seed: int, ticks: int):
    import run_benchmark
    run_benchmark.main(seed=seed, ticks=ticks)

def run_dashboard(seed: int, ticks: int):
    import run_dashboard
    run_dashboard.main(seed=seed, ticks=ticks)
