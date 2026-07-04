from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any

class CLOSModule(ABC):
    def __init__(self, module_id: str):
        self.module_id = module_id
        self.created_at = datetime.now()
        self.state: Dict[str, Any] = {}
        self.cycle_count: int = 0

    @abstractmethod
    async def initialize(self):
        pass

    @abstractmethod
    async def step(self):
        pass

    @abstractmethod
    def save_state(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def load_state(self, state: Dict[str, Any]):
        pass

class Event:
    def __init__(self, event_type: str, data: Dict[str, Any], source: str):
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now()
