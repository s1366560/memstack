from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.domain.model.memory.episode import Episode
from src.domain.model.memory.entity import Entity
from src.domain.model.memory.community import Community

class GraphServicePort(ABC):
    @abstractmethod
    async def add_episode(self, episode: Episode) -> Episode:
        pass

    @abstractmethod
    async def search(self, query: str, project_id: Optional[str] = None, limit: int = 10) -> List[Any]:
        # Returns list of MemoryItems (defined in DTOs usually, or domain items)
        pass

    @abstractmethod
    async def get_graph_data(self, project_id: str, limit: int = 100) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def delete_episode(self, episode_name: str) -> bool:
        pass

    @abstractmethod
    async def delete_episode_by_memory_id(self, memory_id: str) -> bool:
        pass
