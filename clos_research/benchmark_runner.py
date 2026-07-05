"""Benchmark Runner – orkiestracja eksperymentów.

Nie analizuje. Nie liczy statystyk. Jedynie wykonuje procedurę.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from clos_research.protocol import ResearchProtocol
from clos_research.manifest import ExperimentManifest
from genome.engine import GenomeEngine
from birth.engine import BirthEngine
from clos_kernel.kernel import Kernel
from clos_world.world_runtime import WorldRuntime
from clos_brain.brain_runtime import BrainRuntime
from clos_brain.tissue import BrainTissue
from clos_scientist.experiment import run_experiment
from clos_scientist.registry import ExperimentRegistry
from clos_kernel.event_bus import EventBus


class BenchmarkRunner:
    """Wykonawca benchmarków.

    Load Protocol → Generate Matrix → Run → Scientist → Registry → Collect.
    """

    def __init__(self):
        self.genome_engine = GenomeEngine()
        self.birth_engine = BirthEngine(self.genome_engine)
        self.world_runtime = WorldRuntime()
        self.brain_runtime = BrainRuntime()
        self.registry = ExperimentRegistry()

    def run_protocol(self, protocol: ResearchProtocol) -> Dict[str, Any]:
        """Wykonaj pełny protokół badawczy.

        Args:
            protocol: Definicja eksperymentu.

        Returns:
            Słownik z wynikami benchmarku.
        """
        matrix = protocol.get_experiment_matrix()
        results = []
        run_ids = []

        for i, config in enumerate(matrix):
            run_id = f"{protocol.protocol_id}_{config['scenario']}_seed{config['seed']}"
            config["run_id"] = run_id

            # 1. Stwórz genom
            genome = self.genome_engine.create_genome(config["genome_preset"])

            # 2. Narodziny Brain
            brain_obj = self.birth_engine.create_from_genome(genome, generation=1)

            # 3. Stwórz BrainTissue z wyrażonych genów
            tissue = BrainTissue(
                brain_id=brain_obj.identity.brain_id,
                genome_id=genome.id,
                plasticity=brain_obj.cognitive_state.plasticity,
                homeostasis_target=brain_obj.cognitive_state.homeostasis,
                learning_rate=brain_obj.expressed_genes.get("learning_rate", 0.1),
                decay_rate=brain_obj.expressed_genes.get("decay_rate", 0.01),
                memory_capacity=int(brain_obj.expressed_genes.get("memory_capacity", 100)),
                prediction_depth=int(brain_obj.expressed_genes.get("prediction_depth", 3)),
                attention_threshold=brain_obj.expressed_genes.get("attention_threshold", 0.3),
                meta_cognition_sensitivity=brain_obj.expressed_genes.get("meta_cognition_sensitivity", 0.5),
            )

            # 4. Uruchom Kernel + World + Brain
            kernel = Kernel(seed=config["seed"])
            kernel.brain_id = tissue.brain_id
            kernel.max_ticks = config["tick_count"]
            kernel.initialize()

            for tick in range(config["tick_count"]):
                # World → bodziec
                stimulus = self.world_runtime.step(
                    tick=tick,
                    seed=config["seed"],
                    scenario=config["scenario"]
                )

                # Brain → transformacja
                tissue = self.brain_runtime.step(
                    brain=tissue,
                    sensory_input=stimulus,
                    seed=config["seed"],
                    tick=tick
                )

                # Kernel → snapshot
                kernel.snapshot_engine.create_snapshot(
                    brain_id=tissue.brain_id,
                    tick=tick,
                    seed=config["seed"],
                    lifecycle_state=kernel.lifecycle.state.value,
                    brain_status="ALIVE",
                    entropy=tissue.entropy,
                    energy=tissue.energy,
                    age=tissue.age,
                    step_counter=tissue.step_counter
                )

            kernel.stop()

            # 5. Scientist → raport
            snapshots = kernel.snapshot_engine.get_all_snapshots()
            bus = EventBus()
            result = run_experiment(run_id, snapshots, bus.get_history())
            self.registry.register_experiment(result.report)

            results.append({
                "run_id": run_id,
                "report": result.report.to_dict(),
                "seed": config["seed"],
                "scenario": config["scenario"],
                "genome_preset": config["genome_preset"],
            })
            run_ids.append(run_id)

        return {
            "protocol_id": protocol.protocol_id,
            "runs": results,
            "run_ids": run_ids,
            "total_runs": len(results),
            "manifest": self._build_manifest(protocol, len(results)),
        }

    def _build_manifest(self, protocol: ResearchProtocol, total_runs: int) -> Dict[str, Any]:
        """Buduje manifest eksperymentu."""
        manifest = ExperimentManifest(
            protocol_id=protocol.protocol_id,
            dataset_name=protocol.dataset_name,
            dataset_version=protocol.version,
            seed_count=len(protocol.seed_list),
            scenario_count=1,
            genome_count=1,
        )
        return manifest.to_dict()

    def get_registry(self) -> ExperimentRegistry:
        """Zwraca rejestr eksperymentów."""
        return self.registry
