"""Matrix Manifest – rozszerzony manifest dla macierzy eksperymentów."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class MatrixManifest:
    """Manifest macierzy badawczej."""

    schema_version: int = 1
    experiment: Dict[str, Any] = field(default_factory=dict)
    matrix: Dict[str, Any] = field(default_factory=dict)
    ticks: int = 500
    workflow_version: str = "0.4"
    parent_experiment: Optional[str] = None
    seed_policy: str = "fixed"
    publish_on_verify: bool = True

    @property
    def experiment_id(self) -> str:
        return self.experiment.get("id", "")

    @property
    def description(self) -> str:
        return self.experiment.get("description", "")

    @property
    def genomes(self) -> List[str]:
        return self.matrix.get("genomes", [])

    @property
    def scenarios(self) -> List[str]:
        return self.matrix.get("scenarios", [])

    @property
    def seeds(self) -> List[int]:
        return self.matrix.get("seeds", [])

    def get_run_matrix(self) -> List[Dict[str, Any]]:
        runs = []
        for genome in self.genomes:
            for scenario in self.scenarios:
                for seed in self.seeds:
                    runs.append({
                        "genome": genome,
                        "scenario": scenario,
                        "seed": seed,
                        "ticks": self.ticks,
                        "workflow_version": self.workflow_version,
                        "parent_experiment": self.parent_experiment,
                    })
        return runs

    def get_total_runs(self) -> int:
        return len(self.genomes) * len(self.scenarios) * len(self.seeds)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "experiment": self.experiment,
            "matrix": self.matrix,
            "ticks": self.ticks,
            "workflow_version": self.workflow_version,
            "parent_experiment": self.parent_experiment,
            "seed_policy": self.seed_policy,
            "publish_on_verify": self.publish_on_verify,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatrixManifest":
        return cls(
            schema_version=data.get("schema_version", 1),
            experiment=data.get("experiment", {}),
            matrix=data.get("matrix", {}),
            ticks=data.get("ticks", 500),
            workflow_version=data.get("workflow_version", "0.4"),
            parent_experiment=data.get("parent_experiment"),
            seed_policy=data.get("seed_policy", "fixed"),
            publish_on_verify=data.get("publish_on_verify", True),
        )

    @classmethod
    def from_yaml(cls, path: str) -> "MatrixManifest":
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    def summary(self) -> str:
        lines = [
            f"Matrix: {self.experiment_id}",
            f"  Genomes:   {self.genomes}",
            f"  Scenarios: {self.scenarios}",
            f"  Seeds:     {len(self.seeds)} seeds",
            f"  Ticks:     {self.ticks}",
            f"  Total runs: {self.get_total_runs()}",
            f"  Workflow:  v{self.workflow_version}",
        ]
        return "\n".join(lines)
