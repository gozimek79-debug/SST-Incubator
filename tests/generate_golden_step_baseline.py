"""Generate golden_step_baseline.json - JEDNORAZOWY skrypt prowenancji.

SPRINT_v0.9.md, Priorytet 2, nowy inwariant: "chronimy niezmiennosc
ZACHOWANIA systemu, nie niezmiennosc plikow". Zeby test_step_regression byl
uczciwy (nie porownywal kodu sam ze soba), zlote wartosci MUSZA pochodzic z
BrainRuntime.step() SPRZED dodania partial_step() do tego samego pliku.

Uruchomiony raz, na commicie eb6d53e (v0.9 P1, "core/" usuniety,
partial_step() JESZCZE NIE ISTNIEJE, clos_brain/ niezmieniony od 6fe638d
/ v0.8.2b, working tree czyste w momencie generacji). Wyjscie:
tests/golden_step_baseline.json.

NIE URUCHAMIAJ PONOWNIE PO DODANIU partial_step() - zresetowaloby to
baseline i uniewaznilo test regresji (test porownywalby kod sam ze soba,
dokladnie to, czego ten inwariant ma unikac). Jesli kiedys trzeba
swiadomie zmienic zachowanie step() (nie powinno sie zdarzyc bez
osobnej, jawnej decyzji projektowej), ten skrypt jest tu jako
udokumentowany, odtwarzalny proces regeneracji - nie czarna skrzynka.

Wejscia sa CELOWO niezalezne od clos_world (test dotyczy BrainRuntime,
nie World Runtime) - staly seed, staly preset genomu, syntetyczna
sekwencja bodzcow generowana wzorem (nie recznie wpisana lista, zeby
uniknac literowek przy powtornej weryfikacji).
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genome.engine import GenomeEngine
from birth.engine import BirthEngine
from clos_brain.tissue import BrainTissue
from clos_brain.brain_runtime import BrainRuntime

SEED = 42
GENOME_PRESET = "default"
TICKS = 20
OUT_PATH = Path(__file__).parent / "golden_step_baseline.json"


def sensory_inputs(n: int):
    """Syntetyczna, deterministyczna sekwencja bodzcow - wzor, nie recznie
    wpisana lista. Niezalezna od clos_world.generators/scenarios celowo."""
    return [round(0.5 + 0.3 * math.sin(0.3 * t), 6) for t in range(n)]


def build_tissue(genome_preset: str) -> BrainTissue:
    ge = GenomeEngine()
    genome = ge.create_genome(genome_preset)
    be = BirthEngine(ge)
    brain_obj = be.create_from_genome(genome)
    return BrainTissue(
        brain_id=brain_obj.identity.brain_id,
        genome_id=genome.id,
        plasticity=brain_obj.expressed_genes.get("plasticity", 0.5),
        homeostasis_target=brain_obj.expressed_genes.get("homeostasis_target", 0.5),
        learning_rate=brain_obj.expressed_genes.get("learning_rate", 0.1),
        decay_rate=brain_obj.expressed_genes.get("decay_rate", 0.01),
        memory_capacity=int(brain_obj.expressed_genes.get("memory_capacity", 100)),
    )


def tissue_snapshot(brain: BrainTissue) -> dict:
    return {
        "last_prediction": brain.last_prediction,
        "last_input": brain.last_input,
        "precision": round(brain.precision, 10),
        "energy": round(brain.energy, 10),
        "entropy": round(brain.entropy, 10),
        "memory_size": len(brain.memory),
        "sensory_buffer_size": len(brain.sensory_buffer),
        "prediction_error_buffer_size": len(brain.prediction_error_buffer),
    }


def main():
    inputs = sensory_inputs(TICKS)
    brain = build_tissue(GENOME_PRESET)

    per_tick = []
    for tick, sensory_input in enumerate(inputs):
        brain = BrainRuntime.step(brain, sensory_input=sensory_input, seed=SEED, tick=tick)
        per_tick.append({"tick": tick, **tissue_snapshot(brain)})

    baseline = {
        "provenance": {
            "generated_by": "tests/generate_golden_step_baseline.py",
            "note": "Zlote wartosci step() SPRZED partial_step() (SPRINT_v0.9.md P2). "
                    "clos_brain/ niezmieniony od 6fe638d (v0.8.2b).",
        },
        "inputs": {
            "seed": SEED,
            "genome_preset": GENOME_PRESET,
            "ticks": TICKS,
            "sensory_inputs": inputs,
        },
        "per_tick": per_tick,
        "final_memory": [
            {
                "stimulus_hash": r.stimulus_hash,
                "prediction": round(r.prediction, 10),
                "error": round(r.error, 10),
                "timestamp_tick": r.timestamp_tick,
            }
            for r in brain.memory
        ],
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
