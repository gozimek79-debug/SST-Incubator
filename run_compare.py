"""CLOS v0.1 – Porównanie scenariuszy."""

from genome.engine import GenomeEngine
from birth.engine import BirthEngine
from clos_kernel.kernel import Kernel
from clos_world.world_runtime import WorldRuntime
from clos_brain.brain_runtime import BrainRuntime
from clos_brain.tissue import BrainTissue
from clos_scientist.experiment import run_experiment
from clos_scientist.registry import ExperimentRegistry
from clos_kernel.event_bus import EventBus
from clos_scientist.reporter import format_text_report


def run_scenario(name, scenario, seed=42, ticks=300):
    ge = GenomeEngine()
    genome = ge.create_genome("default")
    be = BirthEngine(ge)
    brain_obj = be.create_from_genome(genome)
    
    tissue = BrainTissue(
        brain_id=brain_obj.identity.brain_id,
        genome_id=genome.id,
        plasticity=brain_obj.expressed_genes.get("plasticity", 0.5),
        homeostasis_target=brain_obj.expressed_genes.get("homeostasis_target", 0.5),
        learning_rate=brain_obj.expressed_genes.get("learning_rate", 0.1),
        decay_rate=brain_obj.expressed_genes.get("decay_rate", 0.01),
        memory_capacity=int(brain_obj.expressed_genes.get("memory_capacity", 100)),
    )
    
    kernel = Kernel(seed=seed)
    kernel.brain_id = tissue.brain_id
    kernel.max_ticks = ticks
    kernel.initialize()
    
    world = WorldRuntime()
    brain_rt = BrainRuntime()
    
    for tick in range(ticks):
        stimulus = world.step(tick=tick, seed=seed, scenario=scenario)
        tissue = brain_rt.step(brain=tissue, sensory_input=stimulus, seed=seed, tick=tick)
        kernel.snapshot_engine.create_snapshot(
            brain_id=tissue.brain_id, tick=tick, seed=seed,
            lifecycle_state="running", brain_status="ALIVE",
            entropy=tissue.entropy, energy=tissue.energy,
            age=tissue.age, step_counter=tissue.step_counter
        )
    
    kernel.stop()
    snapshots = kernel.snapshot_engine.get_all_snapshots()
    return run_experiment(name, snapshots, EventBus().get_history())


def main(seed=42, ticks=300):
    print("=" * 60)
    print("CLOS v0.1 – SCENARIO COMPARISON")
    print("=" * 60)

    # Uruchom oba scenariusze
    print("\nRunning STABLE_WORLD...")
    stable = run_scenario("stable_run", "stable_world", seed=seed, ticks=ticks)
    print("Running SHOCK_WORLD...")
    shock = run_scenario("shock_run", "shock_world", seed=seed, ticks=ticks)

    # Wyświetl raporty
    print("\n--- STABLE WORLD REPORT ---")
    print(format_text_report(stable.report))

    print("\n--- SHOCK WORLD REPORT ---")
    print(format_text_report(shock.report))

    # Porównanie
    reg = ExperimentRegistry()
    reg.register_experiment(stable.report)
    reg.register_experiment(shock.report)

    print("\n--- COMPARISON ---")
    print(reg.compare("stable_run", "shock_run"))


if __name__ == "__main__":
    main()
