import json
from pathlib import Path
from typing import Dict, Any, Optional
from .genome import Genome
from .presets import create_default_genome

class GenomeEngine:
    def __init__(self, storage_path: str = "storage/genomes"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.genomes: Dict[str, Genome] = {}

    def create_genome(self, preset: str = "default") -> Genome:
        if preset == "default":
            genome = create_default_genome()
        elif preset == "minimal":
            from .presets import create_minimal_genome
            genome = create_minimal_genome()
        elif preset == "highly_plastic":
            from .presets import create_highly_plastic_genome
            genome = create_highly_plastic_genome()
        else:
            raise ValueError(f"Unknown preset: {preset}")
        
        self.genomes[genome.id] = genome
        return genome

    def save_genome(self, genome: Genome):
        path = self.storage_path / f"{genome.id}.json"
        data = genome.to_dict()
        # Konwersja Enum na string dla JSON
        for gid, gene in data["genes"].items():
            if "dominance" in gene and hasattr(gene["dominance"], "value"):
                gene["dominance"] = gene["dominance"].value
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def load_genome(self, genome_id: str) -> Optional[Genome]:
        path = self.storage_path / f"{genome_id}.json"
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        genome = Genome.from_dict(data)
        self.genomes[genome.id] = genome
        return genome

    def list_genomes(self) -> list:
        return [
            p.stem for p in self.storage_path.glob("*.json")
        ]

    def mutate_genome(self, genome_id: str) -> Dict[str, bool]:
        if genome_id not in self.genomes:
            raise KeyError(f"Genome {genome_id} not loaded")
        return self.genomes[genome_id].mutate_all()

    def express_genome(self, genome_id: str) -> Dict[str, Any]:
        if genome_id not in self.genomes:
            raise KeyError(f"Genome {genome_id} not loaded")
        return self.genomes[genome_id].express_all()
