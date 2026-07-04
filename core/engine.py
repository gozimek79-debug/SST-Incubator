import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from .storage import CLOSStorage
from .config import CLOSConfig

class CLOSEngine:
    def __init__(self, config: CLOSConfig):
        self.config = config
        self.modules: Dict[str, Any] = {}
        self.storage = CLOSStorage(config.database_url)
        self.running = False
        self.cycles = 0
        self.current_experiment_id: Optional[str] = None

    async def register_module(self, module_id: str, module):
        self.modules[module_id] = module
        await module.initialize()

    async def run_experiment(self, name: str, experiment_config: Dict[str, Any]) -> str:
        await self.storage.connect()
        self.running = True
        self.cycles = 0
        
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_experiment_id = experiment_id
        
        cursor = self.storage.conn.cursor()
        cursor.execute(
            "INSERT INTO experiments (id, name, config, status) VALUES (?, ?, ?, ?)",
            (experiment_id, name, str(experiment_config), "running")
        )
        self.storage.conn.commit()

        while self.running and self.cycles < self.config.max_cycles:
            for module_id, module in self.modules.items():
                await module.step()
            
            if self.cycles % self.config.save_interval == 0:
                await self._save_cycle()
            
            self.cycles += 1

        cursor.execute(
            "UPDATE experiments SET status = ? WHERE id = ?",
            ("completed", experiment_id)
        )
        self.storage.conn.commit()
        
        return experiment_id

    async def _save_cycle(self):
        state = {
            "cycle_number": self.cycles,
            "brain_state": self.modules.get("brain", None).save_state() if "brain" in self.modules else {},
            "world_state": self.modules.get("world", None).save_state() if "world" in self.modules else {},
            "metrics": {}
        }
        await self.storage.save_cycle(self.current_experiment_id, state)

    async def stop(self):
        self.running = False
        self.storage.close()
