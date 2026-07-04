from pydantic import BaseModel, ConfigDict
from typing import Dict, Any
from .gene import Gene

class Genome(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    name: str
    version: str = "0.1"
    description: str = ""
    genes: Dict[str, Gene] = {}

    def add_gene(self, gene: Gene):
        self.genes[gene.id] = gene

    def get_gene(self, gene_id: str) -> Gene:
        if gene_id not in self.genes:
            raise KeyError(f"Gene {gene_id} not found in genome")
        return self.genes[gene_id]

    def express_all(self) -> Dict[str, Any]:
        return {gene_id: gene.express() for gene_id, gene in self.genes.items()}

    def mutate_all(self) -> Dict[str, bool]:
        return {gene_id: gene.mutate() for gene_id, gene in self.genes.items()}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "genes": {gid: gene.model_dump() for gid, gene in self.genes.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Genome":
        genes = {gid: Gene(**gdata) for gid, gdata in data.get("genes", {}).items()}
        return cls(
            id=data["id"],
            name=data["name"],
            version=data.get("version", "0.1"),
            description=data.get("description", ""),
            genes=genes
        )
