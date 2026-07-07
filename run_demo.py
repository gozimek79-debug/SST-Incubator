"""Demo CLOS v0.7.3 – z opcjonalnym zapisem snapshotow co N tickow."""

import json, sys, os, logging
from genome.engine import GenomeEngine
from birth.engine import BirthEngine
from clos_kernel.kernel import Kernel
from clos_world.world_runtime import WorldRuntime
from clos_brain.brain_runtime import BrainRuntime
from clos_brain.tissue import BrainTissue
from clos_scientist.experiment import run_experiment
from clos_scientist.analyzer import detect_phases
from clos_kernel.event_bus import EventBus


def main(seed=42, ticks=200, stream=False, genome_preset="default", scenario="shock_world", telemetry_interval=0):
    if stream: logging.getLogger().setLevel(logging.ERROR)

    ge = GenomeEngine(); genome = ge.create_genome(genome_preset)
    be = BirthEngine(ge); brain_obj = be.create_from_genome(genome)

    tissue = BrainTissue(
        brain_id=brain_obj.identity.brain_id, genome_id=genome.id,
        plasticity=brain_obj.expressed_genes.get("plasticity",0.5),
        homeostasis_target=brain_obj.expressed_genes.get("homeostasis_target",0.5),
        learning_rate=brain_obj.expressed_genes.get("learning_rate",0.1),
        decay_rate=brain_obj.expressed_genes.get("decay_rate",0.01),
        memory_capacity=int(brain_obj.expressed_genes.get("memory_capacity",100)),
    )

    kernel = Kernel(seed=seed); kernel.brain_id = tissue.brain_id; kernel.max_ticks = ticks
    kernel.initialize()
    world = WorldRuntime(); brain_rt = BrainRuntime()

    telemetry_snapshots = []

    for tick in range(ticks):
        stimulus = world.step(tick=tick, seed=seed, scenario=scenario)
        tissue = brain_rt.step(brain=tissue, sensory_input=stimulus, seed=seed, tick=tick)

        if telemetry_interval > 0 and tick % telemetry_interval == 0:
            telemetry_snapshots.append({
                "tick": tick, "entropy": round(tissue.entropy,6),
                "energy": round(tissue.energy,6), "precision": round(tissue.precision,6),
                "memory_size": len(tissue.memory),
            })

        if stream:
            print(json.dumps({"event":"TICK","tick":tick,"telemetry":{"entropy":round(tissue.entropy,6)}}), flush=True)

    kernel.stop()
    snapshots = kernel.snapshot_engine.get_all_snapshots()
    result = run_experiment("demo", snapshots, EventBus().get_history())
    phases = detect_phases(snapshots)

    output = {
        "run_id": f"{genome_preset}_{scenario}_s{seed}",
        "genome": genome_preset, "scenario": scenario, "seed": seed, "ticks": ticks,
        "stability_score": round(result.report.stability_score,4),
        "mse": round(result.report.mse,6),
        "entropy_volatility": round(result.report.metrics.get("entropy_volatility",0),6),
        "energy_drift": round(result.report.metrics.get("energy_drift",0),6),
        "adaptation_tick": phases.get("adaptation",0),
        "convergence_tick": phases.get("convergence",0),
        "memory_size": len(tissue.memory),
        "final_entropy": round(tissue.entropy,6),
        "final_energy": round(tissue.energy,6),
        "telemetry_snapshots": telemetry_snapshots if telemetry_interval > 0 else [],
    }

    os.makedirs("reports/runs", exist_ok=True)
    with open(f"reports/runs/{genome_preset}_{scenario}_s{seed}_t{ticks}.json","w",encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    if not stream:
        print(json.dumps({k:v for k,v in output.items() if k!="telemetry_snapshots"}))
    return output

if __name__ == "__main__":
    main()
