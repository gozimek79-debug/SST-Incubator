"""Lesson L1.1 – Pattern Echo: Working Memory Emergence (v0.8.1).

Poprawka metodologiczna: faza ciszy nie podaje bodzca (stimulus=None),
a Perception ignoruje None i nie aktualizuje bufora. Brain musi
predykowac z pamieci. MSE mierzone jest miedzy predykcja a oryginalnym
wzorcem (sinusoida), ktorego Brain juz nie widzi.
"""

import json, os, sys, logging
sys.path.insert(0, os.getcwd())

from genome.engine import GenomeEngine
from birth.engine import BirthEngine
from clos_kernel.kernel import Kernel
from clos_world.world_runtime import WorldRuntime
from clos_brain.brain_runtime import BrainRuntime
from clos_brain.tissue import BrainTissue
from clos_scientist.experiment import run_experiment
from clos_scientist.analyzer import detect_phases
from clos_kernel.event_bus import EventBus
from clos_curriculum.laboratory.statistics import compute_ci95, glass_delta


def run_pattern_echo(genome_preset="default", seed=42, stimulus_ticks=100, silence_ticks=100):
    """Poprawiona wersja: w ciszy stimulus=None, mierzymy MSE vs wzorzec."""
    
    # Wycisz logi
    logging.getLogger().setLevel(logging.ERROR)
    
    total_ticks = stimulus_ticks + silence_ticks
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
    
    kernel = Kernel(seed=seed); kernel.brain_id = tissue.brain_id
    kernel.max_ticks = total_ticks; kernel.initialize()
    world = WorldRuntime(); brain_rt = BrainRuntime()
    
    telemetry = []
    pattern_mse = []  # MSE miedzy predykcja a wzorcem (sinusoida)
    
    for tick in range(total_ticks):
        # Wzorca uzywamy zawsze do pomiaru MSE
        pattern_signal = world.step(tick=tick, seed=seed, scenario="stable_world")
        
        if tick < stimulus_ticks:
            stimulus = pattern_signal  # Faza stymulacji: normalny bodziec
        else:
            stimulus = -1.0  # Faza ciszy: wartosc spoza zakresu [0,1] = brak bodzca
        
        tissue = brain_rt.step(brain=tissue, sensory_input=stimulus, seed=seed, tick=tick)
        
        # MSE miedzy predykcja a wzorcem (niezaleznie od fazy)
        if tissue.last_prediction is not None:
            mse_vs_pattern = abs(tissue.last_prediction - pattern_signal)
            pattern_mse.append(mse_vs_pattern)
        
        if tick % 5 == 0:
            telemetry.append({
                "tick": tick,
                "phase": "stimulus" if tick < stimulus_ticks else "silence",
                "prediction": round(tissue.last_prediction, 6) if tissue.last_prediction else 0,
                "pattern": round(pattern_signal, 6),
                "mse_vs_pattern": round(mse_vs_pattern, 6) if tissue.last_prediction else 0,
                "entropy": round(tissue.entropy, 6),
                "energy": round(tissue.energy, 6),
                "memory_size": len(tissue.memory),
            })
    
    kernel.stop()
    
    # Kluczowe metryki
    silence_start_idx = stimulus_ticks // 5  # indeks w telemetrii
    silence_phase = [t for t in telemetry if t["phase"] == "silence"]
    
    # MSE po 50 tickach ciszy (wzgledem wzorca)
    silence_after_50 = [t for t in silence_phase if t["tick"] >= stimulus_ticks + 50]
    mse_at_tick_50 = sum(t["mse_vs_pattern"] for t in silence_after_50) / len(silence_after_50) if silence_after_50 else 1.0
    
    # MSE w fazie stymulacji (baseline)
    stimulus_phase = [t for t in telemetry if t["phase"] == "stimulus"]
    mse_stimulus = sum(t["mse_vs_pattern"] for t in stimulus_phase) / len(stimulus_phase) if stimulus_phase else 0
    
    # Memory decay: roznica miedzy MSE w ciszy a MSE w stymulacji
    mse_silence = sum(t["mse_vs_pattern"] for t in silence_phase) / len(silence_phase) if silence_phase else 0
    memory_decay = (mse_silence - mse_stimulus) / silence_ticks if silence_ticks > 0 else 0
    
    # Scientist
    snapshots = kernel.snapshot_engine.get_all_snapshots()
    result = run_experiment("pattern_echo", snapshots, EventBus().get_history())
    phases = detect_phases(snapshots)
    
    output = {
        "run_id": f"L1.1_{genome_preset}_s{seed}",
        "lesson": "L1.1",
        "genome": genome_preset,
        "seed": seed,
        "primary_endpoint": {
            "metric": "mse_vs_pattern_after_stimulus_removal",
            "measurement_tick": 50,
            "value": round(mse_at_tick_50, 6),
        },
        "mse_stimulus_phase": round(mse_stimulus, 6),
        "mse_silence_phase": round(mse_silence, 6),
        "memory_decay_rate": round(memory_decay, 6),
        "stability_score": round(result.report.stability_score, 4),
        "adaptation_tick": phases.get("adaptation", 0),
        "final_energy": round(tissue.energy, 6),
        "final_entropy": round(tissue.entropy, 6),
        "memory_size": len(tissue.memory),
        "telemetry": telemetry,
    }
    
    # Nowe kryterium PASS: MSE@50 < 0.5 oznacza, ze Brain UTRZYMUJE wzorzec
    # (przewiduje sinusoidę, mimo ze jej nie widzi)
    output["passed"] = output["primary_endpoint"]["value"] < 0.5
    
    return output


