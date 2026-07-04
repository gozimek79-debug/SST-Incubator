from pydantic import BaseModel
from pathlib import Path
import yaml

class CLOSConfig(BaseModel):
    version: str = "0.1"
    database_url: str = "sqlite:///storage/clos.db"
    experiments_dir: Path = Path("experiments")
    max_cycles: int = 10000
    save_interval: int = 100

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_yaml(cls, path: str = "config.yaml"):
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str = "config.yaml"):
        with open(path, 'w') as f:
            yaml.dump(self.dict(), f, default_flow_style=False)
