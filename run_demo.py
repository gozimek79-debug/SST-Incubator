"""Demo CLOS v0.6 – z parametrami genome i scenario, zapis JSON."""

import json, sys, os, logging
from genome.engine import GenomeEngine
from birth.engine import BirthEngine
from clos_kernel.kernel import Kernel
from clos_world.world_runtime import WorldRuntime
from clos_brain.brain_runtime import BrainRuntime
from clos_brain.tissue import BrainTissue
from clos_scientist.experiment import run_experiment
from clos_kernel.event_bus import EventBus


def main(seed=42, ticks=200, stream=False, genome_preset="default", scenario="shock_world"):
    if stream:
        logging.getLogger().setLevel(logging.ERROR)

    ge = GenomeEngine()
    genome = ge.create_genome(genome_preset)
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
        prediction_depth=int(brain_obj.expressed_genes.get("prediction_depth", 3)),
        attention_threshold=brain_obj.expressed_genes.get("attention_threshold", 0.3),
        meta_cognition_sensitivity=brain_obj.expressed_genes.get("meta_cognition_sensitivity", 0.5),
    )

    if not stream:
        print(f"[{genome_preset}] {scenario} seed={seed} ticks={ticks}")

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
        if stream:
            print(json.dumps({
                "event": "TICK", "run_id": "demo", "tick": tick,
                "telemetry": {"entropy": round(tissue.entropy,6), "energy": round(tissue.energy,6)}
            }), flush=True)

    kernel.stop()

    # Scientist → zapis JSON bezpośrednio (ZADANIE 2: likwidacja parsera STDOUT)
    snapshots = kernel.snapshot_engine.get_all_snapshots()
    result = run_experiment("demo", snapshots, EventBus().get_history())

    # Wyciągnij adaptation_tick z analyzer bezpośrednio
    from clos_scientist.analyzer import detect_phases, compute_adaptation_speed
    phases = detect_phases(snapshots)
    adaptation_tick = phases.get("adaptation", compute_adaptation_speed(snapshots))
    convergence_tick = phases.get("convergence", 0)
    chaos_end = phases.get("initial_chaos", 0)

    output = {
        "run_id": f"{genome_preset}_{scenario}_s{seed}",
        "genome": genome_preset,
        "scenario": scenario,
        "seed": seed,
        "ticks": ticks,
        "stability_score": round(result.report.stability_score, 4),
        "mse": round(result.report.mse, 6),
        "entropy_volatility": round(result.report.metrics.get("entropy_volatility", 0), 6),
        "energy_drift": round(result.report.metrics.get("energy_drift", 0), 6),
        "adaptation_tick": adaptation_tick,
        "convergence_tick": convergence_tick,
        "chaos_end": chaos_end,
        "memory_size": len(tissue.memory),
        "final_entropy": round(tissue.entropy, 6),
        "final_energy": round(tissue.energy, 6),
    }

    # Zapisz do pliku JSON
    output_dir = "reports/runs"
    os.makedirs(output_dir, exist_ok=True)
    json_path = f"{output_dir}/{genome_preset}_{scenario}_s{seed}_t{ticks}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    if not stream:
        print(json.dumps(output))
    return output


if __name__ == "__main__":
    main()