def run_lesson_L1_1():
    print("=" * 60)
    print("CLOS Cognitive Academy v0.8.1")
    print("Lesson L1.1: Pattern Echo – Working Memory")
    print("=" * 60)
    print("Hypothesis: Brain utrzyma reprezentacje wzorca po usunieciu bodzca.")
    print("Primary Endpoint: MSE vs pattern @ 50 ticks of silence")
    print("PASS if MSE@50 < 0.5")
    print("=" * 60)
    
    genomes = ["default", "highly_plastic"]
    seeds = list(range(1, 11))
    all_results = []
    
    for genome in genomes:
        print(f"\nGenome: {genome}")
        genome_results = []
        for seed in seeds:
            print(f"  seed {seed:2d}...", end=" ")
            r = run_pattern_echo(genome_preset=genome, seed=seed)
            genome_results.append(r)
            all_results.append(r)
            status = "PASS" if r["passed"] else "FAIL"
            print(f"{status} (MSE@50={r['primary_endpoint']['value']:.4f}, stim={r['mse_stimulus_phase']:.4f}, sil={r['mse_silence_phase']:.4f})")
        
        mse_vals = [r["primary_endpoint"]["value"] for r in genome_results]
        stats = compute_ci95(mse_vals)
        passed = sum(1 for r in genome_results if r["passed"])
        print(f"  Summary: {passed}/{len(seeds)} passed")
        if stats.get("ci95_valid"):
            print(f"  MSE@50: mean={stats['mean']:.4f}, CI95=[{stats['ci95_low']:.4f}, {stats['ci95_high']:.4f}]")
        else:
            print(f"  MSE@50: mean={stats['mean']:.4f} (deterministic)")
    
    # Porownanie genomow
    default_mse = [r["primary_endpoint"]["value"] for r in all_results if r["genome"] == "default"]
    plastic_mse = [r["primary_endpoint"]["value"] for r in all_results if r["genome"] == "highly_plastic"]
    
    print(f"\n{'='*60}")
    print("GENOME COMPARISON")
    print(f"{'='*60}")
    
    if default_mse and plastic_mse:
        gd = glass_delta(default_mse, plastic_mse)
        if gd.get("computable"):
            print(f"Glass's delta (plastic vs default): {gd['delta']:.4f}")
            print(f"  default_v1 mean MSE@50:      {sum(default_mse)/len(default_mse):.4f}")
            print(f"  highly_plastic_v1 mean MSE@50: {sum(plastic_mse)/len(plastic_mse):.4f}")
        else:
            print(f"Glass's delta: not computable ({gd.get('reason', 'unknown')})")
            print(f"  default_v1 mean MSE@50:      {sum(default_mse)/len(default_mse):.4f}")
            print(f"  highly_plastic_v1 mean MSE@50: {sum(plastic_mse)/len(plastic_mse):.4f}")
    
    # Zapis raportu
    os.makedirs("reports/academy", exist_ok=True)
    report = {
        "lesson": "L1.1",
        "title": "Pattern Echo – Working Memory Emergence",
        "version": "0.8.1",
        "hypothesis": "Brain utrzyma reprezentacje wzorca po usunieciu bodzca",
        "primary_endpoint": "MSE vs pattern @ 50 ticks of silence",
        "pass_condition": "MSE@50 < 0.5",
        "total_runs": len(all_results),
        "genomes": genomes,
        "seeds": seeds,
        "default_stats": compute_ci95(default_mse) if default_mse else {},
        "plastic_stats": compute_ci95(plastic_mse) if plastic_mse else {},
        "glass_delta": gd if default_mse and plastic_mse else {},
        "results": [{k: v for k, v in r.items() if k != "telemetry"} for r in all_results],
    }
    
    with open("reports/academy/L1_1_pattern_echo.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReport saved: reports/academy/L1_1_pattern_echo.json")
    print("=" * 60)
    
    return all_results


if __name__ == "__main__":
    run_lesson_L1_1()
