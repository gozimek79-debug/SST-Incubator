"""Demo CLOS v0.1 – pojedynczy eksperyment."""

import json
import sys
import logging
from genome.engine import GenomeEngine
from birth.engine import BirthEngine
from clos_kernel.kernel import Kernel
from clos_world.world_runtime import WorldRuntime
from clos_brain.brain_runtime import BrainRuntime
from clos_brain.tissue import BrainTissue
from clos_scientist.experiment import run_experiment
from clos_scientist.reporter import format_text_report
from clos_kernel.event_bus import EventBus


def main(seed=42, ticks=200, stream=False):
    if stream:
        # Wycisz logi – tylko JSONL na stdout
        logging.getLogger().setLevel(logging.ERROR)

    if not stream:
        print("=" * 60)
        print("CLOS v0.1 – DEMO EXPERIMENT")
        print("=" * 60)
        print(f"\n[1] Creating genome...")

    ge = GenomeEngine()
    genome = ge.create_genome("default")

    if not stream:
        print(f"    Genome: {genome.name} ({len(genome.genes)} genes)")
        print(f"\n[2] Birth of Brain...")

    be = BirthEngine(ge)
    brain_obj = be.create_from_genome(genome)

    if not stream:
        print(f"    Brain ID: {brain_obj.identity.brain_id}")

    tissue = BrainTissue(
        brain_id=brain_obj.identity.brain_id,
        genome_id=genome.id,
        plasticity=brain_obj.expressed_genes.get("plasticity", 0.5),
        homeostasis_target=brain_obj.expressed_genes.get("homeostasis_target", 0.5),
        learning_rate=brain_obj.expressed_genes.get("learning_rate", 0.1),
        decay_rate=brain_obj.expressed_genes.get("decay_rate", 0.01),
        memory_capacity=int(brain_obj.expressed_genes.get("memory_capacity", 100)),
    )

    if not stream:
        print(f"\n[3] Running simulation ({ticks} ticks, SHOCK_WORLD)...")

    kernel = Kernel(seed=seed)
    kernel.brain_id = tissue.brain_id
    kernel.max_ticks = ticks
    kernel.initialize()

    world = WorldRuntime()
    brain_rt = BrainRuntime()

    for tick in range(ticks):
        stimulus = world.step(tick=tick, seed=seed, scenario="shock_world")
        tissue = brain_rt.step(brain=tissue, sensory_input=stimulus, seed=seed, tick=tick)
        kernel.snapshot_engine.create_snapshot(
            brain_id=tissue.brain_id, tick=tick, seed=seed,
            lifecycle_state="running", brain_status="ALIVE",
            entropy=tissue.entropy, energy=tissue.energy,
            age=tissue.age, step_counter=tissue.step_counter
        )

        if stream:
            tick_data = {
                "event": "TICK",
                "run_id": "demo_shock",
                "tick": tick,
                "timestamp": int(tissue.age),
                "telemetry": {
                    "entropy": round(tissue.entropy, 6),
                    "energy": round(tissue.energy, 6),
                    "precision": round(tissue.precision, 6),
                    "memory_size": len(tissue.memory),
                },
                "phase": "running",
                "anomaly": False,
            }
            print(json.dumps(tick_data), flush=True)

    kernel.stop()

    if not stream:
        snapshots = kernel.snapshot_engine.get_all_snapshots()
        result = run_experiment("demo_shock", snapshots, EventBus().get_history())
        print("\n[4] Generating Scientist report...")
        print("\n" + format_text_report(result.report))
        print("\n[5] Final Brain state:")
        print(tissue.summary())
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    main()
